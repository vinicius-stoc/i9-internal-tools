import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, ExpressionWrapper, F, Q, fields
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.decorators import exige_permissao
from .forms import AtendimentoChamadoForm, ChamadoForm, UsuarioForm
from .models import Chamado
from .services import (
    abrir_chamado,
    assumir_chamado,
    atualizar_atendimento,
    recusar_resolucao,
    validar_resolucao,
)


@login_required(login_url='/login/')
def novo_chamado(request):
    if request.method == 'POST':
        form = ChamadoForm(request.POST, request.FILES)
        if form.is_valid():
            abrir_chamado(form=form, solicitante=request.user)
            messages.success(request, 'Chamado aberto com sucesso! A equipe de TI ja foi notificada.')
            return redirect('meus_chamados')
        messages.error(request, 'Erro ao abrir o chamado. Verifique os campos.')
    else:
        form = ChamadoForm()

    return render(request, 'ti/chamado_form.html', {'form': form})


@login_required(login_url='/login/')
@exige_permissao(['ti'])
def ti_admin(request):
    chamados_query = Chamado.objects.select_related('solicitante', 'tecnico').exclude(
        status__in=['CONCLUIDO', 'CANCELADO', 'RESOLVIDO']
    ).order_by('-data_abertura', '-id')

    paginator = Paginator(chamados_query, 25)
    chamados = paginator.get_page(request.GET.get('page'))

    context = {
        'chamados': chamados,
        'total_abertos': chamados_query.count(),
        'meus_atendimentos': chamados_query.filter(tecnico=request.user).count(),
        'aguardando_validacao': Chamado.objects.filter(status='RESOLVIDO').count(),
    }
    return render(request, 'ti/ti_admin.html', context)


@login_required(login_url='/login/')
@exige_permissao(['ti'])
def dashboard_ti(request):
    metricas = Chamado.objects.aggregate(
        total=Count('id', filter=~Q(status='CANCELADO')),
        abertos=Count('id', filter=Q(status__in=['NOVO', 'ATRIBUIDO', 'EM_ANALISE'])),
        andamento=Count('id', filter=Q(status='EM_ATENDIMENTO')),
        concluidos=Count('id', filter=Q(status__in=['RESOLVIDO', 'CONCLUIDO'])),
        terceiros=Count('id', filter=Q(status__in=['AGUARDANDO_TERCEIRO', 'AGUARDANDO_APROVACAO', 'AGUARDANDO_USUARIO'])),
    )

    tempo_medio_resultado = Chamado.objects.filter(
        status__in=['RESOLVIDO', 'CONCLUIDO'],
        data_fechamento__isnull=False,
    ).aggregate(
        media=Avg(ExpressionWrapper(F('data_fechamento') - F('data_abertura'), output_field=fields.DurationField()))
    )['media']

    if tempo_medio_resultado:
        total_seconds = int(tempo_medio_resultado.total_seconds())
        dias = total_seconds // 86400
        horas = (total_seconds % 86400) // 3600
        tempo_medio_str = f"{dias}d {horas}h"
    else:
        tempo_medio_str = "0h"

    filtro = request.GET.get('filtro', '30')
    data_inicio = None
    hoje = timezone.now().date()
    if filtro == '7':
        data_inicio = hoje - timedelta(days=7)
    elif filtro == '30':
        data_inicio = hoje - timedelta(days=30)
    elif filtro == '90':
        data_inicio = hoje - timedelta(days=90)

    abertos_query = Chamado.objects.annotate(dia=TruncDate('data_abertura'))
    fechados_query = Chamado.objects.filter(
        status__in=['RESOLVIDO', 'CONCLUIDO'],
        data_fechamento__isnull=False,
    ).annotate(dia=TruncDate('data_fechamento'))

    if data_inicio:
        abertos_query = abertos_query.filter(data_abertura__date__gte=data_inicio)
        fechados_query = fechados_query.filter(data_fechamento__date__gte=data_inicio)

    abertos_query = abertos_query.values('dia').annotate(total=Count('id')).order_by('dia')
    fechados_query = fechados_query.values('dia').annotate(total=Count('id')).order_by('dia')

    dict_abertos = {item['dia']: item['total'] for item in abertos_query if item['dia']}
    dict_fechados = {item['dia']: item['total'] for item in fechados_query if item['dia']}
    todas_datas = sorted(set(dict_abertos.keys()) | set(dict_fechados.keys()))

    por_setor = Chamado.objects.values('setor').annotate(total=Count('id')).order_by('-total')
    por_categoria = Chamado.objects.values('categoria').annotate(total=Count('id')).order_by('-total')

    context = {
        'total_chamados': metricas['total'],
        'abertos': metricas['abertos'],
        'andamento': metricas['andamento'],
        'concluidos': metricas['concluidos'],
        'terceiros': metricas['terceiros'],
        'tempo_medio': tempo_medio_str,
        'filtro_ativo': filtro,
        'setor_labels': json.dumps([dict(Chamado.SETORES).get(item['setor'], item['setor']) for item in por_setor]),
        'setor_data': json.dumps([item['total'] for item in por_setor]),
        'categoria_labels': json.dumps([dict(Chamado.CATEGORIAS).get(item['categoria'], item['categoria']) for item in por_categoria]),
        'categoria_data': json.dumps([item['total'] for item in por_categoria]),
        'dia_labels': json.dumps([d.strftime('%d/%m') for d in todas_datas]),
        'dia_data_abertos': json.dumps([dict_abertos.get(d, 0) for d in todas_datas]),
        'dia_data_fechados': json.dumps([dict_fechados.get(d, 0) for d in todas_datas]),
    }
    return render(request, 'ti/dashboard.html', context)


