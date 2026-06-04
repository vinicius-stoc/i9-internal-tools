from __future__ import annotations

from datetime import date, timedelta
from hashlib import sha256
from typing import Iterable

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from pcp.models import (
    PcpAlertaEnviado,
    PcpDowntime,
    PcpParametroAlerta,
    PcpProgramacaoManutencao,
    StatusAlerta,
    StatusManutencao,
    TipoAlerta,
)
from pcp.services.downtime import DowntimeService


class AlertaManutencaoService:
    @staticmethod
    def enviar_alertas_preventivas(*, referencia: date | None = None) -> int:
        referencia = referencia or timezone.localdate()
        total_enviados = 0

        for parametro in PcpParametroAlerta.objects.filter(alertar_preventiva=True).iterator(chunk_size=200):
            limite = referencia + timedelta(days=parametro.dias_antecedencia)
            programacoes = AlertaManutencaoService._programacoes_elegiveis(parametro=parametro).filter(
                data_prevista__gte=referencia,
                data_prevista__lte=limite,
                status=StatusManutencao.PLANEJADA,
            )
            destinatarios = AlertaManutencaoService._parse_emails(parametro.emails_destino)
            for programacao in programacoes.iterator(chunk_size=200):
                total_enviados += int(
                    AlertaManutencaoService._enviar_email_preventiva(
                        parametro=parametro,
                        programacao=programacao,
                        destinatarios=destinatarios,
                        data_referencia=referencia,
                    )
                )

        return total_enviados

    @staticmethod
    def enviar_alertas_downtime_aberto() -> int:
        total_enviados = 0
        referencia = timezone.localdate()

        for downtime in DowntimeService.downtimes_abertos().iterator(chunk_size=200):
            parametros = PcpParametroAlerta.objects.filter(alertar_downtime_aberto=True).filter(
                Q(ativo_pcp=downtime.ativo_pcp)
                | Q(area=downtime.ativo_pcp.area)
                | Q(ativo_pcp__isnull=True, area__isnull=True)
            )
            for parametro in parametros.iterator(chunk_size=200):
                total_enviados += int(
                    AlertaManutencaoService._enviar_email_downtime(
                        parametro=parametro,
                        downtime=downtime,
                        destinatarios=AlertaManutencaoService._parse_emails(parametro.emails_destino),
                        data_referencia=referencia,
                    )
                )

        return total_enviados

    @staticmethod
    def _programacoes_elegiveis(parametro: PcpParametroAlerta) -> QuerySet[PcpProgramacaoManutencao]:
        query = PcpProgramacaoManutencao.objects.select_related("plano__ativo_pcp", "plano__ativo_pcp__area")
        if parametro.ativo_pcp_id:
            return query.filter(plano__ativo_pcp=parametro.ativo_pcp)
        if parametro.area_id:
            return query.filter(plano__ativo_pcp__area=parametro.area)
        return query

    @staticmethod
    def _parse_emails(emails_destino: str) -> list[str]:
        normalized = emails_destino.replace(";", ",").replace("\n", ",")
        destinatarios: list[str] = []
        for email in normalized.split(","):
            email = email.strip().lower()
            if not email:
                continue
            try:
                validate_email(email)
            except ValidationError:
                continue
            destinatarios.append(email)
        return sorted(set(destinatarios))

    @staticmethod
    def _enviar_email_preventiva(
        *,
        parametro: PcpParametroAlerta,
        programacao: PcpProgramacaoManutencao,
        destinatarios: Iterable[str],
        data_referencia: date,
    ) -> bool:
        ativo = programacao.plano.ativo_pcp
        assunto = f"[PCP] Preventiva programada - {ativo.codigo}"
        mensagem = (
            "Existe uma manutencao preventiva programada.\n\n"
            f"Ativo: {ativo.codigo} - {ativo.nome}\n"
            f"Plano: {programacao.plano.nome}\n"
            f"Data prevista: {programacao.data_prevista:%d/%m/%Y}\n"
            f"Status: {programacao.get_status_display()}\n"
        )
        return AlertaManutencaoService._enviar_email_idempotente(
            tipo_alerta=TipoAlerta.PREVENTIVA,
            parametro=parametro,
            programacao=programacao,
            downtime=None,
            data_referencia=data_referencia,
            destinatarios=destinatarios,
            assunto=assunto,
            mensagem=mensagem,
        )

    @staticmethod
    def _enviar_email_downtime(
        *,
        parametro: PcpParametroAlerta,
        downtime: PcpDowntime,
        destinatarios: Iterable[str],
        data_referencia: date,
    ) -> bool:
        assunto = f"[PCP] Downtime aberto - {downtime.ativo_pcp.codigo}"
        mensagem = (
            "Existe um downtime aberto no PCP.\n\n"
            f"Ativo: {downtime.ativo_pcp.codigo} - {downtime.ativo_pcp.nome}\n"
            f"Inicio: {timezone.localtime(downtime.inicio):%d/%m/%Y %H:%M}\n"
            f"Motivo: {downtime.motivo}\n"
        )
        return AlertaManutencaoService._enviar_email_idempotente(
            tipo_alerta=TipoAlerta.DOWNTIME_ABERTO,
            parametro=parametro,
            programacao=None,
            downtime=downtime,
            data_referencia=data_referencia,
            destinatarios=destinatarios,
            assunto=assunto,
            mensagem=mensagem,
        )

    @staticmethod
    def _enviar_email_idempotente(
        *,
        tipo_alerta: str,
        parametro: PcpParametroAlerta,
        programacao: PcpProgramacaoManutencao | None,
        downtime: PcpDowntime | None,
        data_referencia: date,
        destinatarios: Iterable[str],
        assunto: str,
        mensagem: str,
    ) -> bool:
        destinatarios_normalizados = sorted(set(destinatarios))
        if not destinatarios_normalizados:
            return False

        chave = AlertaManutencaoService._gerar_chave_idempotencia(
            tipo_alerta=tipo_alerta,
            parametro_id=parametro.id,
            objeto_id=programacao.id if programacao else downtime.id if downtime else None,
            data_referencia=data_referencia,
            destinatarios=destinatarios_normalizados,
        )
        alerta = AlertaManutencaoService._reservar_envio(
            chave=chave,
            tipo_alerta=tipo_alerta,
            parametro=parametro,
            programacao=programacao,
            downtime=downtime,
            data_referencia=data_referencia,
            destinatarios=destinatarios_normalizados,
            assunto=assunto,
        )
        if alerta is None:
            return False

        try:
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=destinatarios_normalizados,
                fail_silently=False,
            )
        except Exception as exc:
            PcpAlertaEnviado.all_objects.filter(pk=alerta.pk).update(
                status=StatusAlerta.FALHA,
                ultimo_erro=str(exc)[:2000],
                updated_at=timezone.now(),
            )
            raise

        PcpAlertaEnviado.all_objects.filter(pk=alerta.pk).update(
            status=StatusAlerta.ENVIADO,
            enviado_em=timezone.now(),
            ultimo_erro="",
            updated_at=timezone.now(),
        )
        return True

    @staticmethod
    def _reservar_envio(
        *,
        chave: str,
        tipo_alerta: str,
        parametro: PcpParametroAlerta,
        programacao: PcpProgramacaoManutencao | None,
        downtime: PcpDowntime | None,
        data_referencia: date,
        destinatarios: list[str],
        assunto: str,
    ) -> PcpAlertaEnviado | None:
        limite_envio_presumido = timezone.now() - timedelta(minutes=30)
        with transaction.atomic():
            alerta, _ = PcpAlertaEnviado.all_objects.get_or_create(
                chave_idempotencia=chave,
                defaults={
                    "tipo_alerta": tipo_alerta,
                    "parametro": parametro,
                    "programacao": programacao,
                    "downtime": downtime,
                    "data_referencia": data_referencia,
                    "destinatarios": ",".join(destinatarios),
                    "assunto": assunto,
                },
            )
            alerta = PcpAlertaEnviado.all_objects.select_for_update().get(pk=alerta.pk)
            if alerta.status == StatusAlerta.ENVIADO:
                return None
            if alerta.status == StatusAlerta.ENVIANDO and alerta.updated_at >= limite_envio_presumido:
                return None

            alerta.ativo = True
            alerta.status = StatusAlerta.ENVIANDO
            alerta.tentativas += 1
            alerta.ultimo_erro = ""
            alerta.save(update_fields=["ativo", "status", "tentativas", "ultimo_erro", "updated_at"])
            return alerta

    @staticmethod
    def _gerar_chave_idempotencia(
        *,
        tipo_alerta: str,
        parametro_id: int | None,
        objeto_id: int | None,
        data_referencia: date,
        destinatarios: Iterable[str],
    ) -> str:
        payload = "|".join(
            [
                tipo_alerta,
                str(parametro_id or ""),
                str(objeto_id or ""),
                data_referencia.isoformat(),
                ",".join(destinatarios),
            ]
        )
        return sha256(payload.encode("utf-8")).hexdigest()
