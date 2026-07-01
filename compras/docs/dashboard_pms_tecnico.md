# Dashboard Financeiro PMS de Compras - README tecnico

## 1. Visao geral

O Dashboard Financeiro PMS de Compras consolida dados do PMS/Protheus para acompanhar custo previsto, custo empenhado e custo realizado por projeto, EDT/WBS e tarefa.

A tela principal esta em `compras/templates/compras/dashboard.html` e e alimentada pela view `dashboard_compras`, pelo selector `PmsDashboardSelector` e pelos services PMS do app `compras`.

O dashboard trabalha com dados materializados no banco, nao consulta arquivos SDB diretamente durante a renderizacao.

## 2. Objetivo

O objetivo e permitir analise executiva e operacional de gastos PMS em Compras:

- identificar quanto ja virou custo realizado;
- comparar custo realizado contra valor empenhado;
- localizar custo sem empenho;
- analisar concentracao de custo por projeto, EDT/WBS e tarefa;
- acompanhar tendencia mensal de empenho e realizacao;
- apoiar investigacao de projetos fora da curva.

## 3. Arquitetura do fluxo

Fluxo atual:

1. O command `sync_pms_dashboard` executa a carga PMS.
2. `ComprasPmsETLService` le e limpa os SDBs via base ETL do Protheus.
3. O ETL monta registros Django em memoria.
4. Os models PMS sao materializados no banco.
5. A view `dashboard_compras` recebe filtros via `GET`.
6. A view delega o contexto para `PmsDashboardSelector.get_context`.
7. O selector consulta models materializados, aplica filtros, monta KPIs, graficos e tabela hierarquica.
8. `PmsExecutiveMetricsService` monta KPIs e graficos executivos.
9. O template renderiza cards, graficos Chart.js, filtro Choices.js e tabela Alpine.js.

Arquivos centrais:

- `compras/views.py`
- `compras/selectors/pms_dashboard.py`
- `compras/services/pms_hierarchy.py`
- `compras/services/pms_executive_metrics.py`
- `compras/services/pms_etl_service.py`
- `compras/models.py`
- `compras/templates/compras/dashboard.html`
- `compras/management/commands/sync_pms_dashboard.py`
- `compras/management/commands/validar_dashboard_pms.py`

## 4. Fluxo completo dos dados

### Protheus SDB

Os dados PMS e financeiros partem dos arquivos SDB:

- `AF80101.sdb`: projetos PMS.
- `AFC0101.sdb`: EDT/WBS.
- `AF90101.sdb`: tarefas.
- `AFA0101.sdb`: produtos previstos por tarefa.
- `AFB0101.sdb`: despesas previstas por tarefa.
- `AFG0101.sdb`: distribuicao/rateio entre solicitacao e tarefa PMS.
- `SC70101.sdb`: pedidos de compra e valores empenhados.
- `SD10101.sdb`: recebimentos/notas de entrada e valores realizados.

### ETL

O service `ComprasPmsETLService` herda de `ProtheusBaseETL`.

Responsabilidades do ETL:

- validar schema minimo dos arquivos;
- montar projetos, EDTs e tarefas;
- calcular custo previsto;
- calcular custo empenhado por rateio;
- calcular custo realizado por rateio;
- montar serie temporal mensal;
- limpar dados PMS materializados;
- gravar nova fotografia no banco;
- registrar status em `ComprasSyncLog`.

### Models materializados

A camada de dashboard usa os models:

- `PmsProjeto`
- `PmsEdt`
- `PmsTarefa`
- `PmsCustoTarefa`
- `PmsCustoTemporalMensal`
- `ComprasSyncLog`

### Selector

`PmsDashboardSelector.get_context` e a entrada principal para montar o contexto da tela.

O selector:

- normaliza filtro de projeto;
- normaliza filtro de categoria;
- escolhe revisao padrao para projeto unico;
- lista projetos, EDTs, tarefas, custos e serie temporal;
- aplica filtro de categoria;
- consolida KPIs principais;
- monta tabela hierarquica;
- chama `PmsExecutiveMetricsService`;
- prepara datasets dos graficos;
- prepara dados de exportacao CSV.

### Services

`pms_hierarchy.py` concentra:

