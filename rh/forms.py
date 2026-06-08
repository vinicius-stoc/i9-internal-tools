import re
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .models import (Candidatura, Vaga, SolicitacaoVaga, PesquisaDemissional,
                     FormularioAdmissional, DependenteAdmissional)


class CandidaturaForm(forms.ModelForm):
    class Meta:
        model = Candidatura
        fields = ['nome_completo', 'email', 'telefone', 'linkedin', 'curriculo']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'curriculo': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        }

class VagaForm(forms.ModelForm):
    class Meta:
        model = Vaga
        fields = ['titulo', 'setor', 'descricao', 'requisitos', 'ativa']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Analista de TI Sênior'}),
            'setor': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descreva o dia a dia da função, responsabilidades e desafios...'}),
            'requisitos': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ex: Superior completo, experiência com Python, Django, etc...'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'})
        }

class SolicitacaoVagaForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoVaga
        exclude = ['solicitante', 'data_solicitacao', 'status', 'observacoes_rh']

        widgets = {
            'data_prevista_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cargo_solicitante': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ex: Gerente de Obras'}),
            'nome_vaga': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade_vagas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.Select(attrs={'class': 'form-select'}),
            'nome_substituido': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Preencha apenas em caso de substituição'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'escolaridade': forms.Select(attrs={'class': 'form-select'}),
            'curso_area': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ex: Engenharia Civil, Administração...'}),
            'descricao_atividades': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'conhecimentos_desejaveis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'atitudes_desejaveis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observacoes_gerais': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_data_prevista_inicio(self):
        data = self.cleaned_data.get('data_prevista_inicio')
        if data:
            if data.weekday() != 0:
                raise ValidationError(
                    "A política da empresa exige que as admissões ocorram sempre em uma Segunda-feira. Por favor, ajuste a data.")
        return data

    def clean(self):
        cleaned_data = super().clean()
        motivo = cleaned_data.get('motivo')
        nome_substituido = cleaned_data.get('nome_substituido')

        if motivo and 'SUBST' in motivo:
            if not nome_substituido:
                self.add_error('nome_substituido',
                               'Como o motivo é substituição, é obrigatório informar o nome de quem está saindo.')

        return cleaned_data

class PesquisaDemissionalGeracaoForm(forms.ModelForm):
    """
    Formulario exclusivo para o RH gerar link da pesquisa
    """
    class Meta:
        model = PesquisaDemissional
        fields = ['ex_funcionario_nome', 'setor', 'tipo_demissao', 'periodo_saida', 'tempo_casa']
        widgets = {
            'periodo_saida': forms.TextInput(attrs={'placeholder': 'Ex: Março/2026'}),
            'tempo_casa': forms.TextInput(attrs={'placeholder': 'Ex: 2 anos e 3 meses'})
        }

class PesquisaDemissionalRespostaForm(forms.ModelForm):
    """
    Formulario publico para o ex-colaborador responder
    """
    class Meta:
        model = PesquisaDemissional
        fields = [
            'motivo_saida', 'diferente', 'nota_lideranca',
            'nota_oportunidade', 'nota_reconhecimento',
            'nota_clima', 'nota_recomendacao'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        escala_1_a_5 = ['nota_lideranca', 'nota_oportunidade', 'nota_reconhecimento', 'nota_clima']
        for field in escala_1_a_5:
            self.fields[field].widget = forms.NumberInput(attrs={'min': 1, 'max': 5, 'required': True})

        self.fields['nota_recomendacao'].widget = forms.NumberInput(attrs={'min': 0, 'max': 10, 'required': True})

        self.fields['diferente'].widget = forms.Textarea(attrs={'rows': 4})


class FormularioAdmissionalGeracaoForm(forms.ModelForm):
    """
    Formulario interno para o RH gerar link admissional.
    """
    class Meta:
        model = FormularioAdmissional
        fields = ['candidato_nome_interno']
        widgets = {
            'candidato_nome_interno': forms.TextInput(attrs={'class': 'form-control'})
        }


class FormularioAdmissionalRespostaForm(forms.ModelForm):
    """
    Formulario publico para preenchimento admissional.
    """
    campos_obrigatorios = [
        'nome_completo', 'cpf', 'cidade_estado', 'funcao_pretendida',
        'pis', 'numero_ctps', 'serie_ctps', 'uf_ctps',
        'cep', 'endereco',
        'telefone_principal', 'contato_recado', 'email',
        'data_nascimento', 'estado_nascimento', 'naturalidade', 'cor_raca',
        'grau_instrucao', 'nome_mae', 'nome_pai',
        'numero_rg', 'orgao_expedidor', 'uf_rg', 'data_emissao_rg',
        'estado_civil', 'possui_dependentes_ir',
        'botina', 'camisa', 'calca',
        'utiliza_vale_transporte', 'lgpd_consentimento',
    ]

    class Meta:
        model = FormularioAdmissional
        fields = [
            'nome_completo', 'cpf', 'cidade_estado', 'funcao_pretendida',
            'pis', 'numero_ctps', 'serie_ctps', 'uf_ctps',
            'cep', 'endereco',
            'telefone_principal', 'contato_recado', 'email',
            'data_nascimento', 'estado_nascimento', 'naturalidade', 'cor_raca',
            'grau_instrucao', 'nome_mae', 'nome_pai',
            'numero_rg', 'orgao_expedidor', 'uf_rg', 'data_emissao_rg',
            'titulo_eleitor', 'zona_eleitoral', 'secao_eleitoral', 'uf_titulo_eleitor',
            'reservista', 'cnh',
            'estado_civil', 'possui_dependentes_ir',
            'botina', 'camisa', 'calca',
            'utiliza_vale_transporte', 'trajeto_vale_transporte', 'lgpd_consentimento',
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'data_emissao_rg': forms.DateInput(attrs={'type': 'date'}),
            'trajeto_vale_transporte': forms.Textarea(attrs={'rows': 3}),
            'lgpd_consentimento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for nome, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

        for nome in self.campos_obrigatorios:
            self.fields[nome].required = True

        self.fields['cidade_estado'].help_text = 'Ex.: Araucária-PR'
        self.fields['funcao_pretendida'].help_text = 'Ex.: Ajudante, Soldador, Assistente Administrativo'
        self.fields['endereco'].help_text = 'Rua, número, bairro e complemento'
        self.fields['naturalidade'].help_text = 'Cidade onde nasceu'
        self.fields['cnh'].help_text = 'Informar número, validade e estado'
        self.fields['trajeto_vale_transporte'].required = False
        self.fields['trajeto_vale_transporte'].help_text = 'Informe as linhas, terminais ou o caminho utilizado entre sua residência e o trabalho.'

        self.fields['cor_raca'].choices = [
            ('', '---------'),
            ('BRANCA', 'Branca'),
            ('PRETA', 'Preta'),
            ('PARDA', 'Parda'),
            ('AMARELA', 'Amarela'),
            ('INDIGENA', 'Indígena'),
            ('NAO_INFORMAR', 'Prefiro não informar'),
        ]
        self.fields['grau_instrucao'].choices = [
            ('', '---------'),
            ('FUND_INCOMPLETO', 'Ensino Fundamental Incompleto'),
            ('FUND_COMPLETO', 'Ensino Fundamental Completo'),
            ('MEDIO_INCOMPLETO', 'Ensino Médio Incompleto'),
            ('MEDIO_COMPLETO', 'Ensino Médio Completo'),
            ('SUPERIOR_INCOMPLETO', 'Ensino Superior Incompleto'),
            ('SUPERIOR_COMPLETO', 'Ensino Superior Completo'),
            ('POS_GRADUACAO', 'Pós-graduação'),
            ('MESTRADO', 'Mestrado'),
            ('DOUTORADO', 'Doutorado'),
        ]
        self.fields['estado_civil'].choices = [
            ('', '---------'),
            ('SOLTEIRO', 'Solteiro(a)'),
            ('CASADO', 'Casado(a)'),
            ('UNIAO_ESTAVEL', 'União Estável'),
            ('DIVORCIADO', 'Divorciado(a)'),
            ('SEPARADO', 'Separado(a)'),
            ('VIUVO', 'Viúvo(a)'),
        ]
        self.fields['possui_dependentes_ir'].choices = [
            ('', '---------'),
            ('SIM', 'Sim'),
            ('NAO', 'Não'),
        ]
        self.fields['utiliza_vale_transporte'].choices = [
            ('', '---------'),
            ('SIM', 'Sim'),
            ('NAO', 'Não'),
        ]

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data.get('cpf') or '')
        if len(cpf) != 11:
            raise ValidationError('CPF deve conter 11 digitos.')
        return cpf

    def clean_cep(self):
        cep = re.sub(r'\D', '', self.cleaned_data.get('cep') or '')
        if not cep.isdigit():
            raise ValidationError('CEP deve conter apenas numeros.')
        return cep

    def clean_lgpd_consentimento(self):
        consentimento = self.cleaned_data.get('lgpd_consentimento')
        if not consentimento:
            raise ValidationError('E necessario aceitar o uso dos dados para fins admissionais e obrigacoes legais.')
        return consentimento

    def clean(self):
        cleaned_data = super().clean()
        utiliza_vale_transporte = cleaned_data.get('utiliza_vale_transporte')
        trajeto_vale_transporte = cleaned_data.get('trajeto_vale_transporte')

        if utiliza_vale_transporte == 'SIM' and not trajeto_vale_transporte:
            self.add_error('trajeto_vale_transporte', 'Informe o trajeto caso utilize vale transporte.')

        if utiliza_vale_transporte == 'NAO':
            cleaned_data['trajeto_vale_transporte'] = ''

        return cleaned_data


class DependenteAdmissionalForm(forms.ModelForm):
    class Meta:
        model = DependenteAdmissional
        fields = ['nome_completo', 'data_nascimento', 'rg', 'cpf', 'cidade_estado_nascimento']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean_cpf(self):
        cpf = re.sub(r'\D', '', self.cleaned_data.get('cpf') or '')
        if cpf and len(cpf) != 11:
            raise ValidationError('CPF do dependente deve conter 11 digitos.')
        return cpf

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('DELETE'):
            return cleaned_data

        valores = [
            cleaned_data.get('nome_completo'),
            cleaned_data.get('data_nascimento'),
            cleaned_data.get('rg'),
            cleaned_data.get('cpf'),
            cleaned_data.get('cidade_estado_nascimento'),
        ]
        preenchidos = [valor for valor in valores if valor]

        if preenchidos and len(preenchidos) < len(valores):
            raise ValidationError('Preencha todos os campos do dependente ou deixe a linha em branco.')

        return cleaned_data


DependenteAdmissionalFormSet = inlineformset_factory(
    FormularioAdmissional,
    DependenteAdmissional,
    form=DependenteAdmissionalForm,
    extra=2,
    can_delete=True,
)
