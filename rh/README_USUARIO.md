# README do Usuário - Módulo RH

## 1. O que é este módulo

O módulo RH reúne as principais rotinas de Recursos Humanos dentro do sistema.

Com ele é possível:

- Ver vagas disponíveis e receber currículos.
- Gerenciar candidatos.
- Solicitar abertura de novas vagas.
- Aprovar ou reprovar solicitações de contratação.
- Enviar pesquisa demissional.
- Enviar formulário admissional para novos colaboradores.
- Acompanhar indicadores de RH.
- Registrar e acompanhar avaliações de desempenho.
- Importar base de funcionários e ponto.

## 2. Quem pode usar

O acesso depende do perfil do usuário:

| Tipo de usuário | O que pode fazer |
|---|---|
| Visitante externo | Ver vagas abertas, enviar currículo, responder pesquisa ou formulário quando tiver link. |
| Usuário logado | Solicitar abertura de vaga e ver avaliações permitidas para seu perfil. |
| RH | Acessar gestão de vagas, triagem, pesquisas, formulários admissionais, dashboard e importações. |
| Gestor | Criar e acompanhar avaliações dos colaboradores dos setores que gerencia. |
| Colaborador | Ver suas avaliações e registrar ciência quando disponível. |
| TI/Diretoria | Podem ter acesso amplo conforme regra do sistema. |

Quando uma tela não aparecer no menu ou o sistema negar acesso, o usuário deve solicitar revisão de permissão ao TI ou ao RH.

## 3. Como acessar

No menu lateral do sistema, acesse **Recursos Humanos**.

As opções encontradas no código atual são:

- **Dashboard RH**
- **Portal de Vagas**
- **Gestão de Vagas**
- **Triagem (CVs)**
- **Formulário Admissional**
- **Solicitar Contratação**
- **Aprovações**
- **Pesquisa Demissional**
- **Listar Avaliações**
- **Nova Avaliação**
- **Dashboard Geral**

Algumas opções aparecem apenas para quem tem permissão.

## 4. Explicação das telas

### Dashboard RH

Mostra indicadores gerais:

- Funcionários ativos.
- Admissões.
- Desligamentos.
- Turnover.
- Vagas abertas.
- Currículos recebidos.
- Candidatos em processo.
- Contratados.
- Horas de falta e horas extras.

Também possui botões para importar base de funcionários e importar ponto, quando disponíveis.

### Portal de Vagas

Mostra as vagas abertas para candidatura.

Em cada vaga, o candidato pode clicar em **Aplicar** para enviar seus dados e currículo.

### Gestão de Vagas

Tela usada pelo RH para:

- Ver vagas abertas e fechadas.
- Criar nova vaga.
- Editar vaga existente.
- Ver quantidade de candidatos por vaga.
- Acessar candidatos vinculados a uma vaga.

### Triagem (CVs)

Tela usada pelo RH para acompanhar candidaturas.

Permite:

- Filtrar por vaga.
- Ver candidatos novos, em análise e em entrevista.
- Abrir o detalhe do candidato.

### Detalhe do Candidato

Mostra:

- Dados do candidato.
- Vaga desejada.
- Link para currículo.
- Status do processo.
- Campo de observações internas do RH.

O RH pode mudar o status do candidato e salvar.

### Solicitar Contratação

Tela para solicitar abertura de uma vaga.

O usuário informa cargo, departamento, motivo da contratação, quantidade de vagas, data prevista e informações sobre o perfil desejado.

### Aprovações

Tela do RH para analisar solicitações de contratação.

O RH pode registrar parecer e alterar o status para aprovada ou reprovada.

Após aprovar, o código atual orienta o RH a publicar a vaga manualmente na **Gestão de Vagas**.

### Pesquisa Demissional

Tela usada pelo RH para gerar links de pesquisa para ex-colaboradores.

Também permite listar pesquisas e exportar CSV com respostas.

### Formulário Admissional

Tela usada pelo RH para:

- Gerar link de formulário para novo colaborador.
- Ver formulários pendentes e respondidos.
- Abrir detalhes.
- Exportar CSV.
- Gerar PDF de formulários respondidos.

### Avaliações de Desempenho

Permite listar, criar, editar, visualizar e dar ciência em avaliações.

Dependendo do perfil:

- RH/Diretoria/TI podem ter visão geral.
- Gestores veem colaboradores de seus setores.
- Colaboradores veem suas próprias avaliações.

