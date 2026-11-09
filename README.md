# Mini Bank API

[![CI](https://github.com/IsaiasFernando/mini-bank-api/actions/workflows/ci.yml/badge.svg)](https://github.com/IsaiasFernando/mini-bank-api/actions/workflows/ci.yml) ![Python](https://img.shields.io/badge/Python-3.12-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791) ![License](https://img.shields.io/badge/license-MIT-green)

API REST educacional de banco digital desenvolvida com **Python, FastAPI e PostgreSQL**, com autenticação JWT, operações bancárias, extrato paginado, testes automatizados e execução em containers.

> **Aviso:** projeto demonstrativo para portfólio e aprendizado. Não movimenta dinheiro real e não deve ser utilizado como sistema financeiro de produção.

## Funcionalidades

- Cadastro de usuário com criação automática de conta.
- Login com JWT e senha armazenada usando Argon2.
- Consulta de perfil e saldo.
- Depósito, saque e transferência entre contas.
- Extrato com filtros por data e paginação.
- Validação de regras de negócio e saldo não negativo.
- Rate limit no login e CORS configurável.
- Documentação interativa com Swagger UI.
- Testes automatizados e pipeline CI no GitHub Actions.

## Stack

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 · PostgreSQL 16 · Alembic · PyJWT · Argon2 · SlowAPI · Pytest · Docker Compose · GitHub Actions.

## Executar com Docker

1. Clone o repositório e entre na pasta:

   ```bash
   git clone https://github.com/IsaiasFernando/mini-bank-api.git
   cd mini-bank-api
   ```
2. Crie suas variáveis locais:

   ```bash
   cp .env.example .env
   ```

   Edite `SECRET_KEY` (gere uma chave forte com `python -c "import secrets; print(secrets.token_urlsafe(48))"`) e, se quiser, `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB`. O Compose monta o `DATABASE_URL` da API a partir dessas variáveis, então banco e API nunca ficam com credenciais diferentes.
3. Suba a aplicação:

   ```bash
   docker compose up --build
   ```

A API ficará em `http://localhost:8000`; Swagger em `http://localhost:8000/docs`; ReDoc em `http://localhost:8000/redoc`.

## Executar localmente (sem Docker)

Requer Python 3.12. Copie o `.env.example` para `.env` (ele já traz `ENVIRONMENT=development`). Sem `DATABASE_URL`, a API usa um arquivo SQLite local; para usar o PostgreSQL do Compose, suba só o banco com `docker compose up db` e descomente a linha `DATABASE_URL` do `.env` (host `localhost`).

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `ENVIRONMENT` | `production` | Use `development` apenas localmente. Em qualquer outro valor, a API exige `SECRET_KEY` forte. |
| `SECRET_KEY` | chave de exemplo | Segredo do JWT (mínimo de 32 caracteres fora do ambiente local). |
| `DATABASE_URL` | SQLite local | String de conexão do banco. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Validade do token. |
| `CORS_ORIGINS` | `http://localhost:3000` | Origens permitidas, separadas por vírgula (ou lista JSON). |
| `MAX_TRANSACTION_CENTS` | `100000000` | Limite por operação (R$ 1.000.000,00). |
| `RATE_LIMIT_LOGIN` | `5/minute` | Limite de tentativas de login por IP. |

## Endpoints

| Método | Endpoint | Descrição | Autenticação |
|---|---|---|---|
| GET | `/health` | Status da API | Não |
| POST | `/auth/register` | Cadastro e abertura de conta | Não |
| POST | `/auth/login` | Login e emissão JWT | Não |
| GET | `/users/me` | Perfil do usuário | Sim |
| GET | `/accounts/me` | Saldo e número da conta | Sim |
| POST | `/accounts/me/deposit` | Depósito em centavos | Sim |
| POST | `/accounts/me/withdraw` | Saque em centavos | Sim |
| POST | `/transfers` | Transferência por número da conta | Sim |
| GET | `/accounts/me/statement` | Extrato com filtros e paginação | Sim |

### Exemplo de cadastro

```json
{
  "name": "Maria Silva",
  "email": "maria@example.com",
  "password": "SenhaForte123"
}
```

### Exemplo de depósito

```json
{
  "amount_cents": 15000
}
```

Os valores são enviados em centavos: `15000` representa R$ 150,00. A API não utiliza `float` para representar dinheiro.

### Documentação interativa (Swagger UI)

Com a API em execução, a documentação interativa fica em [`http://localhost:8000/docs`](http://localhost:8000/docs) (e a versão ReDoc em `/redoc`).

Para gerar capturas de tela do Swagger (opcional), com a API rodando:

```bash
pip install playwright
playwright install chromium
python scripts/capture_swagger.py   # salva as imagens em docs/images/
```

### Autenticação no Swagger

1. Execute `POST /auth/register`.
2. Faça login em `POST /auth/login` usando `username` (e-mail) e senha no formulário OAuth2.
3. Copie o `access_token` e clique em **Authorize**.
4. Informe o token conforme solicitado pelo Swagger e teste as rotas protegidas.

## Testes

Os testes usam SQLite em memória para execução rápida e isolada, e não dependem do seu `.env`. A execução de produção utiliza PostgreSQL; por isso o CI também aplica as migrações (`upgrade`, `downgrade` e `upgrade`) em um PostgreSQL real.

```bash
pytest -v
pytest -v --cov=app --cov-report=term-missing
```

## Decisões técnicas

- **Dinheiro em centavos:** evita imprecisão de ponto flutuante. As colunas usam `BIGINT`, pois `INTEGER` (32 bits) estouraria em saldos acima de ~R$ 21 milhões.
- **Camada de serviços:** regras bancárias ficam em `app/services`, separadas dos endpoints.
- **Transação atômica:** transferência debita e credita dentro da mesma transação de banco; em caso de falha, ocorre rollback.
- **Lock de linha:** operações de saldo usam `SELECT ... FOR UPDATE`; a transferência bloqueia as duas contas em ordem crescente de ID para reduzir deadlocks no PostgreSQL.
- **Integridade no banco:** saldo não pode ficar negativo e e-mail/número de conta são únicos.
- **Migrações versionadas:** Alembic controla a evolução do schema.

> Observação: SQLite não implementa o mesmo comportamento de `SELECT FOR UPDATE` do PostgreSQL. Os testes automatizados validam regras e fluxos funcionais; a garantia de concorrência deve ser validada em ambiente PostgreSQL.

## Decisões de segurança

- Senhas armazenadas com hash Argon2; nunca em texto puro.
- JWT assinado com segredo configurável e expiração.
- Falha fechada: o ambiente padrão é `production`. Fora de `development`/`test`, a aplicação recusa iniciar com a chave padrão, de exemplo ou com menos de 32 caracteres.
- Login inválido não revela se o e-mail existe: a mensagem é a mesma e o tempo de resposta é equivalente (um hash descartável é verificado quando o e-mail não existe).
- E-mails são tratados sem diferenciar maiúsculas de minúsculas.
- Limite de tentativas no login via SlowAPI.
- CORS configurável por variável de ambiente.
- Validação de payloads e limites de tamanho/valor.
- Container executa a API com usuário não-root e a imagem de produção não inclui dependências de teste.
- A porta do PostgreSQL no Compose é exposta apenas para `127.0.0.1`.
- Segredos locais ficam no `.env`, ignorado pelo Git.

Antes de qualquer implantação pública, gere um `SECRET_KEY` forte, configure CORS para domínios confiáveis, use HTTPS, defina credenciais seguras no banco, configure backups, logs, monitoramento e revisão de segurança. Este projeto não é certificado nem adequado para operações financeiras reais.

## Estrutura

```text
app/
├── core/        # Configurações e segurança
├── db/          # Engine, sessões e Base ORM
├── models/      # Entidades SQLAlchemy
├── schemas/     # Contratos e validação Pydantic
├── routers/     # Endpoints HTTP
├── services/    # Regras de negócio
├── deps.py      # Dependências e autenticação
└── main.py      # Inicialização FastAPI
alembic/         # Migrações do banco
scripts/         # Utilitários (captura de telas do Swagger)
tests/           # Testes automatizados
.github/         # Pipeline CI
CHANGELOG.md     # Histórico de versões
```

## Próximas evoluções

- Idempotência em transferências.
- Logs estruturados e observabilidade.
- Testes de concorrência e de integração executados contra PostgreSQL.
- Lint e formatação automáticos no CI (ruff).
- Deploy de demonstração com dados fictícios.

## Licença

Distribuído sob a licença MIT. Consulte `LICENSE`.

## Autor

**Isaías Fernando**  
[GitHub](https://github.com/IsaiasFernando) · [LinkedIn](https://www.linkedin.com/in/isaias-fernando-17561825a/)
