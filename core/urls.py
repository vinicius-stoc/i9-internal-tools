from django.urls import path
from . import views

urlpatterns = [
    path('task-status/<str:task_id>/', views.checar_status_task_global, name='checar_status_task_global'),
]