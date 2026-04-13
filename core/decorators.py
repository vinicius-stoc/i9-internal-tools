from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def exige_permissao(permissoes_aceitas):
    """Decorador para exige acesso"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            for permissao in permissoes_aceitas:
                if getattr(request.user, permissao, False):
                    return view_func(request, *args, **kwargs)

            messages.error (request, 'Acesso Restrito: Consulte a equipe de TI para liberação')
            return redirect('home')
        return _wrapped_view
    return decorator
