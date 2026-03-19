from django.urls import path
from . import views

urlpatterns = [
    path('api/rncs/', views.api_listar_rncs, name='api_listar_rncs'),
    path('api/rncs/<int:rnc_id>/atualizar/', views.api_atualizar_rnc, name='api_atualizar_rnc')
]