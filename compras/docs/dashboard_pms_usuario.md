# Dashboard Financeiro PMS de Compras - Guia do usuario

## 1. O que e o dashboard

O Dashboard Financeiro PMS de Compras mostra a situacao financeira dos projetos PMS acompanhados pela area de Compras.

Ele organiza os valores por projeto, EDT/WBS e tarefa, permitindo comparar o que ja foi realizado como custo, o que esta empenhado em pedidos de compra e onde existem pontos que precisam de investigacao.

## 2. Para que ele serve

O dashboard serve para apoiar decisoes como:

- identificar projetos com maior custo;
- acompanhar quanto do empenhado ja virou custo;
- encontrar custo sem empenho;
- verificar fases criticas do projeto;
- priorizar analises pelo maior impacto financeiro;
- acompanhar a evolucao mensal dos gastos.

## 3. Quando usar

Use o dashboard quando precisar:

- revisar a carteira de projetos PMS;
- analisar um projeto especifico;
- preparar reuniao gerencial;
- investigar divergencia entre custo e empenho;
- priorizar quais projetos ou EDTs precisam de analise;
- verificar tendencia de gasto ao longo dos meses.

## 4. Como filtrar projetos

O filtro de projeto permite selecionar nenhum, um ou varios projetos.

### Nenhum projeto selecionado

Mostra a carteira completa.

Use para ter uma visao geral de todos os projetos.

### Um projeto selecionado

Mostra a visao detalhada de um unico projeto.

Nesse modo, a tabela principal de EDT/WBS e tarefas fica disponivel.

### Varios projetos selecionados

Mostra uma carteira filtrada com apenas os projetos escolhidos.

Use para comparar um grupo de projetos especifico.

## 5. Como interpretar os cards principais

### Custo

Mostra o valor que ja virou custo realizado.

Esse valor vem dos recebimentos e notas de entrada vinculados aos projetos PMS.

Use para entender quanto ja foi efetivamente consumido no projeto ou carteira filtrada.

Exige atencao quando:

- o valor estiver muito acima do esperado;
- houver crescimento rapido;
- estiver concentrado em poucos projetos ou EDTs.

### Empenhado

Mostra o valor comprometido em pedidos de compra.

Representa o que ja foi comprado ou comprometido, mesmo que ainda nao tenha virado custo realizado.

Use para comparar o que esta comprometido contra o que ja foi realizado.

### Saldo do Empenho

Mostra a diferenca entre empenhado e custo realizado.

Formula simples:

```text
Empenhado - Custo
```

Interpretacao:

- saldo positivo: ainda existe empenho em aberto;
- saldo zero: o empenhado foi totalmente convertido em custo;
- saldo negativo: o custo passou do valor empenhado.

Saldo negativo deve ser investigado.

### % Convertido em Custo

Mostra quanto do empenhado ja virou custo.

Formula simples:

```text
Custo / Empenhado * 100
```

Interpretacao:

- percentual baixo: existe empenho ainda nao realizado;
- percentual proximo de 100%: o empenho esta quase todo convertido em custo;
- percentual acima de 100%: o custo passou do empenhado.

### Custo sem Empenho

Mostra custo realizado sem empenho correspondente no dashboard.

Esse e um dos principais alertas da tela.

Pode indicar:

- lancamento fora do fluxo esperado;
- pedido nao localizado;
- falha de vinculo;
- classificacao incorreta;
- dados incompletos na origem.

Quando for maior que zero, deve ser investigado.

## 6. Como interpretar os cards executivos

### Media por Projeto

Mostra o custo medio dos projetos no escopo filtrado.

Use como referencia geral de custo da carteira.

### Mediana por Projeto

Mostra o valor central dos custos dos projetos.

E util porque reduz o efeito de projetos muito grandes ou muito pequenos.

Se a media estiver muito maior que a mediana, pode existir concentracao de custo em poucos projetos.

### Maior Custo

Mostra o projeto com maior custo realizado no escopo filtrado.

Use para saber qual projeto deve receber a primeira analise financeira.