- indicadores de empenho;
- situacao financeira;
- caminhos de EDT;
- descendentes de EDT;
- consolidacao por EDT;
- consolidacao por projeto.

`pms_executive_metrics.py` concentra:

- KPIs executivos;
- grafico de eficiencia;
- analise de EDTs criticas;
- Pareto;
- matriz de risco;
- serie temporal.

### Template e Chart.js

`dashboard.html` renderiza:

- cards principais;
- cards executivos;
- graficos Chart.js;
- filtro multi-select com Choices.js;
- tabela hierarquica com Alpine.js;
- status da ultima sincronizacao.

SweetAlert2 ja e carregado globalmente em `core/templates/base.html`.

## 5. Tabelas Protheus utilizadas

### AF8 - Projetos PMS

Campos principais usados:

- `AF8_FILIAL`
- `AF8_PROJET`
- `AF8_REVISA`
- `AF8_DESCRI`
- `AF8_DATA`
- `AF8_CALEND`
- `AF8_MASCAR`
- `AF8_DELIM`

Destino: `PmsProjeto`.

### AFC - EDT/WBS

Campos principais usados:

- `AFC_FILIAL`
- `AFC_PROJET`
- `AFC_REVISA`
- `AFC_EDT`
- `AFC_EDTPAI`
- `AFC_DESCRI`
- `AFC_NIVEL`
- `AFC_ORDEM`
- `AFC_UM`
- `AFC_QUANT`
- `AFC_CUSTO`

Destino: `PmsEdt`.

### AF9 - Tarefas

Campos principais usados:

- `AF9_FILIAL`
- `AF9_PROJET`
- `AF9_REVISA`
- `AF9_TAREFA`
- `AF9_EDTPAI`
- `AF9_DESCRI`
- `AF9_NIVEL`
- `AF9_ORDEM`
- `AF9_UM`
- `AF9_QUANT`
- `AF9_START`
- `AF9_FINISH`
- `AF9_CUSTO`

Destino: `PmsTarefa` e base de `PmsCustoTarefa`.

### AFA - Produtos previstos

Campos usados no calculo:

- `AFA_FILIAL`
- `AFA_PROJET`
- `AFA_REVISA`
- `AFA_TAREFA`
- `AFA_QUANT`
- `AFA_CUSTD`

Destino indireto: `PmsCustoTarefa.custo_previsto_produtos`.

### AFB - Despesas previstas

Campos usados no calculo:

- `AFB_FILIAL`
- `AFB_PROJET`
- `AFB_REVISA`
- `AFB_TAREFA`
- `AFB_VALOR`

Destino indireto: `PmsCustoTarefa.custo_previsto_despesas`.

### AFG - Rateio PMS

Campos usados no calculo:

- `AFG_FILIAL`
- `AFG_PROJET`
- `AFG_REVISA`
- `AFG_TAREFA`
- `AFG_NUMSC`
- `AFG_ITEMSC`
- `AFG_QUANT`

Usado para distribuir valores de SC7 e SD1 por tarefa PMS.

### SC7 - Pedidos de compra

Campos usados no calculo:

- `C7_FILIAL`
- `C7_NUMSC`
- `C7_ITEMSC`
- `C7_NUM`
- `C7_ITEM`
- `C7_TOTAL`
- `C7_EMISSAO`
- `C7_DTLANC`

Destino indireto: `PmsCustoTarefa.custo_empenhado` e `PmsCustoTemporalMensal.custo_empenhado`.

### SD1 - Recebimentos/notas

Campos usados no calculo:

- `D1_FILIAL`
- `D1_PEDIDO`
- `D1_ITEMPC`
- `D1_TOTAL`
- `D1_DTDIGIT`
- `D1_EMISSAO`
- `D1_DATACUS`

Destino indireto: `PmsCustoTarefa.custo_realizado` e `PmsCustoTemporalMensal.custo_realizado`.

## 6. Models Django utilizados

### PmsProjeto

Grao: filial + projeto + revisao.

Constraint:

- `uniq_pms_projeto_revisao`

Uso no dashboard:

- lista de projetos;
- descricao do projeto;
- revisao padrao;
- status de escopo atual.

### PmsEdt

