from django.urls import path

from . import views


urlpatterns = [
    path('', views.rdo_list, name='rdo_list'),
    path('novo/', views.rdo_form, name='rdo_novo'),
    path('<int:pk>/', views.rdo_detail, name='rdo_detalhe'),
    path('<int:pk>/editar/', views.rdo_form, name='rdo_editar'),
    path('<int:pk>/pdf/', views.rdo_pdf, name='rdo_pdf'),
    path('<int:pk>/pdf/preview/', views.rdo_pdf_preview, name='rdo_pdf_preview'),
    path('<int:pk>/fotos/', views.rdo_fotos, name='rdo_fotos'),
    path('<int:pk>/efetivo/novo/', views.adicionar_efetivo, name='rdo_adicionar_efetivo'),
    path('<int:pk>/equipamento/novo/', views.adicionar_equipamento, name='rdo_adicionar_equipamento'),
    path('<int:pk>/atividade/nova/', views.adicionar_atividade, name='rdo_adicionar_atividade'),
    path('<int:pk>/ocorrencia/nova/', views.adicionar_ocorrencia, name='rdo_adicionar_ocorrencia'),
    path('obras/', views.obra_list, name='rdo_obras'),
    path('obras/nova/', views.obra_form, name='rdo_obra_nova'),
    path('obras/<int:pk>/opcoes-rdo/', views.obra_opcoes_rdo, name='rdo_obra_opcoes'),
    path('obras/<int:pk>/editar/', views.obra_form, name='rdo_obra_editar'),
]
