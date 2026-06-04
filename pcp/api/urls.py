from __future__ import annotations

from django.urls import path

from .views import (
    AreaProducaoAPIView,
    AtivoAPIView,
    DowntimeAPIView,
    DowntimeCloseAPIView,
    ExecucaoManutencaoAPIView,
    ExecucaoManutencaoCloseAPIView,
    MovimentacaoEstoqueAPIView,
    PlanoManutencaoAPIView,
    ProgramacaoManutencaoAPIView,
    RecalcularPreventivasAPIView,
)


app_name = "pcp_api"

urlpatterns = [
    path("powerbi/movimentacoes/", MovimentacaoEstoqueAPIView.as_view(), name="movimentacoes-powerbi"),
    path("areas/", AreaProducaoAPIView.as_view(), name="areas"),
    path("ativos/", AtivoAPIView.as_view(), name="ativos"),
    path("planos-manutencao/", PlanoManutencaoAPIView.as_view(), name="planos-manutencao"),
    path("programacoes-manutencao/", ProgramacaoManutencaoAPIView.as_view(), name="programacoes-manutencao"),
    path("programacoes-manutencao/recalcular/", RecalcularPreventivasAPIView.as_view(), name="recalcular-preventivas"),
    path("downtimes/", DowntimeAPIView.as_view(), name="downtimes"),
    path("downtimes/<int:downtime_id>/fechar/", DowntimeCloseAPIView.as_view(), name="fechar-downtime"),
    path("execucoes-manutencao/", ExecucaoManutencaoAPIView.as_view(), name="execucoes-manutencao"),
    path(
        "execucoes-manutencao/<int:execucao_id>/concluir/",
        ExecucaoManutencaoCloseAPIView.as_view(),
        name="concluir-execucao-manutencao",
    ),
]