Grao: filial + projeto + revisao + EDT.

Constraint:

- `uniq_pms_edt_revisao`

Uso no dashboard:

- arvore EDT/WBS;
- agrupamento hierarquico;
- graficos de EDT;
- analise de EDTs criticas.

### PmsTarefa

Grao: filial + projeto + revisao + tarefa.

Constraint:

- `uniq_pms_tarefa_revisao`

Uso no dashboard:

- linhas de tarefa;
- vinculo com EDT;
- classificacao de categoria;
- volume de projeto quando nao ha custo previsto.

### PmsCustoTarefa

Grao: filial + projeto + revisao + tarefa.

Constraint:

- `uniq_pms_custo_tarefa_revisao`

Uso no dashboard:

- KPIs principais;
- graficos de custo;
- consolidacao por EDT;
- tabela principal;
- KPIs executivos.

### PmsCustoTemporalMensal

Grao: filial + projeto + revisao + tarefa + competencia.

Constraint:

- `uniq_pms_custo_temporal`

Uso no dashboard:

- tendencia temporal;
- acumulados mensais;
- variacao mensal;
- media movel 3M;
- burn rate de EDTs.

### ComprasSyncLog

Uso no dashboard:

- ultima sincronizacao;
- status visual da carga;
- exibicao de erro de sync.

## 7. Chaves de relacionamento

Chave de projeto:

```text
filial + projeto + revisao
```

Chave de EDT:

```text
filial + projeto + revisao + edt
```

Chave de tarefa:

```text
filial + projeto + revisao + tarefa
```

Chave de solicitacao:

```text
filial + numero SC + item SC
```

Chave de pedido:

```text
filial + pedido + item do pedido
```

Vinculo financeiro:

```text
AFG -> SC7 por filial + numero SC + item SC
SC7 -> SD1 por filial + pedido + item do pedido
```

## 8. Regra de calculo do custo previsto

O custo previsto principal da tarefa vem de:

```text
AF9_CUSTO
```

O ETL tambem materializa o detalhamento:

```text
custo_previsto_produtos = soma(AFA_QUANT * AFA_CUSTD)
custo_previsto_despesas = soma(AFB_VALOR)
custo_previsto_detalhado = custo_previsto_produtos + custo_previsto_despesas
```

O KPI principal usa `PmsCustoTarefa.custo_previsto`.

## 9. Regra de calculo do custo empenhado

O custo empenhado vem de pedidos de compra SC7.

Fluxo:

1. AFG mapeia solicitacao para tarefa PMS.
2. SC7 informa valor do pedido em `C7_TOTAL`.
3. O ETL distribui `C7_TOTAL` entre tarefas PMS conforme proporcao de `AFG_QUANT`.
4. O resultado e gravado em `PmsCustoTarefa.custo_empenhado`.

Formula conceitual:

```text
proporcao_tarefa = AFG_QUANT da tarefa / soma(AFG_QUANT da solicitacao)
custo_empenhado_tarefa = C7_TOTAL * proporcao_tarefa
```

## 10. Regra de calculo do custo realizado

O custo realizado vem de recebimentos/notas SD1.

Fluxo:

1. AFG mapeia solicitacao para tarefa PMS.
2. SC7 liga solicitacao a pedido.
3. SD1 informa recebimento por pedido/item.
4. O ETL distribui `D1_TOTAL` conforme proporcao da AFG.
5. O resultado e gravado em `PmsCustoTarefa.custo_realizado`.

Formula conceitual:

```text
custo_realizado_tarefa = D1_TOTAL * proporcao_tarefa
```

## 11. Regra de rateio por AFG

O rateio usa `AFG_QUANT`.

Para cada solicitacao:

```text
soma_quantidade = soma(AFG_QUANT)
proporcao = AFG_QUANT / soma_quantidade
```

Se a soma de quantidade for zero ou negativa, o ETL levanta erro.

O ETL tambem impede que o mesmo pedido seja vinculado a distribuicoes PMS conflitantes.

## 12. Regra de competencia temporal

A serie temporal mensal usa datas financeiras de SC7 e SD1.

Prioridade para SC7:

1. `C7_EMISSAO`
2. `C7_DTLANC`

Prioridade para SD1:

