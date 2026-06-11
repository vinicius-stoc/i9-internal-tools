from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def preencher_snapshots(apps, schema_editor):
    AvaliacaoDesempenho = apps.get_model('rh', 'AvaliacaoDesempenho')
    PerfilOrganizacional = apps.get_model('core', 'PerfilOrganizacional')

    for avaliacao in AvaliacaoDesempenho.objects.select_related('avaliado').all():
        avaliado = avaliacao.avaliado
        nome = f'{getattr(avaliado, "first_name", "")} {getattr(avaliado, "last_name", "")}'.strip()
        avaliacao.nome_avaliado = nome or getattr(avaliado, 'username', '') or f'Usuario #{avaliado.pk}'

        perfil = PerfilOrganizacional.objects.filter(usuario_id=avaliado.pk).select_related('setor').first()
        if perfil:
            avaliacao.cargo_avaliado = perfil.cargo
            avaliacao.setor_avaliado = perfil.setor.nome if perfil.setor_id else ''
            avaliacao.data_admissao_avaliado = perfil.data_admissao

        avaliacao.save(update_fields=[
            'nome_avaliado',
            'cargo_avaliado',
            'setor_avaliado',
            'data_admissao_avaliado',
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_estrutura_organizacional'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rh', '0019_alter_avaliacaodesempenho_funcionario'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='avaliacaodesempenho',
            unique_together=set(),
        ),
        migrations.RenameField(
            model_name='avaliacaodesempenho',
            old_name='funcionario',
            new_name='avaliado',
        ),
        migrations.AlterField(
            model_name='avaliacaodesempenho',
            name='avaliado',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='avaliacoes_recebidas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='avaliacaodesempenho',
            name='avaliada_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='avaliacoes_realizadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='nome_avaliado',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='cargo_avaliado',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='setor_avaliado',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='data_admissao_avaliado',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='ciencia_gestor',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='data_ciencia_gestor',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='usuario_ciencia_gestor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ciencias_gestor_desempenho', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='ciencia_colaborador',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='data_ciencia_colaborador',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='usuario_ciencia_colaborador',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ciencias_colaborador_desempenho', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='avaliacaodesempenho',
            name='atualizado_em',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='avaliacaodesempenho',
            name='status',
            field=models.CharField(choices=[('RASCUNHO', 'Rascunho'), ('FINALIZADA', 'Finalizada'), ('CIENCIA_PENDENTE', 'Ciencia Pendente'), ('CIENCIA_PARCIAL', 'Ciencia Parcial'), ('CIENCIA_CONCLUIDA', 'Ciencia Concluida'), ('CANCELADA', 'Cancelada')], default='RASCUNHO', max_length=30),
        ),
        migrations.RunPython(preencher_snapshots, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='avaliacaodesempenho',
            name='nome_avaliado',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='avaliacaodesempenho',
            unique_together={('avaliado', 'ano', 'ciclo')},
        ),
        migrations.AlterModelOptions(
            name='avaliacaodesempenho',
            options={'ordering': ['-ano', '-ciclo', '-data_avaliacao'], 'verbose_name': 'Avaliacao de desempenho', 'verbose_name_plural': 'Avaliacoes de desempenho'},
        ),
    ]