## 5. Como cadastrar um novo registro

### Criar uma vaga

1. Acesse **Recursos Humanos > Gestão de Vagas**.
2. Clique em **Nova Vaga**.
3. Preencha título, setor, descrição e requisitos.
4. Marque se a vaga está ativa.
5. Clique em salvar.

Depois de salva, se estiver ativa, a vaga aparece no Portal de Vagas.

### Solicitar contratação

1. Acesse **Recursos Humanos > Solicitar Contratação**.
2. Preencha seus dados e os dados da vaga.
3. Informe a data prevista de início.
4. Se for substituição, informe o nome da pessoa substituída.
5. Clique em enviar.

A solicitação será enviada para análise do RH.

Atenção: a data prevista de início deve ser uma segunda-feira.

### Gerar pesquisa demissional

1. Acesse **Recursos Humanos > Pesquisa Demissional**.
2. Clique em gerar nova pesquisa.
3. Preencha nome do ex-colaborador, setor, tipo de demissão, período de saída e tempo de casa.
4. Salve.
5. Copie o link gerado e envie ao ex-colaborador.

### Gerar formulário admissional

1. Acesse **Recursos Humanos > Formulário Admissional**.
2. Clique em gerar novo formulário.
3. Informe o nome do futuro colaborador.
4. Salve.
5. Copie o link gerado e envie ao candidato.

### Criar avaliação de desempenho

1. Acesse **Recursos Humanos > Nova Avaliação**.
2. Selecione o colaborador.
3. Informe ano e ciclo.
4. Preencha as notas das competências.
5. Adicione comentários, se necessário.
6. Salve.

## 6. Como editar um registro

### Editar vaga

1. Acesse **Gestão de Vagas**.
2. Localize a vaga.
3. Clique na ação de editar.
4. Ajuste os dados.
5. Salve.

### Editar candidatura

1. Acesse **Triagem (CVs)**.
2. Abra o candidato.
3. Altere o status.
4. Preencha ou ajuste as observações.
5. Salve.

### Editar avaliação

A edição aparece somente quando o usuário tem permissão.

No código atual, a avaliação não pode ser editada por gestor quando gestor e colaborador já deram ciência.

## 7. Como excluir ou cancelar

Não foi identificada no código atual uma tela de exclusão direta para vagas, candidaturas, solicitações, pesquisas, formulários ou avaliações.

Alternativas existentes:

- Vaga pode ser fechada/desativada pelo campo **ativa**.
- Solicitação pode ser reprovada/cancelada pelo RH.
- Candidatura pode mudar para reprovada/banco de talentos.
- Avaliação possui status `Cancelada`, mas não foi identificada uma ação específica de cancelamento na interface atual.

Antes de cancelar ou reprovar algo, revise os dados e confirme se a ação está correta.

## 8. Como acompanhar status ou etapas

### Candidatura

Status encontrados:

- **Novo**: currículo recebido e aguardando triagem.
- **Em Análise**: RH está avaliando o candidato.
- **Em Fase de Entrevista**: candidato avançou para entrevista.
- **Aprovado**: candidato contratado.
- **Reprovado / Banco de Talentos**: candidato não avançou ou ficará registrado para futuras vagas.

### Solicitação de vaga

Status encontrados:

- **Pendente**: aguardando análise do RH.
- **Aprovada**: RH aprovou a solicitação.
- **Reprovada / Cancelada**: solicitação não seguirá.

### Pesquisa demissional

Status simples:

- **Pendente**: link ainda não foi respondido.
- **Respondida**: ex-colaborador já enviou a pesquisa.

### Formulário admissional

Status simples:

- **Pendente**: candidato ainda não respondeu.
- **Respondido**: candidato enviou os dados.

### Avaliação de desempenho

Status encontrados:

- **Rascunho**: avaliação em preparação.
- **Finalizada**: avaliação concluída, aguardando ciência.
- **Ciência Pendente**: ainda sem ciência.
- **Ciência Parcial**: gestor ou colaborador já deu ciência, mas não ambos.
- **Ciência Concluída**: gestor e colaborador deram ciência.
- **Cancelada**: avaliação cancelada.

## 9. Como gerar PDF, relatório ou exportação

### Pesquisa demissional

Na lista de pesquisas, use a opção de exportação CSV quando disponível.

O CSV inclui respostas de pesquisas respondidas, como motivo de saída e notas.

### Formulário admissional

Na lista de formulários:

