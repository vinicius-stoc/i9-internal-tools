from django.db import models

class CompraDashboard(models.Model):
    """Table consolidada alimentada pelo ETL PROTHEUS (SC1, SC7, AFG, SD1"""
    STATUS_CHOICES = (
        ('PENDENTE', 'Pendente'),
        ('COM PEDIDO', 'Com Pedido'),
        ('ENTREGUE', 'Entrega'),
    )

    filial = models.CharField(max_length=20, verbose_name="Filial")
    num_sc = models.CharField(max_length=20, verbose_name="Número SC")
    emissao_sc = models.DateField(null=True, blank=True, verbose_name="Emissão SC")

    cod_produto = models.CharField(max_length=50, verbose_name="Cód. Produto")
    descricao_produto = models.CharField(max_length=255, verbose_name="Descrição")
    qtd_solicitada = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    projeto_cod = models.CharField(max_length=50, blank=True, null=True, verbose_name="Projeto (AFG)")

    num_pedido = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número Pedido")
    emissao_pedido = models.DateField(null=True, blank=True, verbose_name="Emissão Pedido")
    data_prev_recebimento = models.DateField(null=True, blank=True, verbose_name="Prev. Recebimento")
    data_recebimento_real = models.DateField(null=True, blank=True, verbose_name="Recebimento Real")

    cod_fornecedor = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cód. Fornecedor")
    nome_fornecedor = models.CharField(max_length=150, blank=True, null=True, verbose_name="Fornecedor")

    qtd_pedido = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    qtd_recebida = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    valor_total = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')

    # KPIs Calculados no ETL
    lead_time_compras = models.IntegerField(default=0, verbose_name="Lead Time Compras (Dias)")
    lead_time_fornecedor = models.IntegerField(default=0, verbose_name="Lead Time Fornecedor (Dias)")
    dias_atraso_entrega = models.IntegerField(default=0, verbose_name="Dias de Atraso")

    # Controle Interno
    data_atualizacao = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "Dado Consolidado de Compra"
        verbose_name_plural = "Dados Consolidados de Compras"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['emissao_sc']),
            models.Index(fields=['projeto_cod']),
            models.Index(fields=['cod_fornecedor']),
        ]

    def __str__(self):
        return f'SC {self.num_sc} - Pedido {self.num_pedido or "N/A}"}'