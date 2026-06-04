from __future__ import annotations

from typing import TypeVar

from django.conf import settings
from django.db import models
from django.utils import timezone


TSoftDeleteModel = TypeVar("TSoftDeleteModel", bound="SoftDeleteModel")


class SoftDeleteQuerySet(models.QuerySet[TSoftDeleteModel]):
    def delete(self) -> tuple[int, dict[str, int]]:
        updated = self.update(ativo=False, updated_at=timezone.now())
        return updated, {self.model._meta.label: updated}

    def active(self) -> "SoftDeleteQuerySet[TSoftDeleteModel]":
        return self.filter(ativo=True)


class ActiveManager(models.Manager[TSoftDeleteModel]):
    def get_queryset(self) -> SoftDeleteQuerySet[TSoftDeleteModel]:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(ativo=True)


class AllObjectsManager(models.Manager[TSoftDeleteModel]):
    def get_queryset(self) -> SoftDeleteQuerySet[TSoftDeleteModel]:
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    ativo = models.BooleanField(default=True, db_index=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using: str | None = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:
        self.ativo = False
        self.save(using=using, update_fields=["ativo", "updated_at"])
        return 1, {self._meta.label: 1}


class TipoMovimentacao(models.TextChoices):
    ENTRADA = "ENTRADA", "Entrada"
    SAIDA = "SAIDA", "Saida"


class OrigemMovimentacao(models.TextChoices):
    NF_ENTRADA = "NF_ENTRADA", "Nota Fiscal de Entrada"
    NF_SAIDA = "NF_SAIDA", "Nota Fiscal de Saida"
    MOV_INTERNA = "MOV_INTERNA", "Movimentacao Interna"


class StatusAtivo(models.TextChoices):
    OPERANDO = "operando", "Operando"
    PARADO = "parado", "Parado"
    MANUTENCAO = "manutencao", "Em manutencao"
    INATIVO = "inativo", "Inativo"


class CriticidadeAtivo(models.TextChoices):
    BAIXA = "baixa", "Baixa"
    MEDIA = "media", "Media"
    ALTA = "alta", "Alta"
    CRITICA = "critica", "Critica"


class TipoManutencao(models.TextChoices):
    PREVENTIVA = "preventiva", "Preventiva"
    CORRETIVA = "corretiva", "Corretiva"
    PREDITIVA = "preditiva", "Preditiva"
    INSPECAO = "inspecao", "Inspecao"


class StatusManutencao(models.TextChoices):
    PLANEJADA = "planejada", "Planejada"
    EM_EXECUCAO = "em_execucao", "Em execucao"
    CONCLUIDA = "concluida", "Concluida"
    CANCELADA = "cancelada", "Cancelada"


class TipoDowntime(models.TextChoices):
    NAO_PLANEJADO = "nao_planejado", "Nao planejado"
    PLANEJADO = "planejado", "Planejado"
    SETUP = "setup", "Setup"
    QUALIDADE = "qualidade", "Qualidade"
    FALTA_MATERIAL = "falta_material", "Falta de material"
    MANUTENCAO = "manutencao", "Manutencao"


class OrigemApontamento(models.TextChoices):
    MANUAL = "manual", "Manual"
    CELERY = "celery", "Celery"
    ETL = "etl", "ETL"
    SISTEMA = "sistema", "Sistema"


class TipoAlerta(models.TextChoices):
    PREVENTIVA = "preventiva", "Preventiva"
    DOWNTIME_ABERTO = "downtime_aberto", "Downtime aberto"


class StatusAlerta(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    ENVIANDO = "enviando", "Enviando"
    ENVIADO = "enviado", "Enviado"
    FALHA = "falha", "Falha"


class MovimentacaoEstoquePCP(SoftDeleteModel):
    filial = models.CharField(max_length=10, default="", db_index=True, verbose_name="Filial")
    produto_codigo = models.CharField(max_length=50, db_index=True, verbose_name="Codigo do Produto")
    data_movimentacao = models.DateField(db_index=True, verbose_name="Data da Movimentacao")
    tipo_movimentacao = models.CharField(
        max_length=10,
        choices=TipoMovimentacao.choices,
        db_index=True,
        verbose_name="Tipo de Movimentacao",
    )
    origem_movimentacao = models.CharField(
        max_length=20,
        choices=OrigemMovimentacao.choices,
        db_index=True,
        verbose_name="Origem da Movimentacao",
    )
    quantidade = models.DecimalField(max_digits=19, decimal_places=5, verbose_name="Quantidade")
    documento = models.CharField(
        max_length=20,
        blank=True,
        default="",
        db_index=True,
        verbose_name="Documento de Origem",
    )
    cf_operacao = models.CharField(
        max_length=5,
        blank=True,
        default="",
        verbose_name="CF da Operacao (SD3)",
    )

    class Meta:
        verbose_name = "Movimentacao de Estoque (PCP)"
        verbose_name_plural = "Movimentacoes de Estoque (PCP)"
        db_table = "pcp_movimentacaoestoquepcp"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "filial",
                    "produto_codigo",
                    "data_movimentacao",
                    "tipo_movimentacao",
                    "origem_movimentacao",
                    "documento",
                    "cf_operacao",
                ],
                name="pcp_movimentacao_natural_uniq",
            ),
            models.CheckConstraint(
                check=models.Q(quantidade__gte=0),
                name="pcp_movimentacao_quantidade_gte_zero",
            ),
        ]
        indexes = [
            models.Index(fields=["filial", "produto_codigo", "data_movimentacao"], name="pcp_mov_fil_prod_data_idx"),
            models.Index(fields=["ativo", "data_movimentacao"], name="pcp_mov_ativo_data_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.produto_codigo} - {self.data_movimentacao}"


class PcpAreaProducao(SoftDeleteModel):
    codigo = models.CharField(max_length=30, unique=True, db_index=True, verbose_name="Codigo")
    nome = models.CharField(max_length=120, db_index=True, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descricao")

    class Meta:
        verbose_name = "Area de Producao"
        verbose_name_plural = "Areas de Producao"
        db_table = "pcp_area_producao"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"


class PcpAtivo(SoftDeleteModel):
    codigo = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="Codigo")
    nome = models.CharField(max_length=150, db_index=True, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descricao")
    fabricante = models.CharField(max_length=120, blank=True, verbose_name="Fabricante")
    modelo = models.CharField(max_length=120, blank=True, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=120, blank=True, db_index=True, verbose_name="Numero de Serie")
    area = models.ForeignKey(
        PcpAreaProducao,
        on_delete=models.PROTECT,
        related_name="ativos",
        db_index=True,
        verbose_name="Area de Producao",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusAtivo.choices,
        default=StatusAtivo.OPERANDO,
        db_index=True,
        verbose_name="Status",
    )
    criticidade = models.CharField(
        max_length=20,
        choices=CriticidadeAtivo.choices,
        default=CriticidadeAtivo.MEDIA,
        db_index=True,
        verbose_name="Criticidade",
    )

    class Meta:
        verbose_name = "Ativo PCP"
        verbose_name_plural = "Ativos PCP"
        db_table = "pcp_ativo"
        indexes = [
            models.Index(fields=["area", "ativo"], name="pcp_ativo_area_ativo_idx"),
            models.Index(fields=["status", "ativo"], name="pcp_ativo_status_idx"),
            models.Index(fields=["criticidade", "ativo"], name="pcp_ativo_criticidade_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"


class PcpPlanoManutencao(SoftDeleteModel):
    ativo_pcp = models.ForeignKey(
        PcpAtivo,
        on_delete=models.PROTECT,
        related_name="planos_manutencao",
        db_index=True,
        verbose_name="Ativo",
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoManutencao.choices,
        default=TipoManutencao.PREVENTIVA,
        db_index=True,
        verbose_name="Tipo",
    )
    nome = models.CharField(max_length=150, db_index=True, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descricao")
    intervalo_dias = models.PositiveIntegerField(null=True, blank=True, verbose_name="Intervalo em dias")

    class Meta:
        verbose_name = "Plano de Manutencao"
        verbose_name_plural = "Planos de Manutencao"
        db_table = "pcp_plano_manutencao"
        constraints = [
            models.CheckConstraint(
                check=models.Q(ativo=False) | models.Q(intervalo_dias__gt=0),
                name="pcp_plano_ativo_exige_intervalo",
            ),
        ]
        indexes = [
            models.Index(fields=["ativo_pcp", "ativo"], name="pcp_plano_ativo_idx"),
            models.Index(fields=["tipo", "ativo"], name="pcp_plano_tipo_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.ativo_pcp.codigo} - {self.nome}"


class PcpProgramacaoManutencao(SoftDeleteModel):
    plano = models.ForeignKey(
        PcpPlanoManutencao,
        on_delete=models.PROTECT,
        related_name="programacoes",
        db_index=True,
        verbose_name="Plano",
    )
    data_prevista = models.DateField(db_index=True, verbose_name="Data prevista")
    data_limite = models.DateField(null=True, blank=True, db_index=True, verbose_name="Data limite")
    status = models.CharField(
        max_length=20,
        choices=StatusManutencao.choices,
        default=StatusManutencao.PLANEJADA,
        db_index=True,
        verbose_name="Status",
    )
    origem = models.CharField(
        max_length=20,
        choices=OrigemApontamento.choices,
        default=OrigemApontamento.SISTEMA,
        db_index=True,
        verbose_name="Origem",
    )

    class Meta:
        verbose_name = "Programacao de Manutencao"
        verbose_name_plural = "Programacoes de Manutencao"
        db_table = "pcp_programacao_manutencao"
        constraints = [
            models.UniqueConstraint(
                fields=["plano", "data_prevista"],
                condition=models.Q(ativo=True),
                name="pcp_programacao_plano_data_uniq",
            ),
            models.UniqueConstraint(
                fields=["plano"],
                condition=models.Q(
                    ativo=True,
                    status__in=[StatusManutencao.PLANEJADA, StatusManutencao.EM_EXECUCAO],
                ),
                name="pcp_programacao_pendente_plano_uniq",
            ),
            models.CheckConstraint(
                check=models.Q(data_limite__isnull=True) | models.Q(data_limite__gte=models.F("data_prevista")),
                name="pcp_programacao_limite_gte_prevista",
            ),
        ]
        indexes = [
            models.Index(fields=["plano", "status"], name="pcp_prog_plano_status_idx"),
            models.Index(fields=["status", "data_prevista"], name="pcp_prog_status_data_idx"),
            models.Index(fields=["ativo", "data_prevista"], name="pcp_prog_ativo_flag_data_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.plano.ativo_pcp.codigo} - {self.data_prevista}"


class PcpExecucaoManutencao(SoftDeleteModel):
    programacao = models.ForeignKey(
        PcpProgramacaoManutencao,
        on_delete=models.SET_NULL,
        related_name="execucoes",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Programacao",
    )
    ativo_pcp = models.ForeignKey(
        PcpAtivo,
        on_delete=models.PROTECT,
        related_name="execucoes_manutencao",
        db_index=True,
        verbose_name="Ativo",
    )
    tipo = models.CharField(max_length=20, choices=TipoManutencao.choices, db_index=True, verbose_name="Tipo")
    data_inicio = models.DateTimeField(db_index=True, verbose_name="Data de inicio")
    data_fim = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="Data de fim")
    observacao = models.TextField(blank=True, verbose_name="Observacao")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="execucoes_manutencao_pcp",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Responsavel",
    )

    class Meta:
        verbose_name = "Execucao de Manutencao"
        verbose_name_plural = "Execucoes de Manutencao"
        db_table = "pcp_execucao_manutencao"
        constraints = [
            models.UniqueConstraint(
                fields=["ativo_pcp"],
                condition=models.Q(ativo=True, data_fim__isnull=True),
                name="pcp_execucao_aberta_ativo_uniq",
            ),
            models.CheckConstraint(
                check=models.Q(data_fim__isnull=True) | models.Q(data_fim__gt=models.F("data_inicio")),
                name="pcp_execucao_fim_gt_inicio",
            ),
        ]
        indexes = [
            models.Index(fields=["ativo_pcp", "data_inicio"], name="pcp_exec_ativo_inicio_idx"),
            models.Index(fields=["tipo", "data_inicio"], name="pcp_exec_tipo_inicio_idx"),
            models.Index(fields=["responsavel", "data_inicio"], name="pcp_exec_resp_inicio_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.ativo_pcp.codigo} - {self.tipo} - {self.data_inicio:%Y-%m-%d}"


class PcpDowntime(SoftDeleteModel):
    ativo_pcp = models.ForeignKey(
        PcpAtivo,
        on_delete=models.PROTECT,
        related_name="downtimes",
        db_index=True,
        verbose_name="Ativo",
    )
    tipo = models.CharField(max_length=30, choices=TipoDowntime.choices, db_index=True, verbose_name="Tipo")
    inicio = models.DateTimeField(db_index=True, verbose_name="Inicio")
    fim = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="Fim")
    duracao_minutos = models.PositiveIntegerField(null=True, blank=True, db_index=True, verbose_name="Duracao em minutos")
    motivo = models.CharField(max_length=255, db_index=True, verbose_name="Motivo")
    observacao = models.TextField(blank=True, verbose_name="Observacao")
    origem = models.CharField(
        max_length=20,
        choices=OrigemApontamento.choices,
        default=OrigemApontamento.MANUAL,
        db_index=True,
        verbose_name="Origem",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="downtimes_pcp",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Responsavel",
    )

    class Meta:
        verbose_name = "Downtime PCP"
        verbose_name_plural = "Downtimes PCP"
        db_table = "pcp_downtime"
        constraints = [
            models.UniqueConstraint(
                fields=["ativo_pcp"],
                condition=models.Q(ativo=True, fim__isnull=True),
                name="pcp_downtime_aberto_ativo_uniq",
            ),
            models.CheckConstraint(
                check=models.Q(fim__isnull=True) | models.Q(fim__gt=models.F("inicio")),
                name="pcp_downtime_fim_gt_inicio",
            ),
        ]
        indexes = [
            models.Index(fields=["ativo_pcp", "inicio"], name="pcp_down_ativo_inicio_idx"),
            models.Index(fields=["tipo", "inicio"], name="pcp_down_tipo_inicio_idx"),
            models.Index(fields=["fim", "ativo"], name="pcp_down_fim_ativo_idx"),
            models.Index(fields=["origem", "inicio"], name="pcp_down_origem_inicio_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.ativo_pcp.codigo} - {self.inicio:%Y-%m-%d %H:%M}"


class PcpParametroAlerta(SoftDeleteModel):
    ativo_pcp = models.ForeignKey(
        PcpAtivo,
        on_delete=models.PROTECT,
        related_name="parametros_alerta",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Ativo",
    )
    area = models.ForeignKey(
        PcpAreaProducao,
        on_delete=models.PROTECT,
        related_name="parametros_alerta",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Area",
    )
    dias_antecedencia = models.PositiveIntegerField(default=7, verbose_name="Dias de antecedencia")
    emails_destino = models.TextField(verbose_name="Emails destino")
    alertar_preventiva = models.BooleanField(default=True, verbose_name="Alertar preventiva")
    alertar_downtime_aberto = models.BooleanField(default=True, verbose_name="Alertar downtime aberto")

    class Meta:
        verbose_name = "Parametro de Alerta PCP"
        verbose_name_plural = "Parametros de Alerta PCP"
        db_table = "pcp_parametro_alerta"
        constraints = [
            models.CheckConstraint(
                check=~models.Q(ativo_pcp__isnull=False, area__isnull=False),
                name="pcp_parametro_alerta_um_alvo",
            ),
        ]
        indexes = [
            models.Index(fields=["ativo_pcp", "ativo"], name="pcp_alerta_ativo_idx"),
            models.Index(fields=["area", "ativo"], name="pcp_alerta_area_idx"),
        ]

    def __str__(self) -> str:
        if self.ativo_pcp_id:
            alvo = self.ativo_pcp.codigo
        elif self.area_id:
            alvo = self.area.codigo
        else:
            alvo = "global"
        return f"Alerta PCP - {alvo}"


class PcpAlertaEnviado(SoftDeleteModel):
    tipo_alerta = models.CharField(max_length=30, choices=TipoAlerta.choices, db_index=True, verbose_name="Tipo")
    chave_idempotencia = models.CharField(max_length=120, unique=True, db_index=True, verbose_name="Chave de idempotencia")
    parametro = models.ForeignKey(
        PcpParametroAlerta,
        on_delete=models.SET_NULL,
        related_name="alertas_enviados",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Parametro",
    )
    programacao = models.ForeignKey(
        PcpProgramacaoManutencao,
        on_delete=models.SET_NULL,
        related_name="alertas_enviados",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Programacao",
    )
    downtime = models.ForeignKey(
        PcpDowntime,
        on_delete=models.SET_NULL,
        related_name="alertas_enviados",
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Downtime",
    )
    data_referencia = models.DateField(db_index=True, verbose_name="Data de referencia")
    destinatarios = models.TextField(verbose_name="Destinatarios")
    assunto = models.CharField(max_length=180, verbose_name="Assunto")
    status = models.CharField(
        max_length=20,
        choices=StatusAlerta.choices,
        default=StatusAlerta.PENDENTE,
        db_index=True,
        verbose_name="Status",
    )
    tentativas = models.PositiveIntegerField(default=0, verbose_name="Tentativas")
    ultimo_erro = models.TextField(blank=True, verbose_name="Ultimo erro")
    enviado_em = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="Enviado em")

    class Meta:
        verbose_name = "Alerta Enviado PCP"
        verbose_name_plural = "Alertas Enviados PCP"
        db_table = "pcp_alerta_enviado"
        indexes = [
            models.Index(fields=["tipo_alerta", "data_referencia"], name="pcp_alerta_env_tipo_data_idx"),
            models.Index(fields=["status", "ativo"], name="pcp_alerta_env_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.tipo_alerta} - {self.data_referencia}"