### Maior % Acima do Empenho

Mostra o projeto com maior percentual de custo acima do empenhado.

Use para identificar onde o custo esta superando o valor comprometido em pedidos.

### Fora da Curva

Mostra quantos projetos estao acima da mediana de custo e tambem acima do empenho.

Use como alerta de projetos que podem precisar de revisao gerencial.

## 7. Como interpretar os graficos

### Custo x Empenhado

Compara o custo realizado com o valor empenhado.

Use para entender se o escopo filtrado esta mais realizado, mais comprometido ou acima do empenho.

Ponto de atencao:

- custo maior que empenhado indica possivel estouro ou falta de vinculo correto.

### Top 10 Projetos por Custo

Aparece quando a tela esta em modo carteira.

Mostra os 10 projetos com maior custo realizado.

Use para priorizar analises pelos projetos de maior impacto financeiro.

### Top 10 EDT/WBS por Custo

Aparece quando a tela esta em modo projeto.

Mostra as EDTs/WBS com maior custo dentro do projeto selecionado.

Use para descobrir qual fase, pacote ou estrutura do projeto concentra mais gasto.

### Top 10 Tarefas por Custo

Mostra as tarefas com maior custo realizado.

Use para ir ao nivel mais detalhado da analise.

### Eficiencia: Volume x Custo Realizado

Mostra a relacao entre volume do projeto e custo realizado.

O volume usa o custo previsto quando disponivel. Quando nao ha custo previsto, usa quantidade de tarefas ou EDTs como referencia.

Interpretacao:

- ponto mais alto: projeto com maior custo;
- ponto mais a direita: projeto com maior volume;
- ponto destacado como alerta: projeto acima da media de custo.

Esse grafico ajuda a encontrar projetos que parecem caros em relacao ao volume.

### Matriz de Risco Financeiro

Mostra os projetos em quadrantes de risco.

Eixo horizontal:

- custo realizado.

Eixo vertical:

- percentual acima do empenho.

Interpretacao:

- alto custo e acima do empenho: prioridade maxima de analise;
- alto custo dentro do empenho: acompanhar, mas sem alerta imediato de estouro;
- baixo custo acima do empenho: investigar vinculo ou lancamento;
- baixo custo dentro do empenho: menor prioridade.

### Tendencia Temporal Financeira

Mostra a evolucao mensal de custo realizado e empenhado.

Use para acompanhar:

- crescimento mensal;
- picos de gasto;
- comparacao entre empenho e realizacao;
- tendencia pela media movel de 3 meses.

Ponto de atencao:

- a tendencia depende das datas financeiras do Protheus.

### Pareto

O Pareto mostra quais itens concentram a maior parte do custo.

Existem tres visoes:

- Pareto Projetos;
- Pareto EDT/WBS;
- Pareto Tarefas.

Use para responder:

```text
Quais poucos itens explicam a maior parte do custo?
```

Priorize a analise pelos primeiros itens do Pareto.

### EDTs Criticas por Consumo

Mostra as EDTs com maior custo realizado.

Campos principais:

- projeto;
- EDT/WBS;
- descricao;
- custo;
- empenhado;
- percentual no total;
- burn rate.

Use para identificar as fases do projeto que mais consomem recurso.

## 8. Como interpretar a tabela principal

A tabela principal aparece quando um unico projeto e selecionado.

Ela mostra a estrutura financeira por:

```text
EDT/WBS > Tarefa
```

Cada linha mostra:

- codigo da estrutura ou tarefa;
- descricao;
- custo;
- empenhado;
- saldo do empenho;
- percentual convertido em custo;
- situacao financeira.

### Situacoes financeiras

#### Custo sem empenho

Existe custo realizado, mas nao existe empenho correspondente.

Deve ser investigado.

#### Custo acima do empenho

O custo realizado passou do valor empenhado.

Deve ser tratado como alerta financeiro.

#### Totalmente realizado

O custo realizado e igual ao empenhado.

Indica que o empenho foi convertido totalmente em custo.

#### Em aberto

Existe empenho maior que o custo realizado.