1. `D1_DTDIGIT`
2. `D1_EMISSAO`
3. `D1_DATACUS`

A competencia e normalizada para o primeiro dia do mes:

```text
data_financeira.replace(day=1)
```

`atualizado_em` nao deve ser usado como data financeira.

## 13. KPIs principais

### Custo

Soma de `PmsCustoTarefa.custo_realizado` no escopo filtrado.

### Empenhado

Soma de `PmsCustoTarefa.custo_empenhado` no escopo filtrado.

### Saldo do empenho

```text
custo_empenhado - custo_realizado
```

Valor negativo indica custo acima do empenho.

### Percentual convertido em custo

```text
custo_realizado / custo_empenhado * 100
```

Quando nao ha empenho, o percentual fica zero.

### Custo sem empenho

Soma do custo realizado das tarefas cujo empenhado e zero.

### Custo previsto

Soma de `PmsCustoTarefa.custo_previsto`.

### Saldo previsto x realizado

Soma de `PmsCustoTarefa.saldo_previsto_realizado`.

No ETL, o saldo da tarefa e calculado como:

```text
custo_previsto - custo_realizado
```

### Percentual realizado

```text
custo_realizado / custo_previsto * 100
```

Quando nao ha previsto, o percentual fica zero.

## 14. KPIs executivos

`PmsExecutiveMetricsService` calcula:

- media de custo por projeto;
- mediana de custo por projeto;
- projeto com maior custo;
- projeto com maior percentual acima do empenho;
- EDT mais critica por custo realizado;
- quantidade de projetos fora da curva;
- concentracao 80/20.

Projeto fora da curva, na regra atual:

```text
custo_realizado > mediana de custo
e percentual_acima_empenho > 0
```

Percentual acima do empenho:

```text
0, se custo_realizado <= custo_empenhado
100, se custo_realizado > 0 e custo_empenhado = 0
(custo_realizado - custo_empenhado) / custo_empenhado * 100, nos demais casos
```

## 15. Graficos

### Custo x Empenhado

Compara soma de custo realizado contra soma de empenhado no escopo filtrado.

Origem:

- `PmsCustoTarefa.custo_realizado`
- `PmsCustoTarefa.custo_empenhado`

### Top 10 Projetos por Custo

Usado em modo carteira.

Agrupa custos por projeto e ordena por custo realizado descrescente.

### Top 10 EDT/WBS por Custo

Usado em modo projeto.

Usa consolidacao de EDTs, incluindo tarefas das EDTs descendentes.

### Top 10 Tarefas por Custo

Agrupa por projeto + tarefa e ordena por custo realizado descrescente.

### Eficiencia: Volume x Custo Realizado

Grafico scatter.

Eixo X:

- custo previsto do projeto, quando existir;
- quantidade de tarefas, se nao houver custo previsto;
- quantidade de EDTs, se nao houver tarefas;
- zero, se nenhum volume estiver disponivel.

Eixo Y:

- custo realizado.

Outlier atual:

```text
custo_realizado > media de custo realizado dos projetos
```

Essa regra e simples e deve ser interpretada como alerta visual, nao como metodo estatistico robusto.

### Matriz de Risco Financeiro

Grafico scatter.

Eixo X:

- custo realizado.

Eixo Y:

- percentual acima do empenho.

Corte de impacto:

```text
mediana do custo realizado
```

Quadrantes:

- alto custo acima do empenho;
- alto custo dentro do empenho;
- baixo custo acima do empenho;
- baixo custo dentro do empenho.

### Tendencia Temporal Financeira

Usa `PmsCustoTemporalMensal`.

Datas devem estar normalizadas para o primeiro dia do mes.

Series:

- custo realizado mensal;
- empenhado mensal;
- media movel 3M;
- custo realizado acumulado;
- empenhado acumulado;
- variacao mensal.

### Pareto Projetos

Ordena projetos por custo realizado e calcula percentual acumulado.

### Pareto EDTs

Ordena EDTs por custo realizado e calcula percentual acumulado.

### Pareto Tarefas

Ordena tarefas por custo realizado e calcula percentual acumulado.

### EDTs Criticas

Lista as 10 EDTs com maior custo realizado.

Campos exibidos:

