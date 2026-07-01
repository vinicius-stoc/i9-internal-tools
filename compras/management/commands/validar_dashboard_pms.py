from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Max, Sum

from compras.models import (
    PmsCustoTarefa,
    PmsCustoTemporalMensal,
    PmsEdt,
    PmsProjeto,
    PmsTarefa,
)
from compras.selectors.pms_dashboard import PmsDashboardSelector
from compras.services.pms_etl_service import ComprasPmsETLService
from compras.services.pms_hierarchy import (
    ZERO,
    calcular_indicadores_empenho,
    consolidar_custos_por_edt,
    montar_caminhos_edt,
)


CEM = Decimal("100")
MONEY_FIELDS = (
    "custo_previsto",
    "custo_realizado",
    "custo_empenhado",
    "saldo_previsto_realizado",
)
STATUS_ORDER = {"OK": 0, "ALERTA": 1, "ERRO": 2}


@dataclass
class Finding:
    status: str
    section: str
    message: str
    context: str = ""


class Command(BaseCommand):
    help = (
        "Valida por amostragem a coerencia dos dados do Dashboard Financeiro PMS "
        "de Compras sem alterar dados."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--sample-size",
            type=int,
            default=5,
            help="Quantidade maxima de projetos amostrados. Padrao: 5.",
        )
        parser.add_argument(
            "--projeto",
            action="append",
            default=[],
            help=(
                "Codigo de projeto para validar. Pode ser repetido ou receber "
                "valores separados por virgula."
            ),
        )
        parser.add_argument(
            "--all-projects",
            action="store_true",
            help="Valida todos os projetos com custo materializado.",
        )
        parser.add_argument(
            "--tolerance",
            default="0.01",
            help="Tolerancia para divergencias monetarias. Padrao: 0.01.",
        )
        parser.add_argument(
            "--raw-sdb-dir",
            default="compras/data",
            help=(
                "Diretorio local para validacao opcional contra SDB bruto. "
                "Padrao: compras/data."
            ),
        )

    def handle(self, *args, **options):
        self.findings = []
        self.ok_items = []
        self.sample_size = max(options["sample_size"], 1)
        self.tolerance = self._decimal(options["tolerance"])
        self.raw_sdb_dir = Path(options["raw_sdb_dir"])

        projetos_solicitados = self._parse_projetos(options["projeto"])
        projetos_amostrados = self._selecionar_projetos(
            projetos_solicitados=projetos_solicitados,
            all_projects=options["all_projects"],
        )

        self._write_header("Validacao Dashboard PMS de Compras")
        self.stdout.write(f"Tolerancia monetaria: {self.tolerance}")
        self.stdout.write(f"Amostra solicitada: {self.sample_size}")
        self.stdout.write("")

        if not projetos_amostrados:
            self._add("ALERTA", "Amostra", "Nenhum projeto com custo foi encontrado.")
            self._print_report([])
            return

        self._validar_integridade_referencial()
        self._validar_revisoes()
        self._validar_filtros(projetos_amostrados)
        self._validar_projetos(projetos_amostrados)
        self._validar_carteira(projetos_amostrados)
        self._validar_temporal(projetos_amostrados)
        self._validar_sdb_bruto(projetos_amostrados)

        status = self._print_report(projetos_amostrados)
        if status == "ERRO":
            raise CommandError("Status final: ERRO")

    def _selecionar_projetos(self, projetos_solicitados, all_projects):
        projetos_existentes = set(
            PmsCustoTarefa.objects.values_list("projeto", flat=True).distinct()
        )
        if projetos_solicitados:
            encontrados = [
                projeto for projeto in projetos_solicitados if projeto in projetos_existentes
            ]
            ausentes = sorted(set(projetos_solicitados) - projetos_existentes)
            for projeto in ausentes:
                self._add(
                    "ALERTA",
                    "Amostra",
                    "Projeto informado sem custo materializado.",
                    projeto,
                )
            return encontrados

        base = list(
            PmsCustoTarefa.objects.values("projeto")
            .annotate(total=Sum("custo_realizado"))
            .order_by("-total", "projeto")
        )
        if all_projects:
            return [item["projeto"] for item in base]

        escolhidos = []
        vistos = set()

        def add(projeto):
            if projeto and projeto not in vistos and projeto in projetos_existentes:
                vistos.add(projeto)
                escolhidos.append(projeto)

        for item in base[: self.sample_size]:
            add(item["projeto"])

        sem_empenho = (
            PmsCustoTarefa.objects.filter(custo_realizado__gt=0, custo_empenhado=0)
            .values("projeto")
            .annotate(total=Sum("custo_realizado"))
            .order_by("-total")
            .first()
        )
        if sem_empenho:
            add(sem_empenho["projeto"])

        multi_revisao = (
            PmsCustoTarefa.objects.values("projeto")
            .annotate(revisoes=Count("revisao", distinct=True))
            .filter(revisoes__gt=1)
            .order_by("projeto")
            .first()
        )
        if multi_revisao:
            add(multi_revisao["projeto"])

        temporal = (
            PmsCustoTemporalMensal.objects.values("projeto")
            .annotate(total=Sum("custo_realizado"))
            .order_by("-total")
            .first()
        )
        if temporal:
            add(temporal["projeto"])

        return escolhidos[: self.sample_size]

    def _validar_integridade_referencial(self):
        projetos = set(
            PmsProjeto.objects.values_list("filial", "projeto", "revisao")
        )
        edts = set(
            PmsEdt.objects.values_list("filial", "projeto", "revisao", "edt")
        )
        tarefas = set(
            PmsTarefa.objects.values_list("filial", "projeto", "revisao", "tarefa")
        )
        custos = list(
            PmsCustoTarefa.objects.values(
                "filial", "projeto", "revisao", "edt", "tarefa"
            )
        )

        custos_sem_projeto = []
        custos_sem_tarefa = []
        custos_sem_edt = []
        for custo in custos:
            projeto_key = (custo["filial"], custo["projeto"], custo["revisao"])
            tarefa_key = (
                custo["filial"],
                custo["projeto"],
                custo["revisao"],
                custo["tarefa"],
            )
            edt_key = (
                custo["filial"],
                custo["projeto"],
                custo["revisao"],
                custo["edt"],
            )
            if projeto_key not in projetos:
                custos_sem_projeto.append(custo)
            if tarefa_key not in tarefas:
                custos_sem_tarefa.append(custo)
            if custo["edt"] and edt_key not in edts:
                custos_sem_edt.append(custo)

        self._record_count(
            "Integridade referencial",
            "Custos sem projeto PMS correspondente",
            custos_sem_projeto,
            "ERRO",
            self._format_cost_key,
        )
        self._record_count(
            "Integridade referencial",
            "Custos sem tarefa PMS correspondente",
            custos_sem_tarefa,
            "ERRO",
            self._format_cost_key,
        )
        self._record_count(
            "Integridade referencial",
            "Custos com EDT inexistente",
            custos_sem_edt,
            "ERRO",
            self._format_cost_key,
        )

        tarefas_rows = list(
            PmsTarefa.objects.values("filial", "projeto", "revisao", "edt", "tarefa")
        )
        tarefas_sem_edt = [
            item
            for item in tarefas_rows
            if not item["edt"]
            or (item["filial"], item["projeto"], item["revisao"], item["edt"])
            not in edts
        ]
        self._record_count(
            "Integridade referencial",
            "Tarefas sem EDT valida",
            tarefas_sem_edt,
            "ALERTA",
            self._format_task_key,
        )

        edts_sem_projeto = [
            item
            for item in PmsEdt.objects.values("filial", "projeto", "revisao", "edt")
            if (item["filial"], item["projeto"], item["revisao"]) not in projetos
        ]
        self._record_count(
            "Integridade referencial",
            "EDTs sem projeto PMS correspondente",
            edts_sem_projeto,
            "ERRO",
            self._format_edt_key,
        )

        custos_por_projeto = set(
            PmsCustoTarefa.objects.values_list("filial", "projeto", "revisao")
        )
        projetos_sem_custos = [
            item
            for item in PmsProjeto.objects.values("filial", "projeto", "revisao")
            if (item["filial"], item["projeto"], item["revisao"])
            not in custos_por_projeto
        ]
        self._record_count(
            "Integridade referencial",
            "Projetos sem custos materializados",
            projetos_sem_custos,
            "ALERTA",
            self._format_project_key,
        )

    def _validar_revisoes(self):
        projetos_multi_revisao = list(
            PmsCustoTarefa.objects.values("projeto")
            .annotate(revisoes=Count("revisao", distinct=True))
            .filter(revisoes__gt=1)
            .order_by("projeto")
        )
        if not projetos_multi_revisao:
            self._ok("Revisao", "Nao ha projetos com multiplas revisoes em custos.")
            return

        exemplos = ", ".join(
            f"{item['projeto']} ({item['revisoes']} revisoes)"
            for item in projetos_multi_revisao[:5]
        )
        self._add(
            "ALERTA",
            "Revisao",
            (
                "Existem projetos com multiplas revisoes em PmsCustoTarefa. "
                "O selector deve usar somente a maior revisao por projeto tanto "
                "em modo projeto unico quanto em modo carteira. Valide os totais "
                "de carteira contra essa regra."
            ),
            f"Projetos afetados: {len(projetos_multi_revisao)}. Exemplos: {exemplos}",
        )

    def _validar_filtros(self, projetos):
        context_all = PmsDashboardSelector.get_context(filtros={"projeto": []})
        if context_all["modo_carteira"] and context_all["filtros"]["projetos"] == []:
            self._ok("Filtros", "Nenhum projeto selecionado ativa modo carteira.")
        else:
            self._add(
                "ERRO",
                "Filtros",
                "Filtro vazio nao ativou modo carteira como esperado.",
                str(context_all.get("filtros")),
            )

        primeiro = projetos[0]
        context_one = PmsDashboardSelector.get_context(filtros={"projeto": [primeiro]})
        if not context_one["modo_carteira"] and context_one["filtros"]["projeto"] == primeiro:
            self._ok("Filtros", "Um projeto selecionado ativa modo projeto.")
        else:
            self._add(
                "ERRO",
                "Filtros",
                "Filtro de projeto unico nao ativou modo projeto.",
                str(context_one.get("filtros")),
            )

        if len(projetos) > 1:
            context_multi = PmsDashboardSelector.get_context(filtros={"projeto": projetos})
            if context_multi["modo_carteira"] and context_multi["filtros"]["projetos"] == projetos:
                self._ok(
                    "Filtros",
                    "Multiplos projetos selecionados ativam carteira filtrada.",
                )
            else:
                self._add(
                    "ERRO",
                    "Filtros",
                    "Filtro multi-projeto nao preservou carteira filtrada.",
                    str(context_multi.get("filtros")),
                )
            querystring = context_multi.get("pagination_querystring", "")
            faltantes = [projeto for projeto in projetos if f"projeto={projeto}" not in querystring]
            if faltantes:
                self._add(
                    "ERRO",
                    "Filtros",
                    "Paginacao nao preserva todos os projetos selecionados.",
                    f"Faltantes: {', '.join(faltantes)}",
                )
            else:
                self._ok(
                    "Filtros",
                    "Paginacao preserva parametros repetidos de projeto.",
                )

        categorias = ["materia_prima"]
        context_categoria = PmsDashboardSelector.get_context(
            filtros={"projeto": [primeiro], "categorias": categorias}
        )
        if context_categoria["filtros"]["categorias"] == categorias:
            self._ok("Filtros", "Filtro de categoria e normalizado e preservado.")
        else:
            self._add(
                "ERRO",
                "Filtros",
                "Filtro de categoria nao foi preservado no contexto.",
                str(context_categoria.get("filtros")),
            )

    def _validar_projetos(self, projetos):
        for projeto in projetos:
            revisao = self._ultima_revisao(projeto)
            if not revisao:
                self._add("ALERTA", "Projeto", "Projeto sem revisao materializada.", projeto)
                continue

            custos = list(
                PmsCustoTarefa.objects.filter(projeto=projeto, revisao=revisao).values(
                    "filial",
                    "projeto",
                    "revisao",
                    "edt",
                    "tarefa",
                    "custo_previsto",
                    "custo_previsto_produtos",
                    "custo_previsto_despesas",
                    "custo_previsto_detalhado",
                    "custo_realizado",
                    "custo_empenhado",
                    "saldo_previsto_realizado",
                    "variacao_percentual",
                )
            )
            context = PmsDashboardSelector.get_context(filtros={"projeto": [projeto]})
            totais = self._somar_custos(custos)
            self._validar_kpis(projeto, totais, context["kpis"])
            self._validar_tabela_principal(projeto, revisao)
            self._validar_graficos_basicos(projeto, context, custos)
            self._validar_graficos_executivos(projeto, context, custos)

    def _validar_carteira(self, projetos):
        if not projetos:
            return
        context = PmsDashboardSelector.get_context(filtros={"projeto": projetos})
        custos = self._custos_ultima_revisao(projetos)
        totais = self._somar_custos(custos)
        self._validar_kpis("Carteira filtrada", totais, context["kpis"])
        self._validar_grafico_custo_empenho("Carteira filtrada", context, totais)
        self._validar_ordem_top10(
            "Graficos antigos",
            "grafico_projetos",
            context["grafico_projetos"].get("custo", []),
            context["grafico_projetos"].get("labels", []),
        )
        self._validar_paretos(context)

    def _validar_kpis(self, escopo, totais, kpis):
        checks = {
            "kpis.custo": (totais["custo_realizado"], kpis.get("custo")),
            "kpis.empenhado": (totais["custo_empenhado"], kpis.get("empenhado")),
            "kpis.saldo_empenho": (
                totais["custo_empenhado"] - totais["custo_realizado"],
                kpis.get("saldo_empenho"),
            ),
            "kpis.custo_sem_empenho": (
                totais["custo_sem_empenho"],
                kpis.get("custo_sem_empenho"),
            ),
            "kpis.custo_previsto": (totais["custo_previsto"], kpis.get("custo_previsto")),
            "kpis.custo_realizado": (
                totais["custo_realizado"],
                kpis.get("custo_realizado"),
            ),
            "kpis.custo_empenhado": (
                totais["custo_empenhado"],
                kpis.get("custo_empenhado"),
            ),
            "kpis.saldo_previsto_realizado": (
                totais["saldo_previsto_realizado"],
                kpis.get("saldo_previsto_realizado"),
            ),
            "kpis.percentual_custo_empenhado": (
                self._percentual(totais["custo_realizado"], totais["custo_empenhado"]),
                kpis.get("percentual_custo_empenhado"),
            ),
            "kpis.percentual_realizado": (
                self._percentual(totais["custo_realizado"], totais["custo_previsto"]),
                kpis.get("percentual_realizado"),
            ),
        }
        for nome, (esperado, atual) in checks.items():
            self._compare(
                "Totais principais",
                nome,
                esperado,
                atual,
                f"Escopo: {escopo}",
            )

    def _validar_tabela_principal(self, projeto, revisao):
        edts = PmsDashboardSelector._listar_edts(projeto, revisao)
        tarefas = PmsDashboardSelector._enriquecer_tarefas_categoria(
            PmsDashboardSelector._listar_tarefas(projeto, revisao)
        )
        custos = PmsDashboardSelector._listar_custos(projeto, revisao)
        custos_por_edt = consolidar_custos_por_edt(edts, tarefas, custos)
        linhas = PmsDashboardSelector._montar_linhas_hierarquia(
            edts=edts,
            tarefas=tarefas,
            custos=custos,
            custos_por_edt=custos_por_edt,
            caminhos_edt=montar_caminhos_edt(edts),
        )

        linhas_tarefa = [linha for linha in linhas if linha["tipo"] == "tarefa"]
        totais_linhas = self._somar_linhas(linhas_tarefa)
        totais_custos = self._somar_custos(custos)
        for campo_linha, campo_custo in (
            ("custo_realizado", "custo_realizado"),
            ("custo_empenhado", "custo_empenhado"),
            ("custo_previsto", "custo_previsto"),
        ):
            self._compare(
                "Tabela principal",
                f"soma tarefas {campo_linha}",
                totais_custos[campo_custo],
                totais_linhas[campo_linha],
                f"Projeto: {projeto} | Revisao: {revisao}",
            )

        esperados_edt = self._totais_edt_independentes(edts, tarefas, custos)
        for linha in [item for item in linhas if item["tipo"] == "edt"]:
            esperado = esperados_edt.get(linha["edt"], {})
            for campo in ("custo_realizado", "custo_empenhado", "custo_previsto"):
                self._compare(
                    "Tabela principal",
                    f"EDT {linha['edt']} {campo}",
                    esperado.get(campo, ZERO),
                    linha.get(campo, ZERO),
                    f"Projeto: {projeto}",
                )

        for linha in linhas[:500]:
            custo = self._decimal(linha.get("custo"))
            empenhado = self._decimal(linha.get("empenhado"))
            indicadores = calcular_indicadores_empenho(
                custo,
                empenhado,
                custo if empenhado == ZERO else self._decimal(linha.get("custo_sem_empenho")),
            )
            self._compare(
                "Tabela principal",
                f"{linha['tipo']} {linha['codigo']} saldo_empenho",
                indicadores["saldo_empenho"],
                linha.get("saldo_empenho"),
                f"Projeto: {projeto}",
            )
            self._compare(
                "Tabela principal",
                f"{linha['tipo']} {linha['codigo']} percentual_custo_empenhado",
                indicadores["percentual_custo_empenhado"],
                linha.get("percentual_custo_empenhado"),
                f"Projeto: {projeto}",
            )
            if linha.get("situacao_financeira") != indicadores["situacao_financeira"]:
                self._add(
                    "ERRO",
                    "Tabela principal",
                    "Situacao financeira divergente.",
                    (
                        f"Projeto: {projeto} | Linha: {linha['codigo']} | "
                        f"Esperado: {indicadores['situacao_financeira']} | "
                        f"Atual: {linha.get('situacao_financeira')}"
                    ),
                )
        self._ok(
            "Tabela principal",
            f"Estrutura recalculada para {projeto} sem alterar tabela renderizada.",
        )

    def _validar_graficos_basicos(self, projeto, context, custos):
        totais = self._somar_custos(custos)
        self._validar_grafico_custo_empenho(projeto, context, totais)
        self._validar_ordem_top10(
            "Graficos antigos",
            "grafico_edts",
            context["grafico_edts"].get("data", []),
            context["grafico_edts"].get("labels", []),
        )
        self._validar_ordem_top10(
            "Graficos antigos",
            "grafico_tarefas",
            context["grafico_tarefas"].get("custo", []),
            context["grafico_tarefas"].get("labels", []),
        )
        for nome in ("grafico_edts", "grafico_tarefas"):
            grafico = context[nome]
            labels = grafico.get("labels", [])
            tooltip_labels = grafico.get("tooltip_labels", [])
            if len(labels) != len(tooltip_labels):
                self._add(
                    "ERRO",
                    "Graficos antigos",
                    "Labels e tooltip_labels possuem tamanhos diferentes.",
                    f"{nome}: labels={len(labels)} tooltip_labels={len(tooltip_labels)}",
                )
            else:
                self._ok("Graficos antigos", f"{nome} preserva labels e tooltips.")

    def _validar_grafico_custo_empenho(self, escopo, context, totais):
        data = context["grafico_custo_empenho"].get("data", [])
        if len(data) != 2:
            self._add(
                "ERRO",
                "Graficos antigos",
                "grafico_custo_empenho nao possui dois valores.",
                f"Escopo: {escopo}",
            )
            return
        self._compare(
            "Graficos antigos",
            "grafico_custo_empenho custo",
            totais["custo_realizado"],
            data[0],
            f"Escopo: {escopo}",
        )
        self._compare(
            "Graficos antigos",
            "grafico_custo_empenho empenhado",
            totais["custo_empenhado"],
            data[1],
            f"Escopo: {escopo}",
        )

    def _validar_graficos_executivos(self, projeto, context, custos):
        kpis = context["kpis_executivos"]
        totais = self._somar_custos(custos)
        projeto_maior = kpis.get("projeto_maior_custo") or {}
        if projeto_maior and projeto_maior.get("projeto") != projeto:
            self._add(
                "ERRO",
                "KPIs executivos",
                "Projeto de maior custo diverge no modo projeto unico.",
                f"Projeto esperado: {projeto} | Atual: {projeto_maior.get('projeto')}",
            )
        else:
            self._ok("KPIs executivos", f"Maior custo coerente para {projeto}.")

        self._compare(
            "KPIs executivos",
            "media_custo_por_projeto",
            totais["custo_realizado"],
            kpis.get("media_custo_por_projeto"),
            f"Projeto: {projeto}",
        )
        self._compare(
            "KPIs executivos",
            "mediana_custo_por_projeto",
            totais["custo_realizado"],
            kpis.get("mediana_custo_por_projeto"),
            f"Projeto: {projeto}",
        )

        eficiencia = context["grafico_eficiencia"].get("datasets", [{}])[0].get("data", [])
        for ponto in eficiencia:
            if "x" not in ponto or "y" not in ponto:
                self._add(
                    "ERRO",
                    "Graficos executivos",
                    "grafico_eficiencia possui ponto sem eixo X ou Y.",
                    str(ponto),
                )
        self._ok("Graficos executivos", "grafico_eficiencia possui eixos X/Y.")

        matriz = context["matriz_risco"]
        for ponto in matriz.get("pontos", []):
            quadrante = ponto.get("quadrante")
            if quadrante not in {
                "alto_custo_acima_empenho",
                "alto_custo_dentro_empenho",
                "baixo_custo_acima_empenho",
                "baixo_custo_dentro_empenho",
            }:
                self._add(
                    "ERRO",
                    "Graficos executivos",
                    "Matriz de risco possui quadrante invalido.",
                    str(ponto),
                )
        self._validar_paretos(context)
        self._validar_serie_temporal_context(context)

    def _validar_paretos(self, context):
        for nome in ("pareto_projetos", "pareto_edts", "pareto_tarefas"):
            pareto = context[nome]
            self._validar_ordem_top10(
                "Pareto",
                nome,
                pareto.get("valores", []),
                pareto.get("labels", []),
            )
            acumulado = [self._decimal(item) for item in pareto.get("percentual_acumulado", [])]
            if any(atual < anterior for anterior, atual in zip(acumulado, acumulado[1:])):
                self._add(
                    "ERRO",
                    "Pareto",
                    "Percentual acumulado nao esta monotonicamente crescente.",
                    nome,
                )
            elif acumulado and acumulado[-1] > CEM + self.tolerance:
                self._add(
                    "ERRO",
                    "Pareto",
                    "Percentual acumulado passou de 100%.",
                    f"{nome}: {acumulado[-1]}",
                )
            else:
                self._ok("Pareto", f"{nome} possui acumulado coerente.")

    def _validar_temporal(self, projetos):
        revisoes = self._revisoes_ultima_por_projeto(projetos)
        custos = self._filtrar_ultima_revisao(
            list(
                PmsCustoTarefa.objects.filter(projeto__in=projetos).values(
                    "filial",
                    "projeto",
                    "revisao",
                    "edt",
                    "tarefa",
                    "custo_empenhado",
                    "custo_realizado",
                )
            ),
            revisoes,
        )
        temporais = self._filtrar_ultima_revisao(
            list(
                PmsCustoTemporalMensal.objects.filter(projeto__in=projetos).values(
                    "filial",
                    "projeto",
                    "revisao",
                    "edt",
                    "tarefa",
                    "competencia",
                    "custo_empenhado",
                    "custo_realizado",
                )
            ),
            revisoes,
        )

        for item in temporais:
            competencia = item["competencia"]
            if competencia.day != 1:
                self._add(
                    "ERRO",
                    "Serie temporal",
                    "Competencia temporal nao esta normalizada para o primeiro dia do mes.",
                    self._format_temporal_key(item),
                )

        por_tarefa_custo = defaultdict(lambda: {"custo_empenhado": ZERO, "custo_realizado": ZERO})
        for item in custos:
            chave = self._task_tuple(item)
            por_tarefa_custo[chave]["custo_empenhado"] += self._decimal(item["custo_empenhado"])
            por_tarefa_custo[chave]["custo_realizado"] += self._decimal(item["custo_realizado"])

        por_tarefa_temporal = defaultdict(lambda: {"custo_empenhado": ZERO, "custo_realizado": ZERO})
        duplicados = defaultdict(int)
        for item in temporais:
            chave = self._task_tuple(item)
            por_tarefa_temporal[chave]["custo_empenhado"] += self._decimal(item["custo_empenhado"])
            por_tarefa_temporal[chave]["custo_realizado"] += self._decimal(item["custo_realizado"])
            duplicados[(chave, item["competencia"])] += 1

        duplicados_reais = [item for item, count in duplicados.items() if count > 1]
        if duplicados_reais:
            self._add(
                "ERRO",
                "Serie temporal",
                "Ha duplicidade por tarefa/competencia.",
                f"Exemplos: {duplicados_reais[:5]}",
            )
        else:
            self._ok("Serie temporal", "Nao ha duplicidade por tarefa/competencia.")

        for chave, valores in list(por_tarefa_custo.items())[:500]:
            temporal = por_tarefa_temporal.get(
                chave, {"custo_empenhado": ZERO, "custo_realizado": ZERO}
            )
            for campo in ("custo_empenhado", "custo_realizado"):
                diff = valores[campo] - temporal[campo]
                if abs(diff) <= self.tolerance:
                    continue
                status = "ALERTA" if valores[campo] >= temporal[campo] else "ERRO"
                causa = (
                    "provavel ausencia de data financeira em SC7/SD1"
                    if status == "ALERTA"
                    else "serie temporal maior que consolidado"
                )
                self._add(
                    status,
                    "Serie temporal",
                    f"Divergencia entre consolidado e temporal em {campo}.",
                    (
                        f"{chave} | Consolidado: {valores[campo]} | "
                        f"Temporal: {temporal[campo]} | Diferenca: {diff} | {causa}"
                    ),
                )

    def _validar_serie_temporal_context(self, context):
        serie = context["serie_temporal"]
        if not serie.get("disponivel"):
            self._add(
                "ALERTA",
                "Serie temporal",
                "Serie temporal indisponivel no contexto do dashboard.",
                serie.get("limite", ""),
            )
            return

        labels = serie.get("labels", [])
        if labels != sorted(labels, key=lambda value: (value[-4:], value[:2])):
            self._add(
                "ERRO",
                "Serie temporal",
                "Labels da serie temporal nao estao em ordem cronologica.",
                str(labels[:12]),
            )
        else:
            self._ok("Serie temporal", "Labels estao em ordem cronologica.")

        realizado = [self._decimal(item) for item in serie.get("realizado", [])]
        acumulado = [self._decimal(item) for item in serie.get("realizado_acumulado", [])]
        esperado = []
        total = ZERO
        for valor in realizado:
            total += valor
            esperado.append(total)
        if len(esperado) != len(acumulado):
            self._add(
                "ERRO",
                "Serie temporal",
                "Tamanhos de realizado e acumulado divergem.",
                f"realizado={len(esperado)} acumulado={len(acumulado)}",
            )
        else:
            for index, (exp, atual) in enumerate(zip(esperado, acumulado)):
                self._compare(
                    "Serie temporal",
                    f"realizado_acumulado[{index}]",
                    exp,
                    atual,
                    "Contexto Chart.js",
                )

    def _validar_sdb_bruto(self, projetos):
        arquivos_esperados = {arquivo.lower() for arquivo in ComprasPmsETLService.ARQUIVOS_PADRAO}
        if not self.raw_sdb_dir.exists():
            self._add(
                "ALERTA",
                "Protheus bruto",
                "Diretorio de SDB bruto nao encontrado.",
                str(self.raw_sdb_dir),
            )
            return

        encontrados = {path.name.lower() for path in self.raw_sdb_dir.glob("*.sdb")}
        faltantes = sorted(arquivos_esperados - encontrados)
        if faltantes:
            self._add(
                "ALERTA",
                "Protheus bruto",
                "Validacao contra SDB bruto limitada por arquivos ausentes.",
                f"Ausentes: {', '.join(faltantes)}",
            )
            return

        try:
            dados_limpos = ComprasPmsETLService._ler_e_limpar_arquivos(str(self.raw_sdb_dir))
            ComprasPmsETLService._validar_schema(dados_limpos)
            custos_brutos = ComprasPmsETLService._montar_custos(
                df_tarefas=dados_limpos.get("af9", pd.DataFrame()),
                df_produtos=dados_limpos.get("afa", pd.DataFrame()),
                df_despesas=dados_limpos.get("afb", pd.DataFrame()),
                df_mapeamentos=dados_limpos.get("afg", pd.DataFrame()),
                df_pedidos=dados_limpos.get("sc7", pd.DataFrame()),
                df_recebimentos=dados_limpos.get("sd1", pd.DataFrame()),
            )
        except Exception as exc:
            self._add(
                "ALERTA",
                "Protheus bruto",
                "Nao foi possivel recomputar os SDBs brutos locais.",
                str(exc),
            )
            return

        bruto_por_chave = {
            (item.filial, item.projeto, item.revisao, item.tarefa): item
            for item in custos_brutos
            if item.projeto in projetos
        }
        banco_por_chave = {
            (item["filial"], item["projeto"], item["revisao"], item["tarefa"]): item
            for item in PmsCustoTarefa.objects.filter(projeto__in=projetos).values(
                "filial",
                "projeto",
                "revisao",
                "tarefa",
                "custo_previsto",
                "custo_empenhado",
                "custo_realizado",
            )
        }

        divergencias = 0
        for chave, bruto in list(bruto_por_chave.items())[: self.sample_size * 20]:
            banco = banco_por_chave.get(chave)
            if not banco:
                divergencias += 1
                self._add(
                    "ALERTA",
                    "Protheus bruto",
                    "Custo recomputado do SDB nao existe no banco materializado.",
                    str(chave),
                )
                continue
            for campo in ("custo_previsto", "custo_empenhado", "custo_realizado"):
                diff = abs(self._decimal(getattr(bruto, campo)) - self._decimal(banco[campo]))
                if diff > self.tolerance:
                    divergencias += 1
                    self._add(
                        "ALERTA",
                        "Protheus bruto",
                        f"Divergencia entre SDB bruto e banco em {campo}.",
                        f"{chave} | Diferenca: {diff}",
                    )
        if divergencias == 0:
            self._ok(
                "Protheus bruto",
                "Amostra recomputada dos SDBs locais bate com o banco materializado.",
            )

    def _validar_ordem_top10(self, section, nome, valores, labels):
        if len(valores) > 10:
            self._add(
                "ERRO",
                section,
                "Grafico possui mais de 10 itens.",
                f"{nome}: {len(valores)}",
            )
        if len(valores) != len(labels):
            self._add(
                "ERRO",
                section,
                "Grafico possui labels e valores com tamanhos diferentes.",
                f"{nome}: labels={len(labels)} valores={len(valores)}",
            )
            return
        decimais = [self._decimal(item) for item in valores]
        if any(atual > anterior for anterior, atual in zip(decimais, decimais[1:])):
            self._add(
                "ERRO",
                section,
                "Ranking nao esta ordenado do maior para o menor.",
                nome,
            )
        else:
            self._ok(section, f"{nome} esta limitado e ordenado.")

    def _totais_edt_independentes(self, edts, tarefas, custos):
        filhos = defaultdict(list)
        for edt in edts:
            filhos[edt.get("edt_pai") or ""].append(edt["edt"])

        def descendentes(codigo):
            resultado = set()
            pilha = list(filhos.get(codigo, []))
            while pilha:
                atual = pilha.pop()
                if atual in resultado or atual == codigo:
                    continue
                resultado.add(atual)
                pilha.extend(filhos.get(atual, []))
            return resultado

        tarefa_para_edt = {tarefa["tarefa"]: tarefa.get("edt") for tarefa in tarefas}
        custo_por_tarefa = {custo["tarefa"]: custo for custo in custos}
        resultado = {}
        for edt in edts:
            codigos = {edt["edt"], *descendentes(edt["edt"])}
            total = {
                "custo_previsto": ZERO,
                "custo_realizado": ZERO,
                "custo_empenhado": ZERO,
            }
            for tarefa, edt_tarefa in tarefa_para_edt.items():
                if edt_tarefa not in codigos:
                    continue
                custo = custo_por_tarefa.get(tarefa, {})
                for campo in total:
                    total[campo] += self._decimal(custo.get(campo))
            resultado[edt["edt"]] = total
        return resultado

    def _somar_custos(self, custos):
        total = {
            "custo_previsto": ZERO,
            "custo_realizado": ZERO,
            "custo_empenhado": ZERO,
            "saldo_previsto_realizado": ZERO,
            "custo_sem_empenho": ZERO,
        }
        for custo in custos:
            for campo in MONEY_FIELDS:
                total[campo] += self._decimal(custo.get(campo))
            if self._decimal(custo.get("custo_empenhado")) == ZERO:
                total["custo_sem_empenho"] += self._decimal(custo.get("custo_realizado"))
        return total

    def _somar_linhas(self, linhas):
        total = {
            "custo_previsto": ZERO,
            "custo_realizado": ZERO,
            "custo_empenhado": ZERO,
        }
        for linha in linhas:
            for campo in total:
                total[campo] += self._decimal(linha.get(campo))
        return total

    def _ultima_revisao(self, projeto):
        return (
            PmsProjeto.objects.filter(projeto=projeto)
            .aggregate(revisao=Max("revisao"))
            .get("revisao")
        )

    def _revisoes_ultima_por_projeto(self, projetos):
        return {
            item["projeto"]: item["revisao"]
            for item in (
                PmsProjeto.objects.filter(projeto__in=projetos)
                .values("projeto")
                .annotate(revisao=Max("revisao"))
            )
            if item.get("projeto") and item.get("revisao")
        }

    def _filtrar_ultima_revisao(self, itens, revisoes):
        return [
            item
            for item in itens
            if item.get("revisao") == revisoes.get(item.get("projeto"))
        ]

    def _custos_ultima_revisao(self, projetos):
        return self._filtrar_ultima_revisao(
            list(
                PmsCustoTarefa.objects.filter(projeto__in=projetos).values(
                    "projeto",
                    "revisao",
                    "edt",
                    "tarefa",
                    "custo_previsto",
                    "custo_realizado",
                    "custo_empenhado",
                    "saldo_previsto_realizado",
                )
            ),
            self._revisoes_ultima_por_projeto(projetos),
        )

    def _compare(self, section, label, expected, actual, context=""):
        expected = self._decimal(expected)
        actual = self._decimal(actual)
        diff = abs(expected - actual)
        if diff <= self.tolerance:
            self._ok(section, f"{label} validado.")
            return
        self._add(
            "ERRO",
            section,
            f"Divergencia em {label}.",
            f"Esperado: {expected} | Atual: {actual} | Dif: {diff} | {context}",
        )

    def _record_count(self, section, message, rows, status, formatter):
        if rows:
            exemplos = "; ".join(formatter(item) for item in rows[:5])
            self._add(
                status,
                section,
                f"{message}: {len(rows)} ocorrencia(s).",
                f"Exemplos: {exemplos}",
            )
        else:
            self._ok(section, message)

    def _print_report(self, projetos):
        status = self._status_final()
        self._write_header("Resumo geral")
        self.stdout.write(f"Projetos amostrados: {len(projetos)}")
        if projetos:
            self.stdout.write(", ".join(projetos))
        self.stdout.write(f"Itens OK: {len(self.ok_items)}")
        self.stdout.write(f"Alertas: {len(self._findings('ALERTA'))}")
        self.stdout.write(f"Divergencias criticas: {len(self._findings('ERRO'))}")
        self.stdout.write("")

        self._print_findings("Divergencias criticas", "ERRO")
        self._print_findings("Alertas", "ALERTA")

        self._write_header("Itens OK")
        for item in self.ok_items[:80]:
            self.stdout.write(f"[OK] {item}")
        if len(self.ok_items) > 80:
            self.stdout.write(f"... {len(self.ok_items) - 80} itens OK omitidos.")
        self.stdout.write("")

        self._write_header("Recomendacoes")
        if self._findings("ERRO"):
            self.stdout.write(
                "- Nao corrigir automaticamente. Revisar causa, impacto e proposta "
                "antes de alterar calculos ou filtros."
            )
        if self._findings("ALERTA"):
            self.stdout.write(
                "- Investigar alertas de revisao, temporalidade e SDB antes de usar "
                "o dashboard como numero executivo final."
            )
        if status == "OK":
            self.stdout.write("- Nenhuma divergencia relevante encontrada na amostra.")

        self.stdout.write("")
        self._write_header("Status final")
        style = self.style.SUCCESS if status == "OK" else self.style.WARNING
        if status == "ERRO":
            style = self.style.ERROR
        self.stdout.write(style(status))
        return status

    def _print_findings(self, title, status):
        self._write_header(title)
        findings = self._findings(status)
        if not findings:
            self.stdout.write(f"Nenhum item {status}.")
            self.stdout.write("")
            return
        for finding in findings:
            self.stdout.write(f"[{finding.status}] {finding.section}: {finding.message}")
            if finding.context:
                self.stdout.write(f"  Contexto: {finding.context}")
        self.stdout.write("")

    def _findings(self, status):
        return [finding for finding in self.findings if finding.status == status]

    def _status_final(self):
        status = "OK"
        for finding in self.findings:
            if STATUS_ORDER[finding.status] > STATUS_ORDER[status]:
                status = finding.status
        return status

    def _add(self, status, section, message, context=""):
        self.findings.append(Finding(status, section, message, context))

    def _ok(self, section, message):
        self.ok_items.append(f"{section}: {message}")

    def _write_header(self, title):
        self.stdout.write("")
        self.stdout.write(title)
        self.stdout.write("-" * len(title))

    @staticmethod
    def _parse_projetos(raw_values):
        projetos = []
        vistos = set()
        for raw in raw_values or []:
            for item in str(raw).split(","):
                projeto = item.strip()
                if projeto and projeto not in vistos:
                    vistos.add(projeto)
                    projetos.append(projeto)
        return projetos

    @staticmethod
    def _percentual(valor, base):
        valor = Command._decimal(valor)
        base = Command._decimal(base)
        return (valor / base) * CEM if base else ZERO

    @staticmethod
    def _decimal(value):
        if value is None or value == "":
            return ZERO
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return ZERO

    @staticmethod
    def _task_tuple(item):
        return (item["filial"], item["projeto"], item["revisao"], item["tarefa"])

    @staticmethod
    def _format_project_key(item):
        return f"{item['filial']} | {item['projeto']} | rev {item['revisao']}"

    @staticmethod
    def _format_edt_key(item):
        return (
            f"{item['filial']} | {item['projeto']} | rev {item['revisao']} | "
            f"EDT {item['edt']}"
        )

    @staticmethod
    def _format_task_key(item):
        return (
            f"{item['filial']} | {item['projeto']} | rev {item['revisao']} | "
            f"Tarefa {item['tarefa']} | EDT {item.get('edt') or '-'}"
        )

    @staticmethod
    def _format_cost_key(item):
        return (
            f"{item['filial']} | {item['projeto']} | rev {item['revisao']} | "
            f"Tarefa {item['tarefa']} | EDT {item.get('edt') or '-'}"
        )

    @staticmethod
    def _format_temporal_key(item):
        return (
            f"{item['filial']} | {item['projeto']} | rev {item['revisao']} | "
            f"Tarefa {item['tarefa']} | {item['competencia']}"
        )
