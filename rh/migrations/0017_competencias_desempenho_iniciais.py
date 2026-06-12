# Generated manually on 2026-06-08

from django.db import migrations


COMPETENCIAS = [
    (
        1,
        'Pontualidade/ Assiduidade',
        'Chega e sai nos horários estabelecidos. Avisa com antecedência possíveis atrasos ou saídas antecipadas. É pontual em reuniões e eventos.',
    ),
    (
        2,
        'Iniciativa/Pró-atividade',
        'Capacidade de antecipar-se, não espera determinações. Apresenta sugestões pertinentes com frequência. Tem iniciativa para conhecer atividades diversas das que executa.',
    ),
    (
        3,
        'Relacionamento',
        'Se relaciona bem com clientes internos e externos.',
    ),
    (
        4,
        'Organização',
        'Elabora cronograma de atividades, definindo prazos e prioridades. Executa suas atividades de maneira lógica e objetiva, de forma a serem facilmente compreendidas e continuadas por terceiros em caso de necessidade.',
    ),
    (
        5,
        'Metas',
        'Cumpre todas as metas estabelecidas. Contribui decisivamente e com contínuo esforço para o alcance ou a superação de suas metas e as da empresa.',
    ),
    (
        6,
        'Qualidade do serviço /Atenção',
        'Desenvolve seu trabalho de acordo com os requisitos. Entrega trabalhos completos, revisados e corretos. Presta atenção no que faz e toma providências para não haver erros; quando esses ocorrem, atua de modo a evitar sua reincidência.',
    ),
    (
        7,
        'Postura Profissional',
        'Apresenta bom marketing pessoal, honestidade, discrição e aparência adequada. Uniforme adequado, asseio e apresentação pessoal.',
    ),
    (
        8,
        'Conhecimento / Desenvolvimento profissional',
        'Conhece profundamente as atividades inerentes à sua função. Interessa-se em manter-se atualizado sobre os assuntos do seu setor. Participa de cursos, treinamentos e outros eventos de capacitação e atualização necessários à função que exerce.',
    ),
    (
        9,
        'Liderança',
        'Capacidade de engajar equipe. Consegue persuadir e influenciar equipe na conquista dos objetivos. A equipe o considera uma boa liderança.',
    ),
]


def cadastrar_competencias(apps, schema_editor):
    CompetenciaDesempenho = apps.get_model('rh', 'CompetenciaDesempenho')
    for ordem, nome, descricao in COMPETENCIAS:
        competencia, _ = CompetenciaDesempenho.objects.get_or_create(
            ordem=ordem,
            defaults={
                'nome': nome,
                'descricao': descricao,
                'ativa': True,
            },
        )
        competencia.nome = nome
        competencia.descricao = descricao
        competencia.ativa = True
        competencia.save(update_fields=['nome', 'descricao', 'ativa'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('rh', '0016_avaliacaodesempenho_competenciadesempenho_and_more'),
    ]

    operations = [
        migrations.RunPython(cadastrar_competencias, noop),
    ]