- projeto;
- EDT/WBS;
- descricao;
- custo;
- empenhado;
- percentual no total;
- burn rate.

Burn rate:

```text
custo_realizado / dias_analise
```

`dias_analise` e derivado da janela temporal disponivel em `PmsCustoTemporalMensal`.

### Tabela principal

Exibida apenas em modo projeto unico.

Mostra arvore:

```text
Projeto > EDT/WBS > Tarefa
```

A paginacao e de 100 linhas, preservando ancestrais necessarios via `parent_chain`.

## 16. Filtros

### Projeto

A view usa:

```python
request.GET.getlist("projeto")
```

Regras:

- nenhum projeto selecionado: modo carteira com todos os projetos;
- um projeto selecionado: modo projeto;
- multiplos projetos selecionados: modo carteira filtrada.

Em modo carteira, o selector aplica a maior revisao disponivel por projeto antes de calcular KPIs, graficos executivos, Pareto, rankings e serie temporal.

### Categorias

A view usa:

```python
request.GET.getlist("categorias")
```

Categorias atuais:

- `materia_prima`
- `itens_comerciais`
- `fixadores`

A categoria e inferida por termos na descricao da tarefa.

### Paginacao

O selector monta `pagination_querystring` preservando parametros repetidos de projeto e categoria.

## 17. Regras de validacao

O command `validar_dashboard_pms` executa validacoes somente leitura:

- integridade referencial entre custos, projetos, EDTs e tarefas;
- projetos sem custos;
- tarefas sem EDT valida;
- multiplas revisoes por projeto;
- totais principais contra contexto do selector;
- soma da tabela principal contra `PmsCustoTarefa`;
- soma de EDTs contra tarefas descendentes;
- situacao financeira;
- ordenacao de top 10;
- labels e tooltips;
- Pareto acumulado;
- serie temporal;
- disponibilidade dos SDBs locais.

Status:

- `OK`: nenhuma divergencia relevante.
- `ALERTA`: limitacao, dado incompleto ou risco explicavel.
- `ERRO`: calculo divergente, integridade quebrada ou regra inconsistente.

## 18. Limitacoes conhecidas

### Revisao em modo carteira

Em modo projeto unico, o selector usa a maior revisao do projeto.

Em modo carteira, o selector tambem filtra a maior revisao por projeto antes de montar custos, EDTs, tarefas e serie temporal.

Essa regra evita somar revisoes antigas do mesmo projeto nos totais executivos.

O command de validacao ainda lista projetos com multiplas revisoes como `ALERTA` porque a existencia de historico materializado exige cuidado ao investigar divergencias diretamente no banco.

### Integridade PMS materializada

Na validacao local por amostragem, foram encontrados:

- custos sem projeto PMS correspondente;
- custos com EDT inexistente;
- EDTs sem projeto PMS correspondente;
- tarefas sem EDT valida.

Esses achados indicam risco de carga parcial, projeto tecnico legado, inconsistencia na origem ou regra de exclusao diferente entre AF8/AFC/AF9/custos.

Nao corrigir sem analise de causa.

### SDB bruto parcial

No ambiente local, a validacao encontrou SDBs parciais em `compras/data`, mas faltaram arquivos PMS obrigatorios para recomputar tudo contra bruto:

- `af80101.sdb`
- `af90101.sdb`
- `afa0101.sdb`
- `afb0101.sdb`
- `afc0101.sdb`

Sem esses arquivos, a validacao contra Protheus bruto fica limitada.

### Outlier simples

O grafico de eficiencia marca outlier por comparacao com a media simples de custo realizado. Nao e uma deteccao estatistica robusta.

## 19. Como rodar a validacao por amostragem

Comando padrao:

```powershell
python manage.py validar_dashboard_pms --sample-size 5
```

Validar projeto especifico:

```powershell
python manage.py validar_dashboard_pms --projeto JP010125 --sample-size 5
```

Validar mais de um projeto:

```powershell
python manage.py validar_dashboard_pms --projeto JP010125 --projeto MO190625
```

Validar todos os projetos:

```powershell
python manage.py validar_dashboard_pms --all-projects
```

Definir tolerancia:

```powershell
python manage.py validar_dashboard_pms --sample-size 5 --tolerance 0.01
```

