from django import forms
from django.forms import BaseFormSet, BaseInlineFormSet, formset_factory, inlineformset_factory
from django.utils.dateparse import parse_duration

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


class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type = 'time'
    format = '%H:%M'


class DurationHHMMField(forms.DurationField):
    def prepare_value(self, value):
        if not value:
            return ''
        total_seconds = int(value.total_seconds()) if hasattr(value, 'total_seconds') else 0
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60
        return f'{hours:02d}:{minutes:02d}'

    def to_python(self, value):
        if not value:
            return None
        value = str(value).strip()
        if ':' in value:
            parts = value.split(':')
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                hours = int(parts[0])
                minutes = int(parts[1])
                if minutes > 59:
                    raise forms.ValidationError('Informe no formato HH:MM.')
                return parse_duration(f'{hours:02d}:{minutes:02d}:00')
        return super().to_python(value)


class ObraForm(forms.ModelForm):
    class Meta:
        model = Obra
        fields = [
            'nome',
            'cliente',
            'local',
            'contrato',
            'data_inicio',
            'data_previsao_fim',
            'data_fim',
            'logo_cliente',
            'responsavel_i9',
            'responsavel_cliente',
            'status',
            'observacoes',
        ]
        widgets = {
            'data_inicio': DateInput(),
            'data_previsao_fim': DateInput(),
            'data_fim': DateInput(),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }


class RDOForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero'].required = False

    class Meta:
        model = RDO
        fields = [
            'obra',
            'numero',
            'data',
            'condicao_manha',
            'condicao_tarde',
            'condicao_noite',
            'status',
            'observacoes_gerais',
        ]
        widgets = {
            'data': DateInput(),
            'observacoes_gerais': forms.Textarea(attrs={'rows': 4}),
        }


class EfetivoRDOForm(forms.ModelForm):
    horas_trabalhadas = DurationHHMMField(
        required=False,
        label='Horas trabalhadas',
        widget=forms.TextInput(attrs={'placeholder': 'HH:MM', 'pattern': r'[0-9]{1,3}:[0-5][0-9]'}),
    )

    def __init__(self, *args, **kwargs):
        self.obra = kwargs.pop('obra', None)
        super().__init__(*args, **kwargs)
        queryset = Funcao.objects.none()
        if self.obra:
            queryset = self.obra.funcoes.filter(ativo=True)
        elif self.instance and self.instance.pk:
            queryset = self.instance.rdo.obra.funcoes.filter(ativo=True)
        self.fields['funcao_cadastro'].queryset = queryset
        self.fields['funcao_cadastro'].label = 'Funcao'
        self.fields['funcao'].label = 'Funcao'
        self.fields['funcao'].required = False
        self.fields['funcao'].widget = forms.HiddenInput()
        self.fields['funcao_cadastro'].required = True

    class Meta:
        model = EfetivoRDO
        fields = ['funcao_cadastro', 'funcao', 'quantidade', 'horario_entrada', 'horas_trabalhadas', 'observacoes']
        widgets = {
            'horario_entrada': TimeInput(format='%H:%M'),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }


class EquipamentoRDOForm(forms.ModelForm):
    horas_utilizadas = DurationHHMMField(
        required=False,
        label='Horas utilizadas',
        widget=forms.TextInput(attrs={'placeholder': 'HH:MM', 'pattern': r'[0-9]{1,3}:[0-5][0-9]'}),
    )

    def __init__(self, *args, **kwargs):
        self.obra = kwargs.pop('obra', None)
        super().__init__(*args, **kwargs)
        queryset = Equipamento.objects.none()
        if self.obra:
            queryset = self.obra.equipamentos.filter(ativo=True)
        elif self.instance and self.instance.pk:
            queryset = self.instance.rdo.obra.equipamentos.filter(ativo=True)
        self.fields['equipamento_cadastro'].queryset = queryset
        self.fields['equipamento_cadastro'].label = 'Equipamento'
        self.fields['equipamento'].label = 'Equipamento'
        self.fields['equipamento'].required = False
        self.fields['equipamento'].widget = forms.HiddenInput()
        self.fields['equipamento_cadastro'].required = True

    class Meta:
        model = EquipamentoRDO
        fields = ['equipamento_cadastro', 'equipamento', 'quantidade', 'horas_utilizadas', 'status', 'observacoes']
        widgets = {'observacoes': forms.Textarea(attrs={'rows': 2})}