Indica que ainda ha valor comprometido nao realizado.

#### Sem movimentacao

Nao ha custo nem empenho para a linha.

## 9. Exemplos de decisoes

### Identificar projeto com gasto alto

Use:

- card Maior Custo;
- Top 10 Projetos;
- Pareto Projetos.

Acao:

- abrir o projeto;
- verificar EDTs de maior consumo;
- avaliar se o gasto esta dentro do esperado.

### Identificar fase critica

Use:

- Top 10 EDT/WBS;
- EDTs Criticas por Consumo;
- tabela principal.

Acao:

- localizar a EDT;
- verificar tarefas vinculadas;
- analisar se o custo esta coerente com o andamento.

### Identificar custo sem empenho

Use:

- card Custo sem Empenho;
- tabela principal;
- situacao financeira das linhas.

Acao:

- investigar pedido, nota, vinculo PMS e classificacao.

### Identificar projeto fora da curva

Use:

- card Fora da Curva;
- grafico de Eficiencia;
- Matriz de Risco.

Acao:

- priorizar projetos com alto custo e custo acima do empenho.

### Acompanhar tendencia de gasto

Use:

- Tendencia Temporal Financeira.

Acao:

- avaliar meses de pico;
- verificar crescimento recorrente;
- cruzar com compras, recebimentos e fases do projeto.

### Priorizar analise por Pareto

Use:

- Pareto Projetos;
- Pareto EDT/WBS;
- Pareto Tarefas.

Acao:

- investigar primeiro os itens que mais explicam o custo acumulado.

## 10. Cuidados importantes

### O dashboard depende da ultima sincronizacao

Os dados refletem a ultima carga PMS registrada.

Antes de tomar decisao, confira a data e o status da ultima sincronizacao.

### Os dados vem do Protheus

Se houver erro de cadastro, vinculo, data ou classificacao no Protheus, o dashboard pode refletir essa inconsistencia.

### Empenhado nao e custo realizado

Empenhado representa valor comprometido em pedido.

Custo realizado representa recebimento ou nota ja reconhecida como custo.

### Custo sem empenho deve ser investigado

Esse indicador nao deve ser ignorado.

Ele pode apontar falha de processo, vinculo ou dado de origem.

### Tendencia temporal depende de datas financeiras

Se pedidos ou notas estiverem sem data financeira valida, a serie temporal pode ficar incompleta.

### Revisoes de projeto exigem cuidado

Quando o mesmo projeto possui mais de uma revisao, os totais precisam ser analisados com atencao.

O dashboard considera a revisao mais recente disponivel para cada projeto.

Em caso de duvida, validar com TI antes de usar o numero em reuniao executiva.

## 11. Glossario simples

### Projeto

Obra, contrato ou iniciativa controlada no PMS.

### EDT/WBS

Estrutura que organiza o projeto em fases, pacotes ou grupos de trabalho.

### Tarefa

Item detalhado dentro da EDT/WBS.

### Custo previsto

Valor planejado para o projeto ou tarefa.

### Empenhado

Valor comprometido em pedido de compra.

### Custo realizado

Valor que ja virou custo efetivo por recebimento ou nota.

### Saldo

Diferenca entre valores, normalmente entre empenhado e custo realizado.

### Burn rate

Ritmo medio de consumo financeiro em determinado periodo.

### Pareto

Analise que mostra quais poucos itens concentram a maior parte do custo.

### Fora da curva

Projeto com comportamento acima do padrao da carteira, geralmente por custo alto e estouro em relacao ao empenho.

## 12. Leitura recomendada da tela

Sequencia pratica:

1. Confira a ultima sincronizacao.
2. Selecione o projeto ou carteira.
3. Leia os cards principais.
4. Verifique se existe custo sem empenho.
5. Veja o Top 10 ou Pareto para priorizar.
6. Abra a tabela do projeto quando precisar detalhar EDT e tarefa.
7. Use a tendencia temporal para entender evolucao mensal.
8. Investigue primeiro alto custo, custo sem empenho e custo acima do empenho.
