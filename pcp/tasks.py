from __future__ import annotations

import logging

from celery import shared_task

from .services import AlertaManutencaoService, PCPEstoqueETLService, ProgramacaoManutencaoService


logger = logging.getLogger(__name__)


@shared_task(
    name="pcp.run_pcp_estoque_etl",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
    soft_time_limit=3300,
    time_limit=3600,
)
def run_pcp_estoque_etl() -> str:
    """
    Executa a extracao, transformacao e carga das movimentacoes
    de estoque do Protheus (SD1, SD2, SD3) para o Data Mart do PCP.
    """
    logger.info("Iniciando task Celery: pcp.run_pcp_estoque_etl")

    PCPEstoqueETLService.executar()
    logger.info("Task pcp.run_pcp_estoque_etl finalizada com sucesso.")
    return "ETL de estoque PCP concluido com sucesso."


@shared_task(name="pcp.recalcular_preventivas", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def recalcular_preventivas() -> dict[str, int]:
    resultado = ProgramacaoManutencaoService.recalcular_preventivas()
    return {"criadas": resultado.criadas, "existentes": resultado.existentes}


@shared_task(name="pcp.enviar_alertas_preventivas", autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def enviar_alertas_preventivas() -> int:
    return AlertaManutencaoService.enviar_alertas_preventivas()


@shared_task(name="pcp.enviar_alertas_downtime_aberto", autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def enviar_alertas_downtime_aberto() -> int:
    return AlertaManutencaoService.enviar_alertas_downtime_aberto()