1. Abra o detalhe de um formulário respondido.
2. Clique em gerar PDF.

O PDF inclui dados pessoais, contatos, documentos, dependentes, uniforme, vale-transporte, LGPD e dados de controle.

Também existe exportação CSV na listagem de formulários.

### Avaliação de desempenho

Na avaliação ou dashboard individual, use a opção de PDF.

O PDF inclui:

- Dados do colaborador.
- Período da avaliação.
- Notas por competência.
- Histórico comparativo.
- Comentários.
- Ciência do gestor e do colaborador.

Na listagem, existe exportação CSV das avaliações.

### Dashboard RH

O dashboard possui botão de impressão no template atual.

## 10. Erros comuns e como resolver

| Mensagem/situação | Possível causa | O que fazer |
|---|---|---|
| Você não possui permissão | Usuário sem grupo ou perfil adequado. | Solicite revisão ao TI/RH. |
| Formato inválido. Envie Excel | Arquivo de base não é `.xls` ou `.xlsx`. | Envie arquivo no formato correto. |
| Formato inválido. Envie CSV | Arquivo de ponto não é `.csv`. | Gere novamente o arquivo em CSV. |
| Selecione o arquivo e a data de referência | Faltou arquivo ou data na importação de ponto. | Preencha ambos os campos. |
| CPF deve conter exatamente 11 dígitos | CPF incompleto ou com letras. | Digite somente números. |
| CEP deve conter exatamente 8 dígitos | CEP incompleto. | Digite somente os 8 números. |
| PIS deve conter exatamente 11 dígitos | PIS incompleto. | Digite somente números. |
| Telefone para recado igual ao principal | Os dois telefones são iguais. | Informe um telefone de recado diferente. |
| Informe o trajeto caso utilize vale transporte | Marcou vale-transporte como Sim e não preencheu trajeto. | Informe linhas, terminais ou percurso. |
| Formulário indisponível | Link já foi respondido. | Em caso de erro, acione o RH. |
| Pesquisa indisponível | Link já foi respondido. | Em caso de erro, acione o RH. |
| Já existe avaliação para usuário, ano e ciclo | Tentativa de duplicar avaliação. | Localize a avaliação existente. |

Acione o TI quando:

- O menu esperado não aparecer.
- O arquivo de importação estiver correto e o erro persistir.
- Um link público não abrir.
- Um PDF ou CSV não for gerado.

## 11. Boas práticas de uso

- Revise os dados antes de salvar.
- Em vagas, mantenha descrição e requisitos claros.
- Em solicitações, escolha uma segunda-feira para data prevista de início.
- Em candidaturas, mantenha observações objetivas e profissionais.
- Em formulários admissionais, confira CPF, PIS, CEP e telefones.
- Só envie link admissional ao candidato correto.
- Não compartilhe links de pesquisa ou formulário em canais públicos.
- Antes de importar arquivos, confira se as colunas estão no padrão esperado.
- Em avaliações, preencha notas com cuidado e use comentários para dar contexto.
- Registre ciência apenas depois de revisar a avaliação.

## 12. Dúvidas frequentes

### Posso responder o formulário admissional mais de uma vez?

Não. O link é bloqueado depois do envio.

### Posso responder a pesquisa demissional mais de uma vez?

Não. O link só aceita uma resposta.

### A aprovação de uma solicitação cria a vaga automaticamente?

Não identificado no código atual. Após aprovar, o RH deve publicar a vaga na Gestão de Vagas.

### Por que não vejo o botão de Nova Avaliação?

Você pode não ter permissão para criar avaliações. Essa opção depende do seu perfil.

### Quem pode dar ciência na avaliação?

O gestor autorizado pode dar ciência como gestor. O colaborador só pode dar ciência na própria avaliação.

### Posso excluir uma vaga?

Não foi identificada exclusão pela interface atual. Use a opção de fechar/desativar a vaga.

### O que fazer se o candidato informou dados errados no formulário admissional?

Como o link fica bloqueado após resposta, acione o RH/TI para orientar a correção.

### O currículo pode ser em qualquer formato?

Não. O código aceita apenas PDF, DOC ou DOCX, com limite de 3 MB.

### O que entra no PDF admissional?

Dados informados pelo candidato: dados pessoais, documentos, contatos, dependentes, uniforme, vale-transporte e consentimento LGPD.

### O que entra no PDF de avaliação?

Dados do colaborador, notas por competência, média, classificação, histórico, comentários e ciências digitais.
