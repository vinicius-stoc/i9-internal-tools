from rh.services.avaliacoes_desempenho import pode_criar_avaliacao


def permissoes_avaliacao_desempenho(request):
    return {
        'pode_criar_avaliacao_desempenho': pode_criar_avaliacao(
            getattr(request, 'user', None)
        ),
    }
