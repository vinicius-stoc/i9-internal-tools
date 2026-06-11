from django.contrib import admin

from .models import GestorSetor, PerfilOrganizacional, SetorOrganizacional


@admin.register(SetorOrganizacional)
class SetorOrganizacionalAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'ativo', 'ordem')
    list_filter = ('ativo',)
    search_fields = ('codigo', 'nome')
    ordering = ('ordem', 'nome')


@admin.register(PerfilOrganizacional)
class PerfilOrganizacionalAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'setor', 'cargo', 'pode_ser_avaliado', 'ativo', 'gestor_direto')
    list_filter = ('setor', 'ativo', 'pode_ser_avaliado')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'cargo')
    autocomplete_fields = ('usuario', 'gestor_direto')


@admin.register(GestorSetor)
class GestorSetorAdmin(admin.ModelAdmin):
    list_display = ('gestor', 'setor', 'ativo')
    list_filter = ('setor', 'ativo')
    search_fields = ('gestor__username', 'gestor__first_name', 'gestor__last_name', 'setor__nome')
    autocomplete_fields = ('gestor',)
