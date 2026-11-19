![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT-000000?logo=jsonwebtokens&logoColor=white)
![CI](https://github.com/JohnLouisMaker/deliver-backend/actions/workflows/ci.yml/badge.svg)

# Deliver — Backend

API REST de um sistema de delivery: autenticação JWT, cardápio administrável
com upload de imagem e pedidos com preço calculado no servidor.

**Status:** em desenvolvimento. Autenticação, cardápio e checkout estão
funcionando e cobertos por testes; acompanhamento de status na cozinha está
no roadmap.

**Frontend:** [deliver-frontend](https://github.com/JohnLouisMaker/deliver-frontend)

## Sobre o projeto

O backend concentra as decisões que não podem depender do cliente:

- **Preço nunca vem do frontend.** No checkout, cada item é lido do banco e o
  total é recalculado no servidor; o cliente envia apenas item, tamanho e
  quantidade.
- **Snapshot do item no pedido.** Nome, imagem e preço unitário são copiados
  para `itens_pedidos` no momento da compra — mudar o cardápio depois não
  altera o histórico de pedidos já feitos.
- **Autorização por dono.** Usuário comum só acessa os próprios pedidos;
  admin tem acesso irrestrito. A regra fica na dependência, não em cada rota.
- **Três tipos de token.** `access` (curto), `refresh` (longo) e `reset`
  (exclusivo do fluxo de recuperação de senha), distinguidos pelo campo `type`
  do payload.

## Stack

| Tecnologia          | Uso                                                            |
| ------------------- | -------------------------------------------------------------- |
| FastAPI             | Framework web                                                  |
| SQLAlchemy 2        | ORM e modelagem do banco                                       |
| PostgreSQL          | Banco de dados (hospedado no [Supabase](https://supabase.com)) |
| Alembic             | Migrações do banco                                             |
| python-jose         | Geração e validação de JWT                                     |
| passlib[bcrypt]     | Hash de senhas                                                 |
| fastapi-mail        | Envio de e-mail (recuperação de senha)                         |
| Pydantic            | Validação e serialização dos schemas                           |
| pytest + httpx      | Testes de integração                                           |
| uvicorn             | Servidor ASGI                                                  |

## Como rodar

Pré-requisitos: Python 3.11+ e um PostgreSQL (local, em container ou no
Supabase).

```bash
git clone https://github.com/JohnLouisMaker/deliver-backend.git
cd deliver-backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Crie um `.env` na raiz:

```env
DATABASE_URL=postgresql://usuario:senha@host:5432/postgres
# Opcional: conexão direta (porta 5432) usada apenas pelas migrations
# DATABASE_URL_MIGRATIONS=postgresql://usuario:senha@host:5432/postgres
SECRET_KEY=troque-esta-chave
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE=30           # minutos
REFRESH_TOKEN_EXPIRE=7           # dias

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
EMAIL_FROM=noreply@delivery.com
```

> No Supabase, a connection string fica em `Project Settings → Database`.
> O modo **Transaction Pooler** (porta `6543`) é o recomendado quando a
> aplicação roda em ambiente serverless ou com muitas instâncias.

Aplique as migrações, popule o cardápio e suba o servidor:

```bash
alembic upgrade head
python -m app.seed               # opcional: cardápio inicial
uvicorn app.main:app --reload
```

API em `http://127.0.0.1:8000` e documentação em
`http://127.0.0.1:8000/docs`.

## Docker

```bash
docker build -t deliver-backend .
docker run -p 8000:8000 --env-file .env deliver-backend
```

A imagem parte de `python:3.11-slim` e instala `libpq-dev` para o `psycopg2`.
As variáveis são lidas do `.env` em tempo de execução — a mesma imagem serve
para qualquer ambiente.

## Testes

```bash
pytest -q
```

21 testes de integração, organizados por área:

| Arquivo             | Testes | Cobre                                             |
| ------------------- | ------ | ------------------------------------------------- |
| `test_auth.py`      | 11     | cadastro, login, refresh, rotas protegidas        |
| `test_orders.py`    | 5      | criação de pedido, preço no servidor, autorização |
| `test_products.py`  | 5      | cardápio, categorias e permissão de admin         |

Os testes rodam **contra um PostgreSQL real**, não SQLite: os modelos usam
`Enum`, `Numeric` e `CHECK`, e um banco em memória não reproduziria isso. No
CI, o schema é criado com `alembic upgrade head` antes do pytest — o que
também valida que as migrations aplicam do zero.

## CI

GitHub Actions sobe um **PostgreSQL 16 em service container** com healthcheck,
instala as dependências em Python 3.11 com cache de pip, aplica as migrations
e roda `pytest`. Dispara em push para `main`, `feat/**`, `fix/**`,
`refactor/**` e em pull requests para `main`.

## Endpoints

### Infra — `/health`

| Método | Rota      | Descrição                                     | Auth |
| ------ | --------- | --------------------------------------------- | ---- |
| `GET`  | `/health` | Status da API e conectividade com o banco     | —    |

Responde `200` com `{"status": "ok", "database": "ok"}` quando o banco
responde a um `SELECT 1`; caso contrário responde `503` com
`{"status": "error", "database": "unavailable"}`. Usado como healthcheck
no Railway/Docker.

### Auth — `/auth`

| Método | Rota                      | Descrição                                                     | Auth          |
| ------ | ------------------------- | ------------------------------------------------------------- | ------------- |
| `POST` | `/auth/signup`            | Cadastro de novo usuário                                      | —             |
| `POST` | `/auth/login`             | Login com e-mail e senha (JSON)                               | —             |
| `POST` | `/auth/loginform`         | Login via OAuth2 form (usado pelo Swagger)                    | —             |
| `POST` | `/auth/refresh`           | Renova o access token (refresh token no header)               | Refresh Token |
| `GET`  | `/auth/me`                | Dados do usuário autenticado                                  | Access Token  |
| `PATCH`| `/auth/me`                | Atualiza os dados do usuário autenticado                      | Access Token  |
| `POST` | `/auth/forgot-password`   | Envia código de recuperação por e-mail                        | —             |
| `POST` | `/auth/verify-reset-code` | Valida o código recebido                                      | —             |
| `POST` | `/auth/reset-password`    | Define nova senha com o código                                | —             |

Rotas protegidas esperam `Authorization: Bearer <access_token>`. Quando o
access token expira, a API responde `401` e o cliente renova em
`POST /auth/refresh`, também via header.

### Cardápio — `/cardapio`

| Método   | Rota                          | Descrição                                                    | Permissão |
| -------- | ----------------------------- | ------------------------------------------------------------ | --------- |
| `GET`    | `/cardapio/`                  | Lista itens disponíveis (filtro opcional por `categoria`)     | —         |
| `GET`    | `/cardapio/{item_id}`         | Detalhes de um item                                           | —         |
| `POST`   | `/cardapio/adicionar`         | Cria item, com upload de imagem                               | Admin     |
| `PATCH`  | `/cardapio/editar/{item_id}`  | Atualiza nome, preço e/ou disponibilidade                     | Admin     |
| `DELETE` | `/cardapio/deletar/{item_id}` | Remove o item e a imagem                                      | Admin     |

### Pedidos — `/pedidos`

| Método   | Rota                                          | Descrição                                                          | Permissão     |
| -------- | --------------------------------------------- | ------------------------------------------------------------------ | ------------- |
| `POST`   | `/pedidos`                                    | Checkout: cria o pedido e os itens com snapshot de preço            | Autenticado   |
| `GET`    | `/pedidos/meus_pedidos`                       | Lista os pedidos do usuário autenticado                             | Autenticado   |
| `POST`   | `/pedidos/adicionar_item/{pedido_id}`         | Adiciona item ao pedido; preço lido do banco                        | Dono ou Admin |
| `DELETE` | `/pedidos/remover_item/{pedido_id}/{item_id}` | Remove item do pedido                                               | Dono ou Admin |
| `POST`   | `/pedidos/finalizar/{pedido_id}`              | Finaliza o pedido                                                   | Dono ou Admin |

Contrato completo do checkout (payload, resposta e erros):
[`docs/checkout-api.md`](docs/checkout-api.md).

## Modelo de dados

```
usuario 1---N pedidos 1---N itens_pedidos
itens_cardapio 1---N itens_cardapio_precos_tamanho
itens_cardapio 1---N itens_pedidos   (opcional: item pode ter sido removido)
```

**usuario** — `id`, `nome`, `email` (unique), `senha` (hash bcrypt), `ativo`,
`admin`, `reset_code_hash`, `reset_code_expires_at`, `reset_code_attempts`

**itens_cardapio** — `id`, `nome`, `descricao`, `preco` (para itens de preço
fixo), `categoria` (`PIZZA`, `BEBIDA`, `SOBREMESA`, `LANCHE`,
`ACOMPANHAMENTO`, `OUTROS`), `disponivel`, `imagem_url`

**itens_cardapio_precos_tamanho** — `id`, `item_cardapio_id` (FK, ON DELETE
CASCADE), `tamanho` (`pequena` / `media` / `grande`, com CHECK), `preco`
(CHECK `preco > 0`). Unique em (`item_cardapio_id`, `tamanho`).

**pedidos** — `id`, `usuario_id` (FK), `status` (`Pendente`, `Finalizado`,
`Cancelado`), `preco` (total), `troco_para`

**itens_pedidos** — `id`, `pedido_id` (FK), `item_cardapio_id` (FK, nullable),
`nome_snapshot`, `imagem_url_snapshot`, `sabor`, `tamanho`, `quantidade`,
`preco_unitario` (copiado do cardápio no momento do pedido)

## Migrações

```bash
alembic revision --autogenerate -m "descricao"   # criar
alembic upgrade head                             # aplicar
alembic downgrade -1                             # reverter a última
```

## Estrutura

```
├── alembic/                # Migrações
│   └── versions/
├── app/
│   ├── core/config.py      # Configuração via .env
│   ├── database/           # Engine, SessionLocal e Base
│   ├── models/             # UserModel, PedidoModel, ItemPedidoModel, ItemCardapio
│   ├── routes/             # auth_routes, order_routes, product_routes
│   ├── schemas/            # Schemas Pydantic
│   ├── dependencies.py     # Injeção de dependências e autorização
│   ├── security.py         # bcrypt e OAuth2
│   ├── seed.py             # Cardápio inicial
│   └── main.py             # Entry point
├── docs/checkout-api.md    # Contrato do checkout
├── static/uploads/         # Imagens do cardápio
├── tests/                  # Testes de integração
├── alembic.ini
└── requirements.txt
```

## Roadmap

- [ ] Acompanhamento de status do pedido na cozinha
- [ ] Paginação na listagem do cardápio
- [ ] Rate limiting nas rotas de autenticação
