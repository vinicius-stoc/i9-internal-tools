from __future__ import annotations

from django.db import IntegrityError, transaction

from pcp.models import (
    CriticidadeAtivo,
    PcpAreaProducao,
    PcpAtivo,
    PcpDowntime,
    PcpExecucaoManutencao,
    StatusAtivo,
)
from pcp.services.exceptions import PcpConflictError, PcpValidationError


class AtivoService:
    @staticmethod
    def criar_area(*, codigo: str, nome: str, descricao: str = "") -> PcpAreaProducao:
        codigo_normalizado = codigo.strip().upper()
        nome_normalizado = nome.strip()
        if not codigo_normalizado or not nome_normalizado:
            raise PcpValidationError("Codigo e nome da area sao obrigatorios.")

        try:
            with transaction.atomic():
                return PcpAreaProducao.objects.create(
                    codigo=codigo_normalizado,
                    nome=nome_normalizado,
                    descricao=descricao.strip(),
                )
        except IntegrityError as exc:
            raise PcpConflictError("Ja existe uma area com este codigo.") from exc

    @staticmethod
    def criar_ativo(
        *,
        codigo: str,
        nome: str,
        area: PcpAreaProducao,
        descricao: str = "",
        fabricante: str = "",
        modelo: str = "",
        numero_serie: str = "",
        status: str = StatusAtivo.OPERANDO,
        criticidade: str = CriticidadeAtivo.MEDIA,
    ) -> PcpAtivo:
        codigo_normalizado = codigo.strip().upper()
        nome_normalizado = nome.strip()
        if not codigo_normalizado or not nome_normalizado:
            raise PcpValidationError("Codigo e nome do ativo sao obrigatorios.")
        try:
            with transaction.atomic():
                area = PcpAreaProducao.objects.select_for_update().get(pk=area.pk)
                return PcpAtivo.objects.create(
                    codigo=codigo_normalizado,
                    nome=nome_normalizado,
                    area=area,
                    descricao=descricao.strip(),
                    fabricante=fabricante.strip(),
                    modelo=modelo.strip(),
                    numero_serie=numero_serie.strip(),
                    status=status,
                    criticidade=criticidade,
                )
        except PcpAreaProducao.DoesNotExist as exc:
            raise PcpValidationError("Nao e permitido vincular um ativo a uma area inativa.") from exc
        except IntegrityError as exc:
            raise PcpConflictError("Ja existe um ativo com este codigo.") from exc

    @staticmethod
    def desativar_ativo(*, ativo: PcpAtivo) -> PcpAtivo:
        with transaction.atomic():
            ativo = PcpAtivo.objects.select_for_update().get(pk=ativo.pk)
            possui_operacao_aberta = PcpDowntime.objects.filter(ativo_pcp=ativo, fim__isnull=True).exists() or (
                PcpExecucaoManutencao.objects.filter(ativo_pcp=ativo, data_fim__isnull=True).exists()
            )
            if possui_operacao_aberta:
                raise PcpConflictError("Ativo possui downtime ou manutencao aberta.")
            ativo.status = StatusAtivo.INATIVO
            ativo.ativo = False
            ativo.save(update_fields=["status", "ativo", "updated_at"])
        return ativo
