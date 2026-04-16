import pandas as pd
from django.core.management.base import BaseCommand
from rh.models import Funcionario


class Command(BaseCommand):
    help = "C:\Estudos\EmpregadosExcel_TI.xls"

    def handle(self, *args, **kwargs):
        caminho_arquivo = r"C:\Estudos\EmpregadosExcel_TI.xls"

        self.stdout.write(self.style.WARNING(f'Lendo arquivo: {caminho_arquivo}...'))

        try:
            df = pd.read_excel(caminho_arquivo)
            df = df.replace({pd.NA: None, float('nan'): None})
            df['Descrição Dpto'] = df['Descrição Dpto'].str.replace(' ', '_', regex=False).str.replace('-', '', regex=False)
            df['Admissão'] = pd.to_datetime(df['Admissão'], format='%d/%m/%Y', errors='coerce')
            df['Data Demissão'] = pd.to_datetime(df['Data Demissão'], format='%d/%m/%Y', errors='coerce')
            df['Admissão'] = df['Admissão'].dt.strftime('%Y-%m-%d')
            df['Data Demissão'] = df['Data Demissão'].dt.strftime('%Y-%m-%d')
            df = df.replace({pd.NA: None, float('nan'): None, 'NaT': None})

            mapa_setor = {
                'ADMINISTRATIVO': 'AD',
                'COMERCIAL': 'CO',
                'COMPRAS': 'CM',
                'DIRETORIA': 'DI',
                'FINANCEIRO': 'FI',
                'OBRAS': 'OB',
                'OBRA_MOSAIC': 'OM',
                'OBRA_TIMAC': 'OT',
                'PLANEJAMENTO_PROCESSO_E_QUALIDADE': 'PP',
                'PRAF_INDUSTRIAL_LTDA': 'PR',
                'PRODUÇÃO': 'PD',
                'PROJETOS': 'PJ',
                'RECURSOS_HUMANOS': 'RH',
                'Sede_ADM': 'SA',
                'TECNOLOGIA_DA_INFORMAÇAO': 'TI',
            }

            # TODO 2: Mapeamento de Situação
            mapa_situacao = {
                'Trabalhando': 'AT',
                #por enquanto, em breve adicionarei as demais
            }

            sucesso = 0

            for index, row in df.iterrows():
                cpf_excel = str(row['CPF']).strip()
                nome_excel = row['Nome']
                salario_excel = row['Salário']
                situacao_excel = row['Situação']
                data_demissao_excel = row['Data Demissão']
                grau_instrucao_excel = row['Grau instrução']
                sexo_excel = row['Sexo']
                dpto_excel = row['Descrição Dpto']
                desc_cargo_excel = row['Descrição cargo']
                admissao = row['Admissão']
                sigla_setor = mapa_setor.get(row['Descrição Dpto'], 'CA')
                sigla_situacao = mapa_situacao.get(row['Situação'], 'AT')


                Funcionario.objects.update_or_create(
                    cpf=cpf_excel,
                    defaults={
                        'nome_completo': nome_excel,
                        'situacao': sigla_situacao,
                        'setor': sigla_setor,
                        'data_admissao': admissao,
                        'data_demissao': data_demissao_excel if pd.notnull(data_demissao_excel) else None,
                        'cargo': desc_cargo_excel,
                        'salario': salario_excel,
                    }
                )
                sucesso += 1

            self.stdout.write(self.style.SUCCESS(f'Sucesso! {sucesso} funcionários processados.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro durante a importação: {str(e)}'))