class AtividadeRDOForm(forms.ModelForm):
    class Meta:
        model = AtividadeRDO
        fields = ['descricao', 'local_execucao', 'percentual_avanco', 'observacoes']
        labels = {'local_execucao': 'Execucao'}
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }


class OcorrenciaRDOForm(forms.ModelForm):
    class Meta:
        model = OcorrenciaRDO
        fields = ['tipo', 'descricao', 'impacto', 'providencia']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'impacto': forms.Textarea(attrs={'rows': 2}),
            'providencia': forms.Textarea(attrs={'rows': 2}),
        }


class FotoRDOForm(forms.ModelForm):
    class Meta:
        model = FotoRDO
        fields = ['imagem', 'legenda']


class ObraChildFormSet(BaseInlineFormSet):
    pass


class ObraFuncaoForm(forms.Form):
    funcao = forms.ModelChoiceField(
        queryset=Funcao.objects.filter(ativo=True),
        required=False,
        label='Funcao',
        empty_label='----------',
    )


class BaseObraFuncaoFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        funcoes = []
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            funcao = form.cleaned_data.get('funcao')
            if funcao:
                funcoes.append(funcao)

        ids = [funcao.pk for funcao in funcoes]
        if len(ids) != len(set(ids)):
            raise forms.ValidationError('Nao repita a mesma funcao na obra.')

    def selected_funcoes(self):
        return [
            form.cleaned_data['funcao']
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE') and form.cleaned_data.get('funcao')
        ]


ObraFuncaoFormSet = formset_factory(
    ObraFuncaoForm,
    formset=BaseObraFuncaoFormSet,
    extra=1,
    can_delete=True,
)


class ObraEquipamentoForm(forms.Form):
    equipamento = forms.ModelChoiceField(
        queryset=Equipamento.objects.filter(ativo=True),
        required=False,
        label='Equipamento',
        empty_label='----------',
    )


class BaseObraEquipamentoFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        equipamentos = []
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            equipamento = form.cleaned_data.get('equipamento')
            if equipamento:
                equipamentos.append(equipamento)

        ids = [equipamento.pk for equipamento in equipamentos]
        if len(ids) != len(set(ids)):
            raise forms.ValidationError('Nao repita o mesmo equipamento na obra.')

    def selected_equipamentos(self):
        return [
            form.cleaned_data['equipamento']
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE') and form.cleaned_data.get('equipamento')
        ]


ObraEquipamentoFormSet = formset_factory(
    ObraEquipamentoForm,
    formset=BaseObraEquipamentoFormSet,
    extra=1,
    can_delete=True,
)


class ObraAwareInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.obra = kwargs.pop('obra', None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        if self.obra:
            kwargs['obra'] = self.obra
        return super()._construct_form(i, **kwargs)


EfetivoFormSet = inlineformset_factory(
    RDO,
    EfetivoRDO,
    form=EfetivoRDOForm,
    formset=ObraAwareInlineFormSet,
    extra=1,
    can_delete=True,
)

EquipamentoFormSet = inlineformset_factory(
    RDO,
    EquipamentoRDO,
    form=EquipamentoRDOForm,
    formset=ObraAwareInlineFormSet,
    extra=1,
    can_delete=True,
)

AtividadeFormSet = inlineformset_factory(
    RDO,
    AtividadeRDO,
    form=AtividadeRDOForm,
    extra=1,
    can_delete=True,
)

OcorrenciaFormSet = inlineformset_factory(
    RDO,
    OcorrenciaRDO,
    form=OcorrenciaRDOForm,
    extra=1,
    can_delete=True,
)

FotoFormSet = inlineformset_factory(
    RDO,
    FotoRDO,
    form=FotoRDOForm,
    extra=1,
    can_delete=True,
)
