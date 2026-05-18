from django.db import migrations


def forwards(apps, schema_editor):
    Chamado = apps.get_model('ti', 'Chamado')
    Chamado.objects.filter(setor='RECURSOS HUMADOS').update(setor='RECURSOS HUMANOS')


def backwards(apps, schema_editor):
    Chamado = apps.get_model('ti', 'Chamado')
    Chamado.objects.filter(setor='RECURSOS HUMANOS').update(setor='RECURSOS HUMADOS')


class Migration(migrations.Migration):
    dependencies = [
        ('ti', '0005_alter_chamado_categoria_alter_chamado_data_abertura_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
