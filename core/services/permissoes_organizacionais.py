from django.contrib.auth import get_user_model

from core.models import PerfilOrganizacional, SetorOrganizacional


GRUPOS_ACESSO_GLOBAL = {'RH', 'TI', 'Diretoria'}


def usuario_tem_acesso_global(user):
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    grupos = set(user.groups.values_list('name', flat=True))
    return bool(grupos.intersection(GRUPOS_ACESSO_GLOBAL))


def usuario_eh_gestor(user):
    if not user or not user.is_authenticated:
        return False

    return user.setores_gestor.filter(ativo=True).exists()


def setores_gerenciados_por(user):
    if not user or not user.is_authenticated:
        return SetorOrganizacional.objects.none()

    return SetorOrganizacional.objects.filter(
        gestores__gestor=user,
        gestores__ativo=True,
        ativo=True,
    ).distinct()


def usuario_pode_ver_usuario(user, usuario_alvo):
    if not user or not user.is_authenticated or not usuario_alvo:
        return False

    if usuario_tem_acesso_global(user):
        return True

    if user == usuario_alvo:
        return True

    setores = setores_gerenciados_por(user)
    return PerfilOrganizacional.objects.filter(
        usuario=usuario_alvo,
        setor__in=setores,
        ativo=True,
    ).exists()


def usuarios_visiveis_para(user):
    User = get_user_model()

    if not user or not user.is_authenticated:
        return User.objects.none()

    base = User.objects.filter(is_active=True, perfil_organizacional__ativo=True)

    if usuario_tem_acesso_global(user):
        return base.distinct().order_by('first_name', 'last_name', 'username')

    setores = setores_gerenciados_por(user)
    if setores.exists():
        return base.filter(perfil_organizacional__setor__in=setores).distinct().order_by(
            'first_name',
            'last_name',
            'username',
        )

    return base.filter(pk=user.pk).distinct()


def usuarios_avaliaveis_para(user):
    User = get_user_model()

    if not user or not user.is_authenticated:
        return User.objects.none()

    base = User.objects.filter(
        is_active=True,
        perfil_organizacional__ativo=True,
        perfil_organizacional__pode_ser_avaliado=True,
    ).exclude(
        setores_gestor__ativo=True,
    ).select_related(
        'perfil_organizacional',
        'perfil_organizacional__setor',
    )

    if usuario_tem_acesso_global(user):
        return base.exclude(pk=user.pk).distinct().order_by('first_name', 'last_name', 'username')

    if usuario_eh_gestor(user):
        return base.filter(
            perfil_organizacional__setor__in=setores_gerenciados_por(user),
        ).exclude(
            pk=user.pk,
        ).distinct().order_by('first_name', 'last_name', 'username')

    return User.objects.none()
