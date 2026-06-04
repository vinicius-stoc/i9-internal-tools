from __future__ import annotations

from typing import Any

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from core.decorators import group_required
from pcp.selectors import PcpDashboardSelector


@login_required(login_url="/login/")
@group_required(["PCP"])
def dashboard_pcp(request: HttpRequest) -> HttpResponse:
    dias = _parse_periodo(request.GET.get("periodo"))
    context: dict[str, Any] = PcpDashboardSelector.get_context(dias=dias)
    return render(request, "pcp/dashboard.html", context)


def _parse_periodo(periodo: str | None) -> int:
    if periodo in {"7", "30", "90"}:
        return int(periodo)
    return 30
