# Changelog

## 1.0.2

### Corrigido
- Saldo e valores das transações agora usam `BIGINT` (migração `0002_bigint_amounts`). Com `INTEGER` (32 bits), o PostgreSQL rejeitava saldos acima de ~R$ 21,4 milhões e a API respondia erro 500.
- Cadastro compara o e-mail sempre em minúsculas, igual ao login e ao banco.
- `CORS_ORIGINS` agora aceita explicitamente lista separada por vírgula ou lista JSON (`NoDecode`; exige `pydantic-settings>=2.7`).

### Segurança
- O ambiente padrão passou a ser `production` (falha fechada): sem `ENVIRONMENT` definido, a aplicação exige uma `SECRET_KEY` forte.
- O login verifica um hash descartável quando o e-mail não existe, equalizando o tempo de resposta.
- A porta do PostgreSQL no Compose é exposta só para `127.0.0.1`.
- A imagem Docker não inclui mais pytest, httpx nem pytest-cov (`requirements-dev.txt`).

### Alterado
- O Compose monta o `DATABASE_URL` a partir de `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB`.
- `/transfers` passou a ter `response_model` (`TransferOut`) e `get_current_account` usa `select()`.
- `.gitignore` ignora `*.db`; adicionado `HEALTHCHECK` ao Dockerfile.
- README sem textos de rascunho, com tabela de variáveis de ambiente.

### Testes e CI
- Novos testes: tokens inválidos, limites por operação, saldo acima de 32 bits, validação de cadastro, e-mail sem diferenciar maiúsculas, filtros de data do extrato, direção das transferências, tipos `BIGINT` e cabeça única das migrações.
- Testes herméticos: não dependem do `.env` do desenvolvedor.
- Novo job de CI que aplica as migrações em um PostgreSQL real.

## 1.0.1
- Versão inicial enviada para revisão.
