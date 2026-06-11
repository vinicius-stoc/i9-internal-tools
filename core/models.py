from django.conf import settings
from django.db import models


class SetorOrganizacional(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=120)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = 'Setor Organizacional'
        verbose_name_plural = 'Setores Organizacionais'

    def __str__(self):
        return self.nome


class PerfilOrganizacional(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_organizacional',
    )
    setor = models.ForeignKey(
        SetorOrganizacional,
        on_delete=models.PROTECT,
        related_name='perfis',
    )
    cargo = models.CharField(max_length=150, blank=True, null=True)
    data_admissao = models.DateField(blank=True, null=True)
    pode_ser_avaliado = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)
    gestor_direto = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='liderados_diretos',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil Organizacional'
        verbose_name_plural = 'Perfis Organizacionais'

    def __str__(self):
        nome = self.usuario.get_full_name() or self.usuario.username
        return f'{nome} - {self.setor.nome}'


class GestorSetor(models.Model):
    gestor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='setores_gestor',
    )
    setor = models.ForeignKey(
        SetorOrganizacional,
        on_delete=models.CASCADE,
        related_name='gestores',
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['gestor', 'setor']
        verbose_name = 'Gestor de Setor'
        verbose_name_plural = 'Gestores de Setores'

    def __str__(self):
        nome = self.gestor.get_full_name() or self.gestor.username
        return f'{nome} - {self.setor.nome}'