No ambiente Codex local deste repo, se `python` nao estiver no PATH, usar o runtime Python com `PYTHONPATH` apontando para a venv:

```powershell
$env:PYTHONPATH='.venv\Lib\site-packages;.'
& 'C:\Users\Admini9TMG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' manage.py validar_dashboard_pms --sample-size 5
```

## 20. Como investigar divergencias

### Integridade referencial

Verificar se a chave existe nos models:

- `PmsProjeto`: filial + projeto + revisao.
- `PmsEdt`: filial + projeto + revisao + EDT.
- `PmsTarefa`: filial + projeto + revisao + tarefa.
- `PmsCustoTarefa`: filial + projeto + revisao + tarefa.

Se houver custo sem projeto ou EDT sem projeto, investigar:

- carga parcial de AF8;
- filtro de deletados no SDB;
- revisao divergente;
- filial divergente;
- projeto tecnico/placeholder vindo do Protheus.

### Divergencia de KPI

Comparar:

```text
soma direta de PmsCustoTarefa
vs.
PmsDashboardSelector.get_context()["kpis"]
```

Se divergir, olhar primeiro:

- filtros aplicados;
- revisao usada;
- filtro de categoria;
- modo carteira vs modo projeto.

### Divergencia temporal

Comparar:

```text
soma PmsCustoTemporalMensal por tarefa
vs.
PmsCustoTarefa por tarefa
```

Se o temporal for menor, causa provavel:

- SC7 sem data financeira valida;
- SD1 sem data financeira valida;
- pedido/recebimento sem vinculo completo.

Se o temporal for maior, tratar como erro.

### Divergencia contra SDB bruto

So investigar quando todos os arquivos PMS obrigatorios estiverem disponiveis localmente ou no spool.

Nao inventar comparacao manual se os SDBs nao estiverem completos.

## 21. Cuidados antes de alterar o dashboard

Antes de alterar calculos:

1. Rodar `validar_dashboard_pms`.
2. Confirmar se a divergencia vem do dado, do ETL, do selector ou do template.
3. Validar projeto unico e carteira.
4. Validar multiplas revisoes.
5. Validar filtro de categoria.
6. Validar serie temporal.
7. Nao usar `atualizado_em` como data financeira.
8. Nao alterar a tabela principal sem aprovacao especifica.
9. Nao mascarar custo sem empenho.
10. Nao somar revisoes sem regra explicita de negocio.

## 22. Checklist de manutencao

Antes de publicar mudancas:

- [ ] Rodar `python manage.py check`.
- [ ] Rodar `python manage.py validar_dashboard_pms --sample-size 5`.
- [ ] Rodar teste especifico de `compras`, se disponivel.
- [ ] Testar dashboard com nenhum projeto selecionado.
- [ ] Testar dashboard com um projeto selecionado.
- [ ] Testar dashboard com multiplos projetos selecionados.
- [ ] Testar filtro de categoria.
- [ ] Testar paginacao preservando querystring.
- [ ] Verificar se os graficos renderizam sem erro de JavaScript.
- [ ] Verificar se Choices.js continua funcionando.
- [ ] Verificar se Alpine.js continua abrindo/fechando a tabela hierarquica.
- [ ] Confirmar que a tabela principal nao foi alterada sem aprovacao.
- [ ] Registrar achados de dados antes de propor correcao.

## Resultado da primeira validacao local

Comando executado:

```powershell
validar_dashboard_pms --sample-size 2
```

Resultado:

```text
Status final: ERRO
Projetos amostrados: JP010125, MO190625
Itens OK: 864
Alertas: 4
Divergencias criticas: 3
```

Divergencias criticas:

- 1275 custos sem projeto PMS correspondente.
- 108 custos com EDT inexistente.
- 651 EDTs sem projeto PMS correspondente.

Alertas:

- 108 tarefas sem EDT valida.
- 1 projeto sem custos materializados.
- 25 projetos com multiplas revisoes em `PmsCustoTarefa`; o selector deve considerar apenas a maior revisao por projeto em modo carteira.
- validacao contra SDB bruto limitada por arquivos ausentes.

Esses achados nao foram corrigidos automaticamente.
