from django.shortcuts import render
from celery.result import AsyncResult
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login/')
def home(request):
    return render(request, 'home.html')


@login_required(login_url='/login/')
def checar_status_task_global(request, task_id):
    """
    View global e genérica para consultar o status de QUALQUER
    task do Celery rodando em background no sistema.
    """
    task_result = AsyncResult(task_id)
    return JsonResponse({
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    })