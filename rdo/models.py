from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from PIL import Image, ImageOps


class Obra(models.Model):
    STATUS = [
        ('PLANEJADA', 'Planejada'),
        ('EM_ANDAMENTO', 'Em andamento'),
        ('PARALISADA', 'Paralisada'),
        ('CONCLUIDA', 'Concluida'),
        ('CANCELADA', 'Cancelada'),
    ]

    nome = models.CharField(max_length=150)
    cliente = models.CharField(max_length=150)
    local = models.CharField(max_length=200)
    contrato = models.CharField(max_length=80, blank=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_previsao_fim = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    logo_cliente = models.ImageField(upload_to='rdo/clientes/logos/', blank=True)
    responsavel_i9 = models.CharField(max_length=150, blank=True)
    responsavel_cliente = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='EM_ANDAMENTO')
    funcoes = models.ManyToManyField('Funcao', related_name='obras', blank=True)
    equipamentos = models.ManyToManyField('Equipamento', related_name='obras', blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Obra'
        verbose_name_plural = 'Obras'

    def __str__(self):
        return f'{self.nome} - {self.cliente}'

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.upper()
        super().save(*args, **kwargs)


class Funcao(models.Model):
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Funcao'
        verbose_name_plural = 'Funcoes'
        constraints = [
            models.UniqueConstraint(fields=['nome'], name='funcao_nome_unico'),
        ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.strip()
        super().save(*args, **kwargs)


class Equipamento(models.Model):
    nome = models.CharField(max_length=120)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Equipamento'
        verbose_name_plural = 'Equipamentos'
        constraints = [
            models.UniqueConstraint(fields=['nome'], name='equipamento_nome_unico'),
        ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.strip()
        super().save(*args, **kwargs)


class RDO(models.Model):
    STATUS = [
        ('RASCUNHO', 'Rascunho'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]

    CONDICOES_CLIMATICAS = [
        ('NAO_SE_APLICA', 'Nao se aplica'),
        ('ENSOLARADO', 'Ensolarado'),
        ('NUBLADO', 'Nublado'),
        ('CHUVOSO', 'Chuvoso'),
        ('VENTO_FORTE', 'Vento forte'),
        ('PARCIALMENTE_NUBLADO', 'Parcialmente nublado'),
    ]

    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name='rdos')
    numero = models.PositiveIntegerField()
    data = models.DateField()
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='rdos_responsavel',
    )
    condicao_climatica = models.CharField(max_length=30, choices=CONDICOES_CLIMATICAS, blank=True)
    condicao_manha = models.CharField(max_length=30, choices=CONDICOES_CLIMATICAS, default='NAO_SE_APLICA')
    condicao_tarde = models.CharField(max_length=30, choices=CONDICOES_CLIMATICAS, default='NAO_SE_APLICA')
    condicao_noite = models.CharField(max_length=30, choices=CONDICOES_CLIMATICAS, default='NAO_SE_APLICA')
    status = models.CharField(max_length=20, choices=STATUS, default='RASCUNHO')
    observacoes_gerais = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data', '-numero']
        verbose_name = 'RDO'
        verbose_name_plural = 'RDOs'
        constraints = [
            models.UniqueConstraint(fields=['obra', 'numero'], name='rdo_obra_numero_unico'),
            models.UniqueConstraint(fields=['obra', 'data'], name='rdo_obra_data_unica'),
        ]

    def __str__(self):
        return f'RDO {self.numero} - {self.obra.nome} - {self.data:%d/%m/%Y}'


class EfetivoRDO(models.Model):
    rdo = models.ForeignKey(RDO, on_delete=models.CASCADE, related_name='efetivos')
    funcao_cadastro = models.ForeignKey(
        Funcao,
        on_delete=models.PROTECT,
        related_name='efetivos_rdo',
        null=True,
        blank=True,
    )
    funcao = models.CharField(max_length=100, blank=True)
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    horario_entrada = models.TimeField(null=True, blank=True)
    horas_trabalhadas = models.DurationField(null=True, blank=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['funcao']
        verbose_name = 'Efetivo do RDO'
        verbose_name_plural = 'Efetivos dos RDOs'

    def __str__(self):
        return f'{self.nome_funcao}: {self.quantidade} pessoa(s)'

    @property
    def nome_funcao(self):
        return self.funcao_cadastro.nome if self.funcao_cadastro_id else self.funcao

    @property
    def horas_trabalhadas_formatadas(self):
        return _format_duration(self.horas_trabalhadas)

    def save(self, *args, **kwargs):
        if self.funcao_cadastro_id:
            self.funcao = self.funcao_cadastro.nome
        super().save(*args, **kwargs)


class EquipamentoRDO(models.Model):
    STATUS = [
        ('OPERANDO', 'Operando'),
        ('PARADO', 'Parado'),
        ('MANUTENCAO', 'Em manutencao'),
    ]

    rdo = models.ForeignKey(RDO, on_delete=models.CASCADE, related_name='equipamentos')
    equipamento_cadastro = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name='equipamentos_rdo',
        null=True,
        blank=True,
    )
    equipamento = models.CharField(max_length=120, blank=True)
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    horas_utilizadas = models.DurationField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='OPERANDO')
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['equipamento']
        verbose_name = 'Equipamento do RDO'
        verbose_name_plural = 'Equipamentos dos RDOs'

    def __str__(self):
        return f'{self.nome_equipamento}: {self.quantidade} unidade(s)'

    @property
    def nome_equipamento(self):
        return self.equipamento_cadastro.nome if self.equipamento_cadastro_id else self.equipamento

    @property
    def horas_utilizadas_formatadas(self):
        return _format_duration(self.horas_utilizadas)

    def save(self, *args, **kwargs):
        if self.equipamento_cadastro_id:
            self.equipamento = self.equipamento_cadastro.nome
        super().save(*args, **kwargs)


class AtividadeRDO(models.Model):
    rdo = models.ForeignKey(RDO, on_delete=models.CASCADE, related_name='atividades')
    descricao = models.TextField()
    local_execucao = models.CharField(max_length=150, blank=True)
    percentual_avanco = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Atividade do RDO'
        verbose_name_plural = 'Atividades dos RDOs'

    def __str__(self):
        return f'{self.descricao[:60]}'


class OcorrenciaRDO(models.Model):
    TIPOS = [
        ('SEGURANCA', 'Seguranca'),
        ('QUALIDADE', 'Qualidade'),
        ('CLIMA', 'Clima'),
        ('SUPRIMENTOS', 'Suprimentos'),
        ('EQUIPAMENTO', 'Equipamento'),
        ('OUTROS', 'Outros'),
    ]

    rdo = models.ForeignKey(RDO, on_delete=models.CASCADE, related_name='ocorrencias')
    tipo = models.CharField(max_length=30, choices=TIPOS)
    descricao = models.TextField()
    impacto = models.TextField(blank=True)
    providencia = models.TextField(blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Ocorrencia do RDO'
        verbose_name_plural = 'Ocorrencias dos RDOs'

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.descricao[:50]}'


class FotoRDO(models.Model):
    PDF_MAX_SIZE = (1200, 1200)
    PDF_JPEG_QUALITY = 78

    rdo = models.ForeignKey(RDO, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='rdo/fotos/%Y/%m/')
    imagem_pdf = models.ImageField(upload_to='rdo/fotos_pdf/%Y/%m/', blank=True)
    legenda = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']
        verbose_name = 'Foto do RDO'
        verbose_name_plural = 'Fotos dos RDOs'

    def __str__(self):
        return self.legenda or f'Foto RDO {self.rdo.numero}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.imagem and not self.imagem_pdf:
            self.gerar_imagem_pdf(save=True)

    def gerar_imagem_pdf(self, save=False):
        if not self.imagem:
            return

        self.imagem.open('rb')
        with Image.open(self.imagem) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail(self.PDF_MAX_SIZE, Image.Resampling.LANCZOS)

            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            elif image.mode == 'L':
                image = image.convert('RGB')

            output = BytesIO()
            image.save(
                output,
                format='JPEG',
                quality=self.PDF_JPEG_QUALITY,
                optimize=True,
                progressive=True,
            )

        original_name = Path(self.imagem.name).stem or f'foto_rdo_{self.pk}'
        optimized_name = f'{original_name}_pdf.jpg'
        self.imagem_pdf.save(optimized_name, ContentFile(output.getvalue()), save=False)

        if save:
            super().save(update_fields=['imagem_pdf'])


def _format_duration(value):
    if not value:
        return '-'
    total_seconds = int(value.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f'{hours:02d}:{minutes:02d}'
