from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


SETORES_INICIAIS = [
    {'codigo': 'CA', 'nome': 'Comercial', 'ordem': 1},
    {'codigo': 'CO', 'nome': 'Compras', 'ordem': 2},
    {'codigo': 'DI', 'nome': 'Diretoria', 'ordem': 3},
    {'codigo': 'FI', 'nome': 'Financeiro', 'ordem': 4},
    {'codigo': 'OB', 'nome': 'Obra', 'ordem': 5},
    {'codigo': 'QA', 'nome': 'SGQ', 'ordem': 6},
    {'codigo': 'FA', 'nome': 'Fabrica', 'ordem': 7},
    {'codigo': 'PR', 'nome': 'Projetos', 'ordem': 8},
    {'codigo': 'EG', 'nome': 'Engenharia', 'ordem': 9},
    {'codigo': 'RH', 'nome': 'Recursos Humanos', 'ordem': 10},
    {'codigo': 'TI', 'nome': 'T.I', 'ordem': 11},
]


def criar_setores_iniciais(apps, schema_editor):
    SetorOrganizacional = apps.get_model('core', 'SetorOrganizacional')
    for setor in SETORES_INICIAIS:
        SetorOrganizacional.objects.update_or_create(
            codigo=setor['codigo'],
            defaults={
                'nome': setor['nome'],
                'ordem': setor['ordem'],
                'ativo': True,
            },
        )


def remover_setores_iniciais(apps, schema_editor):
    SetorOrganizacional = apps.get_model('core', 'SetorOrganizacional')
    SetorOrganizacional.objects.filter(
        codigo__in=[setor['codigo'] for setor in SETORES_INICIAIS],
    ).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SetorOrganizacional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20, unique=True)),
                ('nome', models.CharField(max_length=120)),
                ('ativo', models.BooleanField(default=True)),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Setor Organizacional',
                'verbose_name_plural': 'Setores Organizacionais',
                'ordering': ['ordem', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='PerfilOrganizacional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cargo', models.CharField(blank=True, max_length=150, null=True)),
                ('data_admissao', models.DateField(blank=True, null=True)),
                ('pode_ser_avaliado', models.BooleanField(default=True)),
                ('ativo', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('gestor_direto', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='liderados_diretos', to=settings.AUTH_USER_MODEL)),
                ('setor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='perfis', to='core.setororganizacional')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_organizacional', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Perfil Organizacional',
                'verbose_name_plural': 'Perfis Organizacionais',
            },
        ),
        migrations.CreateModel(
            name='GestorSetor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ativo', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('gestor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='setores_gestor', to=settings.AUTH_USER_MODEL)),
                ('setor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gestores', to='core.setororganizacional')),
            ],
            options={
                'verbose_name': 'Gestor de Setor',
                'verbose_name_plural': 'Gestores de Setores',
                'unique_together': {('gestor', 'setor')},
            },
        ),
        migrations.RunPython(criar_setores_iniciais, remover_setores_iniciais),
    ]
