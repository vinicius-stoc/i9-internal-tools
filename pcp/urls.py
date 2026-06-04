from __future__ import annotations

from django.urls import path

from . import views


urlpatterns = [
    path("dashboard/", views.dashboard_pcp, name="dashboard_pcp"),
]
