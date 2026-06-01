from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import group_required

from .forms import (
    AtividadeFormSet,
    AtividadeRDOForm,
    EfetivoFormSet,
    EfetivoRDOForm,
    EquipamentoFormSet,
    EquipamentoRDOForm,
    FotoFormSet,
    FotoRDOForm,
    ObraEquipamentoFormSet,
    ObraFuncaoFormSet,
    ObraForm,
    OcorrenciaFormSet,
    OcorrenciaRDOForm,
    RDOForm,
)
from .models import Obra, RDO
from .services.pdf_service import RDOPDFService
from .services.rdo_service import RDOService


def _rdo_com_relacionamentos():
    return RDO.objects.select_related('obra', 'responsavel').prefetch_related(
        'efetivos__funcao_cadastro',
        'equipamentos__equipamento_cadastro',
        'atividades',
        'ocorrencias',
        'fotos',
    )


@login_required(login_url='/login/')
@group_required(['RDO'])
def obra_list(request):
    obras = Obra.objects.all()
    busca = request.GET.get('busca')
    if busca:
        obras = obras.filter(
            Q(nome__icontains=busca)
            | Q(cliente__icontains=busca)
            | Q(local__icontains=busca)
            | Q(contrato__icontains=busca)
        )
    return render(request, 'rdo/obra_list.html', {'obras': obras, 'busca': busca or ''})


@login_required(login_url='/login/')
@group_required(['RDO'])
def obra_form(request, pk=None):
    obra = get_object_or_404(Obra, pk=pk) if pk else None
    form = ObraForm(request.POST or None, request.FILES or None, instance=obra)
    funcoes_initial = [{'funcao': funcao.pk} for funcao in obra.funcoes.all()] if obra else None
    equipamentos_initial = [{'equipamento': equipamento.pk} for equipamento in obra.equipamentos.all()] if obra else None
    funcao_formset = ObraFuncaoFormSet(request.POST or None, initial=funcoes_initial, prefix='funcoes')
    equipamento_formset = ObraEquipamentoFormSet(
        request.POST or None,
        initial=equipamentos_initial,
        prefix='equipamentos_obra',
    )
    if request.method == 'POST':
        if form.is_valid() and funcao_formset.is_valid() and equipamento_formset.is_valid():
            with transaction.atomic():
                obra_salva = form.save()
                obra_salva.funcoes.set(funcao_formset.selected_funcoes())
                obra_salva.equipamentos.set(equipamento_formset.selected_equipamentos())
            messages.success(request, 'Obra salva com sucesso.')
            return redirect('rdo_obra_editar', pk=obra_salva.pk)
        messages.error(request, 'Revise os campos destacados antes de salvar a obra.')
    return render(
        request,
        'rdo/obra_form.html',
        {'form': form, 'obra': obra, 'funcao_formset': funcao_formset, 'equipamento_formset': equipamento_formset},
    )


@login_required(login_url='/login/')
@group_required(['RDO'])
def rdo_list(request):
    rdos = _rdo_com_relacionamentos().all()
    busca = request.GET.get('busca')
    if busca:
        filtros = (
            Q(obra__nome__icontains=busca)
            | Q(obra__cliente__icontains=busca)
            | Q(responsavel__username__icontains=busca)
        )
        if busca.isdigit():
            filtros |= Q(numero=int(busca))
        rdos = rdos.filter(filtros)
    return render(request, 'rdo/rdo_list.html', {'rdos': rdos, 'busca': busca or ''})


@login_required(login_url='/login/')
@group_required(['RDO'])
def rdo_detail(request, pk):
    rdo = get_object_or_404(_rdo_com_relacionamentos(), pk=pk)
    return render(request, 'rdo/rdo_detail.html', {'rdo': rdo, 'total_efetivo': RDOService.total_efetivo(rdo)})


