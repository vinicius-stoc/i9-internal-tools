from django.contrib import admin
from .models import Chamado, ChamadoImagem


class ChamadoImagemInline(admin.TabularInline):
    model = ChamadoImagem
    extra = 0


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'solicitante', 'tecnico', 'prioridade', 'status', 'data_abertura', 'data_fechamento')
    list_filter = ('status', 'prioridade', 'categoria', 'setor')
    search_fields = ('id', 'titulo', 'descricao', 'solicitante__username', 'solicitante__email')
    date_hierarchy = 'data_abertura'
    inlines = [ChamadoImagemInline]


@admin.register(ChamadoImagem)
class ChamadoImagemAdmin(admin.ModelAdmin):
    list_display = ('id', 'chamado', 'imagem')
    search_fields = ('chamado__id', 'chamado__titulo')
