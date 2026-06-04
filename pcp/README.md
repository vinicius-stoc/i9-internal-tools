# Modulo PCP

## Arquitetura

O modulo segue um monolito modular Django:

- `models.py`: persistencia, relacionamentos e invariantes de banco.
- `services/`: comandos e regras de negocio transacionais.
- `selectors/`: consultas otimizadas para API e dashboard.
- `api/`: filtros, serializacao, permissoes e transporte HTTP.
- `tasks.py`: adaptadores Celery idempotentes.

Views, endpoints e tasks nao devem alterar models diretamente quando existir um service para a operacao.

## Invariantes principais

- Models principais utilizam soft delete por meio do campo `ativo`.
- Um ativo pode possuir apenas um downtime aberto.
- Um ativo pode possuir apenas uma execucao de manutencao aberta.
- Um plano pode possuir apenas uma programacao pendente.
- Programacoes atrasadas sao identificadas pela data prevista; o atraso nao e persistido como status.
- Movimentacoes de estoque sao unicas por filial, produto, data, tipo, origem, documento e CF.
- Alertas utilizam registro de envio para evitar duplicidade concorrente.

As invariantes criticas sao garantidas por constraints PostgreSQL e complementadas por services transacionais.

## Autorizacao

- Dashboard: grupos `PCP`, `TI`, `Diretoria` ou superusuario.
- API operacional: grupos `PCP`, `TI`, `Diretoria` ou superusuario.
- API Power BI: header `Authorization: Api-Key <token>`, configurado por `POWER_BI_API_KEY`.

## Tarefas Celery

- `pcp.run_pcp_estoque_etl`
- `pcp.recalcular_preventivas`
- `pcp.enviar_alertas_preventivas`
- `pcp.enviar_alertas_downtime_aberto`

As tasks utilizam retry com backoff. Como `CELERY_TASK_ACKS_LATE` esta habilitado, toda nova task do PCP deve ser idempotente.

## Validacao

Antes do deploy:

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test pcp
```

O workflow de deploy executa essas validacoes em SQLite antes de atualizar o PythonAnywhere. As migrations de producao continuam destinadas ao PostgreSQL 12.

Para reiniciar os workers Celery apos o deploy, configure o secret `PA_ALWAYS_ON_TASK_IDS` no GitHub com os IDs das Always-on Tasks separados por virgula.