@login_required(login_url='/login/')
@group_required(['RDO'])
def rdo_form(request, pk=None):
    rdo = get_object_or_404(RDO, pk=pk) if pk else None
    initial = {}
    obra_id = request.GET.get('obra')
    if obra_id and not rdo:
        initial['obra'] = obra_id

    form = RDOForm(request.POST or None, instance=rdo, initial=initial)
    formsets = _build_formsets(request, rdo)

    if request.method == 'POST':
        if form.is_valid() and all(formset.is_valid() for formset in formsets.values()):
            try:
                with transaction.atomic():
                    rdo_salvo = form.save(commit=False)
                    rdo_salvo.responsavel = request.user
                    if not rdo_salvo.numero:
                        rdo_salvo.numero = RDOService.proximo_numero(rdo_salvo.obra)
                    rdo_salvo.save()
                    form.save_m2m()
                    for formset in formsets.values():
                        formset.instance = rdo_salvo
                        formset.save()
                messages.success(request, 'RDO salvo com sucesso.')
                return redirect('rdo_detalhe', pk=rdo_salvo.pk)
            except IntegrityError:
                messages.error(request, 'Ja existe RDO para esta obra com a mesma data ou numero.')
        else:
            messages.error(request, 'Revise os campos destacados antes de salvar o RDO.')

    return render(request, 'rdo/rdo_form.html', {'form': form, 'formsets': formsets, 'rdo': rdo})


def _build_formsets(request, rdo):
    data = request.POST if request.method == 'POST' else None
    files = request.FILES if request.method == 'POST' else None
    obra = None
    obra_id = None
    if rdo:
        obra = rdo.obra
    elif request.method == 'POST':
        obra_id = request.POST.get('obra')
    else:
        obra_id = request.GET.get('obra')
    if obra_id:
        obra = Obra.objects.filter(pk=obra_id).first()
    return {
        'efetivos': EfetivoFormSet(data, instance=rdo, prefix='efetivos', obra=obra),
        'equipamentos': EquipamentoFormSet(data, instance=rdo, prefix='equipamentos', obra=obra),
        'atividades': AtividadeFormSet(data, instance=rdo, prefix='atividades'),
        'ocorrencias': OcorrenciaFormSet(data, instance=rdo, prefix='ocorrencias'),
        'fotos': FotoFormSet(data, files, instance=rdo, prefix='fotos'),
    }


@login_required(login_url='/login/')
@group_required(['RDO'])
def rdo_pdf(request, pk):
    rdo = get_object_or_404(_rdo_com_relacionamentos(), pk=pk)
    return RDOPDFService.gerar_response(rdo, inline=False)


@login_required(login_url='/login/')
@group_required(['RDO'])
def rdo_pdf_preview(request, pk):
    rdo = get_object_or_404(_rdo_com_relacionamentos(), pk=pk)
    return RDOPDFService.gerar_response(rdo, inline=True)


@login_required(login_url='/login/')
@group_required(['RDO'])
def rdo_fotos(request, pk):
    rdo = get_object_or_404(_rdo_com_relacionamentos(), pk=pk)
    form = FotoRDOForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        foto = form.save(commit=False)
        foto.rdo = rdo
        foto.save()
        messages.success(request, 'Foto anexada ao RDO.')
        return redirect('rdo_fotos', pk=rdo.pk)
    return render(request, 'rdo/foto_form.html', {'rdo': rdo, 'form': form})


def _adicionar_item(request, pk, form_class, template_title):
    rdo = get_object_or_404(RDO.objects.select_related('obra'), pk=pk)
    kwargs = {'obra': rdo.obra} if form_class in (EfetivoRDOForm, EquipamentoRDOForm) else {}
    form = form_class(request.POST or None, **kwargs)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.rdo = rdo
        item.save()
        messages.success(request, f'{template_title} salvo com sucesso.')
        return redirect('rdo_detalhe', pk=rdo.pk)
    return render(request, 'rdo/item_form.html', {'rdo': rdo, 'form': form, 'titulo': template_title})


@login_required(login_url='/login/')
@group_required(['RDO'])
def adicionar_efetivo(request, pk):
    return _adicionar_item(request, pk, EfetivoRDOForm, 'Efetivo')


@login_required(login_url='/login/')
@group_required(['RDO'])
def adicionar_equipamento(request, pk):
    return _adicionar_item(request, pk, EquipamentoRDOForm, 'Equipamento')


@login_required(login_url='/login/')
@group_required(['RDO'])
def adicionar_atividade(request, pk):
    return _adicionar_item(request, pk, AtividadeRDOForm, 'Atividade executada')


@login_required(login_url='/login/')
@group_required(['RDO'])
def adicionar_ocorrencia(request, pk):
    return _adicionar_item(request, pk, OcorrenciaRDOForm, 'Ocorrencia')


@login_required(login_url='/login/')
@group_required(['RDO'])
def obra_opcoes_rdo(request, pk):
    obra = get_object_or_404(Obra, pk=pk)
    return JsonResponse({
        'funcoes': list(obra.funcoes.filter(ativo=True).values('id', 'nome')),
        'equipamentos': list(obra.equipamentos.filter(ativo=True).values('id', 'nome')),
    })
