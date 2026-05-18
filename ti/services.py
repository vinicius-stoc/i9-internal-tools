from django.db import transaction

from .models import ChamadoImagem
from .tasks import task_notificar_chamado


def abrir_chamado(*, form, solicitante):
    arquivos = form.cleaned_data.get('imagens') or []
    if not isinstance(arquivos, (list, tuple)):
        arquivos = [arquivos]

    with transaction.atomic():
        chamado = form.save(commit=False)
        chamado.solicitante = solicitante
        chamado.full_clean()
        chamado.save()

        for arquivo in arquivos:
            ChamadoImagem.objects.create(chamado=chamado, imagem=arquivo)

        _agendar_notificacao(chamado.id, 'ABERTURA', countdown=5)

    return chamado


def assumir_chamado(*, chamado, tecnico):
    status_anterior = chamado.status
    chamado.tecnico = tecnico
    if chamado.status in ['NOVO', 'ATRIBUIDO']:
        chamado.status = 'EM_ATENDIMENTO'

    chamado.full_clean()
    chamado.save()
    _notificar_se_status_mudou(chamado.id, status_anterior, chamado.status)
    return chamado


def atualizar_atendimento(*, form):
    chamado = form.instance
    status_anterior = chamado.status
    chamado = form.save(commit=False)
    chamado.full_clean()
    chamado.save()
    _notificar_se_status_mudou(chamado.id, status_anterior, chamado.status)
    return chamado


def validar_resolucao(*, chamado):
    status_anterior = chamado.status
    chamado.validado_pelo_solicitante = True
    chamado.status = 'CONCLUIDO'
    chamado.full_clean()
    chamado.save()
    _notificar_se_status_mudou(chamado.id, status_anterior, chamado.status)
    return chamado


def recusar_resolucao(*, chamado):
    status_anterior = chamado.status
    chamado.status = 'EM_ATENDIMENTO'
    chamado.full_clean()
    chamado.save()
    _notificar_se_status_mudou(chamado.id, status_anterior, chamado.status)
    return chamado


def _notificar_se_status_mudou(chamado_id, status_anterior, status_atual):
    if status_anterior == status_atual:
        return

    tipo = 'CONCLUSAO' if status_atual == 'CONCLUIDO' else status_atual
    _agendar_notificacao(chamado_id, tipo)


def _agendar_notificacao(chamado_id, tipo, countdown=None):
    def enqueue():
        if countdown:
            task_notificar_chamado.apply_async(args=[chamado_id, tipo], countdown=countdown)
        else:
            task_notificar_chamado.delay(chamado_id, tipo)

    transaction.on_commit(enqueue)
