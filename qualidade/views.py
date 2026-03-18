from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import RNC

@login_required(login_url='/login/')
def dashboard_qualidade(request):
    """Renderiza a página principal do dashboard da qualidade."""
    return render(request, 'qualidade/dashboard.html')


@login_required(login_url='/login/')
def api_listar_rncs(request):
    """
    Fornece os dados de todas as RNCs em formato JSON para alimentar a tabela Tabulator.
    Esta versão é otimizada para evitar o problema N+1 queries.
    """
    # Otimização de consulta para carregar todos os dados relacionados de uma vez
    rncs_qs = RNC.objects.select_related(
        'registrador', 'local', 'equipamento', 'tipo_nc'
    ).prefetch_related(
        'responsaveis', 'imagens'
    ).all().order_by('-id')

    data = []
    for rnc in rncs_qs:
        # Constrói a lista de nomes de responsáveis
        responsaveis_nomes = ", ".join([user.get_full_name() or user.username for user in rnc.responsaveis.all()])
        
        # Pega a URL da primeira imagem, se existir
        primeira_imagem = rnc.imagens.first()
        primeira_imagem_url = primeira_imagem.imagem.url if primeira_imagem else None

        data.append({
            "id": rnc.id,
            "status": rnc.get_status_display(),
            "registrador": rnc.registrador.get_full_name() or rnc.registrador.username,
            "detector": rnc.get_detector_display(),
            "data_abertura": rnc.data_abertura.strftime('%d/%m/%Y') if rnc.data_abertura else None,
            "projeto_cod": rnc.projeto_cod,
            "elemento_rastreador": rnc.elemento_rastreador,
            "local": rnc.local.nome if rnc.local else None,
            "equipamento": rnc.equipamento.nome if rnc.equipamento else None,
            "classificacao": rnc.get_classificacao_display(),
            "criticidade": rnc.get_criticidade_display(),
            "justificativa_criticidade": rnc.justificativa_criticidade,
            "tipo_nc": rnc.tipo_nc.nome if rnc.tipo_nc else None,
            "descricao": rnc.descricao,
            "correcao": rnc.correcao,
            "causas_principais": rnc.causas_principais,
            "acao_corretiva": rnc.acao_corretiva,
            "eficacia_texto": rnc.eficacia_texto,
            "responsaveis": responsaveis_nomes,
            "data_prevista_conclusao": rnc.data_prevista_conclusao.strftime('%Y-%m-%d') if rnc.data_prevista_conclusao else None,
            "data_encerramento": rnc.data_encerramento.strftime('%Y-%m-%d') if rnc.data_encerramento else None,
            "ishikawa_link": rnc.ishikawa_link,
            "eficacia_pdf": rnc.eficacia_pdf.url if rnc.eficacia_pdf else None,
            "qtd_imagens": rnc.imagens.count(),
            "primeira_imagem_url": primeira_imagem_url
        })

    return JsonResponse(data, safe=False)