@login_required(login_url='/login/')
@exige_permissao(['ti'])
def atender_chamado(request, pk):
    chamado = get_object_or_404(Chamado.objects.select_related('solicitante', 'tecnico'), pk=pk)

    if request.method == 'POST':
        if 'assumir_chamado' in request.POST:
            assumir_chamado(chamado=chamado, tecnico=request.user)
            messages.success(request, f"Voce assumiu o chamado #{chamado.id}!")
            return redirect('atender_chamado', pk=chamado.id)

        form = AtendimentoChamadoForm(request.POST, instance=chamado)
        if form.is_valid():
            atualizar_atendimento(form=form)
            messages.success(request, "Chamado atualizado com sucesso!")
            return redirect('ti_admin')

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"Erro no campo {field}: {error}")
    else:
        form = AtendimentoChamadoForm(instance=chamado)

    return render(request, 'ti/atender_chamado.html', {'chamado': chamado, 'form': form})


@login_required(login_url='/login/')
def meus_chamados(request):
    chamados = Chamado.objects.filter(solicitante=request.user).order_by('-data_abertura')
    return render(request, 'ti/meus_chamados.html', {'chamados': chamados})


@login_required(login_url='/login/')
def detalhe_meu_chamado(request, pk):
    chamado = get_object_or_404(Chamado.objects.select_related('tecnico'), pk=pk, solicitante=request.user)

    if request.method == 'POST':
        if chamado.status == 'RESOLVIDO':
            if 'validar_concluir' in request.POST:
                validar_resolucao(chamado=chamado)
                messages.success(request, 'Chamado validado e encerrado com sucesso. Obrigado!')
                return redirect('meus_chamados')

            if 'recusar_resolucao' in request.POST:
                recusar_resolucao(chamado=chamado)
                messages.warning(request, 'O chamado foi devolvido para a equipe de TI continuar o atendimento.')
                return redirect('meus_chamados')
        else:
            messages.error(request, 'Este chamado nao esta aguardando validacao.')

    return render(request, 'ti/meu_chamado_detalhe.html', {'chamado': chamado})


User = get_user_model()


@login_required(login_url='/login/')
@exige_permissao(['ti'])
def gestao_usuarios(request):
    usuarios = User.objects.all().order_by('-is_active', 'username')
    return render(request, 'ti/gestao_usuarios.html', {'usuarios': usuarios})


@login_required(login_url='/login/')
@exige_permissao(['ti'])
def form_usuario(request, pk=None):
    if pk:
        usuario = get_object_or_404(User, pk=pk)
        titulo = "Editar Usuario"
    else:
        usuario = None
        titulo = "Novo Usuario"

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario, current_user=request.user)
        if form.is_valid():
            if not usuario and not form.cleaned_data.get('password'):
                messages.error(request, "Para novos usuarios, a senha e obrigatoria.")
            else:
                form.save()
                messages.success(request, f"Usuario {'atualizado' if usuario else 'criado'} com sucesso!")
                return redirect('gestao_usuarios')
    else:
        form = UsuarioForm(instance=usuario, current_user=request.user)

    return render(request, 'ti/form_usuario.html', {'form': form, 'titulo': titulo, 'usuario': usuario})
