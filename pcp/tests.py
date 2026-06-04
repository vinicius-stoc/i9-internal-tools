from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from pcp.models import (
    MovimentacaoEstoquePCP,
    OrigemMovimentacao,
    PcpAlertaEnviado,
    PcpAreaProducao,
    PcpAtivo,
    PcpExecucaoManutencao,
    PcpParametroAlerta,
    PcpPlanoManutencao,
    StatusAlerta,
    StatusAtivo,
    StatusManutencao,
    TipoManutencao,
    TipoMovimentacao,
)
from pcp.services import (
    AlertaManutencaoService,
    DowntimeService,
    PCPEstoqueETLService,
    PlanoManutencaoService,
    ProgramacaoManutencaoService,
)
from pcp.services.exceptions import PcpConflictError, PcpValidationError


class PcpMaintenanceServicesTests(TestCase):
    def setUp(self) -> None:
        self.area = PcpAreaProducao.objects.create(codigo="LINHA-01", nome="Linha 01")
        self.ativo = PcpAtivo.objects.create(codigo="MAQ-001", nome="Centro de Usinagem", area=self.area)

    def test_criar_plano_exige_intervalo_valido(self) -> None:
        with self.assertRaises(PcpValidationError):
            PlanoManutencaoService.criar_plano(
                ativo_pcp=self.ativo,
                nome="Preventiva mensal",
                tipo=TipoManutencao.PREVENTIVA,
            )

    def test_recalculo_diario_mantem_uma_programacao_pendente(self) -> None:
        plano = PcpPlanoManutencao.objects.create(
            ativo_pcp=self.ativo,
            nome="Preventiva mensal",
            intervalo_dias=30,
        )

        primeira = ProgramacaoManutencaoService.gerar_proxima_preventiva(
            plano=plano,
            referencia=date(2026, 6, 3),
        )
        segunda = ProgramacaoManutencaoService.gerar_proxima_preventiva(
            plano=plano,
            referencia=date(2026, 6, 4),
        )

        self.assertTrue(primeira.criada)
        self.assertFalse(segunda.criada)
        self.assertEqual(primeira.programacao.pk, segunda.programacao.pk)
        self.assertEqual(primeira.programacao.data_prevista, date(2026, 7, 3))
        self.assertEqual(plano.programacoes.count(), 1)

    def test_concluir_execucao_gera_proxima_programacao(self) -> None:
        plano = PcpPlanoManutencao.objects.create(
            ativo_pcp=self.ativo,
            nome="Preventiva mensal",
            intervalo_dias=30,
        )
        programacao = ProgramacaoManutencaoService.gerar_proxima_preventiva(
            plano=plano,
            referencia=date(2026, 6, 3),
        ).programacao
        inicio = timezone.now()
        execucao = PcpExecucaoManutencao.objects.create(
            programacao=programacao,
            ativo_pcp=self.ativo,
            tipo=TipoManutencao.PREVENTIVA,
            data_inicio=inicio,
        )

        ProgramacaoManutencaoService.concluir_execucao(
            execucao=execucao,
            data_fim=inicio + timedelta(hours=1),
        )

        programacao.refresh_from_db()
        self.assertEqual(programacao.status, StatusManutencao.CONCLUIDA)
        self.assertEqual(plano.programacoes.filter(status=StatusManutencao.PLANEJADA).count(), 1)

    def test_downtime_abertura_e_fechamento_calculam_duracao_e_status(self) -> None:
        inicio = timezone.now()
        downtime = DowntimeService.abrir_downtime(ativo_pcp=self.ativo, motivo="Falha eletrica", inicio=inicio)

        with self.assertRaises(PcpConflictError):
            DowntimeService.abrir_downtime(ativo_pcp=self.ativo, motivo="Segunda falha", inicio=inicio)

        fechado = DowntimeService.fechar_downtime(downtime=downtime, fim=inicio + timedelta(minutes=91))
        self.ativo.refresh_from_db()

        self.assertEqual(fechado.duracao_minutos, 91)
        self.assertEqual(self.ativo.status, StatusAtivo.OPERANDO)

    def test_soft_delete_remove_do_manager_padrao_sem_excluir_registro(self) -> None:
        ativo_id = self.ativo.id
        self.ativo.delete()

        self.assertFalse(PcpAtivo.objects.filter(id=ativo_id).exists())
        self.assertTrue(PcpAtivo.all_objects.filter(id=ativo_id, ativo=False).exists())

    def test_all_objects_tambem_aplica_soft_delete_em_lote(self) -> None:
        ativo_id = self.ativo.id
        PcpAtivo.all_objects.filter(id=ativo_id).delete()

        self.assertFalse(PcpAtivo.objects.filter(id=ativo_id).exists())
        self.assertTrue(PcpAtivo.all_objects.filter(id=ativo_id, ativo=False).exists())

    def test_parametro_alerta_nao_aceita_area_e_ativo_simultaneamente(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            PcpParametroAlerta.objects.create(
                ativo_pcp=self.ativo,
                area=self.area,
                emails_destino="pcp@example.com",
            )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_alerta_preventiva_e_idempotente_por_data_referencia(self) -> None:
        plano = PcpPlanoManutencao.objects.create(
            ativo_pcp=self.ativo,
            nome="Preventiva diaria",
            intervalo_dias=1,
        )
        referencia = date(2026, 6, 3)
        ProgramacaoManutencaoService.gerar_proxima_preventiva(plano=plano, referencia=referencia)
        PcpParametroAlerta.objects.create(
            ativo_pcp=self.ativo,
            dias_antecedencia=7,
            emails_destino="pcp@example.com;invalido",
        )

        primeiro_envio = AlertaManutencaoService.enviar_alertas_preventivas(referencia=referencia)
        segundo_envio = AlertaManutencaoService.enviar_alertas_preventivas(referencia=referencia)

        alerta = PcpAlertaEnviado.objects.get()
        self.assertEqual(primeiro_envio, 1)
        self.assertEqual(segundo_envio, 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(alerta.status, StatusAlerta.ENVIADO)
        self.assertEqual(alerta.tentativas, 1)


class PcpEstoqueETLTests(TestCase):
    def test_etl_processa_chaves_minusculas_e_diferencia_tipo_movimentacao(self) -> None:
        sd1 = pd.DataFrame(
            [
                {
                    "D1_FILIAL": "01",
                    "D1_COD": "PROD-1",
                    "D1_DTDIGIT": "20260603",
                    "D1_QUANT": "10.5",
                    "D1_DOC": "100",
                }
            ]
        )
        sd3 = pd.DataFrame(
            [
                {
                    "D3_FILIAL": "01",
                    "D3_COD": "PROD-1",
                    "D3_EMISSAO": "20260603",
                    "D3_QUANT": "2",
                    "D3_DOC": "200",
                    "D3_TM": "RE",
                    "D3_CF": "001",
                },
                {
                    "D3_FILIAL": "01",
                    "D3_COD": "PROD-1",
                    "D3_EMISSAO": "20260603",
                    "D3_QUANT": "1",
                    "D3_DOC": "200",
                    "D3_TM": "DE",
                    "D3_CF": "001",
                },
            ]
        )

        processado = PCPEstoqueETLService.transformar_e_salvar({"sd1": sd1, "sd3": sd3})

        self.assertTrue(processado)
        self.assertEqual(MovimentacaoEstoquePCP.objects.count(), 3)
        self.assertTrue(
            MovimentacaoEstoquePCP.objects.filter(
                origem_movimentacao=OrigemMovimentacao.MOV_INTERNA,
                tipo_movimentacao=TipoMovimentacao.SAIDA,
            ).exists()
        )
        self.assertTrue(
            MovimentacaoEstoquePCP.objects.filter(
                origem_movimentacao=OrigemMovimentacao.MOV_INTERNA,
                tipo_movimentacao=TipoMovimentacao.ENTRADA,
            ).exists()
        )


class PcpOperationalApiTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="pcp_user",
            email="pcp_user@example.com",
            password="senha-forte-123",
        )
        self.user_sem_grupo = user_model.objects.create_user(
            username="sem_grupo",
            email="sem_grupo@example.com",
            password="senha-forte-123",
        )
        grupo_pcp, _ = Group.objects.get_or_create(name="PCP")
        self.user.groups.add(grupo_pcp)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.area = PcpAreaProducao.objects.create(codigo="LINHA-API", nome="Linha API")
        self.ativo = PcpAtivo.objects.create(codigo="MAQ-API", nome="Maquina API", area=self.area)

    def test_api_bloqueia_usuario_autenticado_sem_grupo_pcp(self) -> None:
        self.client.force_authenticate(user=self.user_sem_grupo)
        response = self.client.get("/api/pcp/ativos/")
        self.assertEqual(response.status_code, 403)

    def test_api_rejeita_filtro_invalido(self) -> None:
        response = self.client.get("/api/pcp/programacoes-manutencao/?data_inicio=invalida")
        self.assertEqual(response.status_code, 400)

    def test_api_abre_e_fecha_downtime_via_services(self) -> None:
        inicio = timezone.now()
        response = self.client.post(
            "/api/pcp/downtimes/",
            {"ativo_pcp": self.ativo.id, "motivo": "Falha API", "inicio": inicio.isoformat()},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        downtime_id = response.data["id"]
        response = self.client.post(
            f"/api/pcp/downtimes/{downtime_id}/fechar/",
            {"fim": (inicio + timedelta(minutes=45)).isoformat()},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["duracao_minutos"], 45)

    def test_api_inicia_e_conclui_execucao_de_manutencao(self) -> None:
        plano = PcpPlanoManutencao.objects.create(
            ativo_pcp=self.ativo,
            nome="Preventiva API",
            intervalo_dias=30,
        )
        programacao = ProgramacaoManutencaoService.gerar_proxima_preventiva(
            plano=plano,
            referencia=date(2026, 6, 3),
        ).programacao
        inicio = timezone.now()

        response = self.client.post(
            "/api/pcp/execucoes-manutencao/",
            {
                "ativo_pcp": self.ativo.id,
                "programacao": programacao.id,
                "tipo": TipoManutencao.PREVENTIVA,
                "data_inicio": inicio.isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        execucao_id = response.data["id"]
        self.ativo.refresh_from_db()
        self.assertEqual(self.ativo.status, StatusAtivo.MANUTENCAO)

        response = self.client.post(
            f"/api/pcp/execucoes-manutencao/{execucao_id}/concluir/",
            {"data_fim": (inicio + timedelta(hours=1)).isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.ativo.refresh_from_db()
        self.assertEqual(self.ativo.status, StatusAtivo.OPERANDO)

    @override_settings(POWER_BI_API_KEY="segredo-power-bi")
    def test_api_power_bi_exige_chave_e_retorna_filial(self) -> None:
        MovimentacaoEstoquePCP.objects.create(
            filial="01",
            produto_codigo="PROD-API",
            data_movimentacao=date(2026, 6, 3),
            tipo_movimentacao=TipoMovimentacao.ENTRADA,
            origem_movimentacao=OrigemMovimentacao.NF_ENTRADA,
            quantidade=10,
        )

        negado = self.client.get("/api/pcp/powerbi/movimentacoes/")
        autorizado = self.client.get(
            "/api/pcp/powerbi/movimentacoes/",
            HTTP_AUTHORIZATION="Api-Key segredo-power-bi",
        )

        self.assertEqual(negado.status_code, 403)
        self.assertEqual(autorizado.status_code, 200)
        self.assertEqual(autorizado.data["results"][0]["filial"], "01")


class PcpDashboardViewTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="pcp_dashboard",
            email="pcp_dashboard@example.com",
            password="senha-forte-123",
        )
        grupo_pcp, _ = Group.objects.get_or_create(name="PCP")
        self.user.groups.add(grupo_pcp)
        self.client.force_login(self.user)

    def test_dashboard_pcp_renderiza_para_usuario_do_grupo_pcp(self) -> None:
        response = self.client.get("/pcp/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pcp/dashboard.html")
        self.assertContains(response, "Dashboard PCP")
