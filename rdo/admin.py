from django.contrib import admin

from .models import (
    AtividadeRDO,
    EfetivoRDO,
    Equipamento,
    EquipamentoRDO,
    FotoRDO,
    Funcao,
    Obra,
    OcorrenciaRDO,
    RDO,
)


class EfetivoRDOInline(admin.TabularInline):
    model = EfetivoRDO
    extra = 0


class EquipamentoRDOInline(admin.TabularInline):
    model = EquipamentoRDO
    extra = 0


class AtividadeRDOInline(admin.TabularInline):
    model = AtividadeRDO
    extra = 0


class OcorrenciaRDOInline(admin.TabularInline):
    model = OcorrenciaRDO
    extra = 0


class FotoRDOInline(admin.TabularInline):
    model = FotoRDO
    extra = 0


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente', 'local', 'status', 'data_inicio', 'data_previsao_fim', 'data_fim')
    list_filter = ('status',)
    search_fields = ('nome', 'cliente', 'local', 'contrato')
    filter_horizontal = ('funcoes', 'equipamentos')


@admin.register(RDO)
class RDOAdmin(admin.ModelAdmin):
    list_display = ('numero', 'obra', 'data', 'responsavel', 'status', 'condicao_manha', 'condicao_tarde', 'condicao_noite')
    list_filter = ('status', 'condicao_manha', 'condicao_tarde', 'condicao_noite', 'obra')
    search_fields = ('obra__nome', 'obra__cliente', 'numero', 'responsavel__username')
    date_hierarchy = 'data'
    inlines = [EfetivoRDOInline, EquipamentoRDOInline, AtividadeRDOInline, OcorrenciaRDOInline, FotoRDOInline]


@admin.register(EfetivoRDO)
class EfetivoRDOAdmin(admin.ModelAdmin):
    list_display = ('rdo', 'funcao_cadastro', 'funcao', 'quantidade', 'horario_entrada', 'horas_trabalhadas')
    search_fields = ('funcao', 'funcao_cadastro__nome', 'rdo__obra__nome')


@admin.register(EquipamentoRDO)
class EquipamentoRDOAdmin(admin.ModelAdmin):
    list_display = ('rdo', 'equipamento_cadastro', 'equipamento', 'quantidade', 'horas_utilizadas', 'status')
    list_filter = ('status',)
    search_fields = ('equipamento', 'equipamento_cadastro__nome', 'rdo__obra__nome')


@admin.register(AtividadeRDO)
class AtividadeRDOAdmin(admin.ModelAdmin):
    list_display = ('rdo', 'local_execucao', 'percentual_avanco')
    search_fields = ('descricao', 'local_execucao', 'rdo__obra__nome')


@admin.register(OcorrenciaRDO)
class OcorrenciaRDOAdmin(admin.ModelAdmin):
    list_display = ('rdo', 'tipo')
    list_filter = ('tipo',)
    search_fields = ('descricao', 'impacto', 'providencia', 'rdo__obra__nome')


@admin.register(FotoRDO)
class FotoRDOAdmin(admin.ModelAdmin):
    list_display = ('rdo', 'legenda', 'criado_em', 'imagem_pdf')
    search_fields = ('legenda', 'rdo__obra__nome')


@admin.register(Funcao)
class FuncaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'criado_em')
    list_filter = ('ativo',)
    search_fields = ('nome',)


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'criado_em')
    list_filter = ('ativo',)
    search_fields = ('nome',)
