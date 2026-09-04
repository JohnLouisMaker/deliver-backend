# Deliver Backend — FastAPI + PostgreSQL

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-database-4169E1?logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-hosting-3FCF8E?logo=supabase&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-migrations-5A5A5A)
![JWT](https://img.shields.io/badge/Auth-JWT-000000?logo=jsonwebtokens&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

API RESTful para um sistema de delivery (estilo pizzaria), construída com **FastAPI**, **SQLAlchemy** e autenticação via **JWT**.

## Sobre o Projeto

Backend com autenticação completa (cadastro, login, refresh de token e recuperação de senha por e-mail), um **cardápio** administrável (com upload de imagem) e **pedidos** vinculados a itens do cardápio — o preço de cada item é sempre lido do banco, nunca confiado ao cliente. Cada pedido pertence a um usuário e pode conter múltiplos itens (sabor, tamanho, quantidade). Administradores têm acesso irrestrito; usuários comuns gerenciam apenas os próprios pedidos.

## Tecnologias

| Tecnologia | Uso |
|---|---|
| **FastAPI** | Framework web |
| **SQLAlchemy 2** | ORM e modelagem do banco |
| **PostgreSQL** | Banco de dados (hospedado no [Supabase](https://supabase.com)) |
| **Alembic** | Migrações do banco |
| **python-jose** | Geração e validação de JWT |
| **passlib[bcrypt]** | Hash de senhas |
| **fastapi-mail** | Envio de e-mail (recuperação de senha) |
| **python-dotenv** | Variáveis de ambiente |
| **psycopg2-binary** | Driver do PostgreSQL |
| **uvicorn** | Servidor ASGI |

## Estrutura do Projeto

```
├── alembic/                    # Migrações do banco de dados
│   └── versions/
├── app/
│   ├── core/
│   │   └── config.py           # Configurações via .env (JWT, SMTP)
│   ├── database/
│   │   └── database.py         # Engine, SessionLocal e Base do SQLAlchemy
│   ├── models/
│   │   └── models.py           # Modelos: UserModel, PedidoModel, ItemPedidoModel, ItemCardapio
│   ├── routes/
│   │   ├── auth_routes.py      # Rotas de autenticação e recuperação de senha
│   │   ├── order_routes.py     # Rotas de pedidos
│   │   └── product_routes.py   # Rotas do cardápio
│   ├── schemas/
│   │   └── schemas.py          # Schemas Pydantic
│   ├── dependencies.py         # Injeção de dependências e autenticação
│   ├── main.py                 # Entry point da aplicação
│   ├── security.py             # Contexto bcrypt e OAuth2
│   └── seed.py                 # Popula o cardápio inicial no banco
├── static/uploads/             # Imagens dos itens do cardápio
├── tests/                      # Testes (auth, pedidos, cardápio)
├── alembic.ini
├── requirements.txt
└── .env                        # (não versionado)
```

> ⚠️ Detalhes conhecidos do projeto: `requirements.txt` é salvo em UTF-16 (abra com editor compatível ou `pip install -r requirements.txt` normalmente, que funciona); o `Dockerfile` usa `main:app` no `CMD`, mas o entry point real é `app.main:app`; o `package.json` na raiz só declara `@supabase/supabase-js` (não é usado pelo backend Python — é dependência auxiliar/de outro contexto).

## Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/JohnLouisMaker/deliver-backend.git
cd deliver-backend
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto. O banco Postgres deste projeto roda no **Supabase** — pegue a *Connection String* em `Project Settings → Database` (prefira o modo **Transaction Pooler**, porta `6543`, para ambientes serverless/produção):

```env
# Banco de dados (Supabase)
DATABASE_URL=postgresql://postgres.xxxxxxxxxxxx:SUA_SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres

# JWT
SECRET_KEY=sua_chave_secreta_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE=30          # em minutos
REFRESH_TOKEN_EXPIRE=10080      # em minutos (o padrão equivale a 7 dias)

# SMTP (usado no fluxo de recuperação de senha)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
EMAIL_FROM=noreply@delivery.com
```

> A conexão usa `psycopg2` via SQLAlchemy, então qualquer *connection string* Postgres do Supabase funciona — direta (porta `5432`) ou via pooler (porta `6543`, recomendada quando o app roda em serverless/muitas instâncias).

### 5. Execute as migrações

```bash
alembic upgrade head
```

### 6. (Opcional) Popule o cardápio inicial

```bash
python -m app.seed
```

### 7. Inicie o servidor

```bash
uvicorn app.main:app --reload
```

A API estará disponível em: `http://127.0.0.1:8000`
Documentação interativa: `http://127.0.0.1:8000/docs`

## Autenticação

A API usa **JWT** com três tipos de token (campo `type` no payload): `access`, `refresh` e `reset` (para redefinição de senha).

* **Access Token**: curta duração, usado nas requisições autenticadas.
* **Refresh Token**: longa duração, usado para renovar o access token.
* **Reset Token**: emitido em `/auth/forgot-password`, usado apenas no fluxo de recuperação de senha.

Todas as rotas protegidas exigem o header:
`Authorization: Bearer <access_token>`

## Endpoints

### Auth — `/auth`

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| `POST` | `/auth/signup` | Cadastro de novo usuário | ❌ |
| `POST` | `/auth/login` | Login com email e senha (JSON) | ❌ |
| `POST` | `/auth/loginform` | Login via OAuth2 form (usado pelo Swagger) | ❌ |
| `POST` | `/auth/refresh` | Renova o access token | Refresh Token |
| `GET` | `/auth/me` | Retorna os dados do usuário autenticado | Access Token |
| `POST` | `/auth/forgot-password` | Envia um código de recuperação por e-mail e retorna um `reset_token` | ❌ |
| `POST` | `/auth/verify-reset-code` | Valida o código de recuperação recebido por e-mail | ❌ |
| `POST` | `/auth/reset-password` | Define uma nova senha usando o código + `reset_token` | ❌ |

### Cardápio — `/cardapio`

| Método | Rota | Descrição | Permissão |
|---|---|---|---|
| `GET` | `/cardapio/` | Lista itens disponíveis (filtro opcional por `categoria`) | ❌ |
| `GET` | `/cardapio/{item_id}` | Detalhes de um item | ❌ |
| `POST` | `/cardapio/adicionar` | Cria um item do cardápio (com upload de imagem) | Admin |
| `PATCH` | `/cardapio/editar/{item_id}` | Atualiza nome, preço e/ou disponibilidade de um item | Admin |
| `DELETE` | `/cardapio/deletar/{item_id}` | Remove um item (e sua imagem) | Admin |

### Pedidos — `/pedidos`

| Método | Rota | Descrição | Permissão |
|---|---|---|---|
| `POST` | `/pedidos/criar_pedido` | Cria um novo pedido (status `PENDENTE`) | Autenticado |
| `GET` | `/pedidos/meus_pedidos` | Lista os pedidos do usuário autenticado | Autenticado |
| `POST` | `/pedidos/adicionar_item/{pedido_id}` | Adiciona um item do cardápio ao pedido (preço vem do banco) | Dono ou Admin |
| `DELETE` | `/pedidos/remover_item/{pedido_id}/{item_id}` | Remove um item do pedido | Dono ou Admin |
| `POST` | `/pedidos/finalizar/{pedido_id}` | Finaliza o pedido (envia para a cozinha) | Dono ou Admin |

## Modelos do Banco

### usuario
* `id`: Integer (PK)
* `nome`: String(100)
* `email`: String(150) - Unique
* `senha`: String(250) — hash bcrypt
* `ativo`: Boolean
* `admin`: Boolean
* `reset_code_hash`: String(64) - Nullable — hash SHA-256 do código de recuperação
* `reset_code_expires_at`: DateTime - Nullable
* `reset_code_attempts`: Integer

### itens_cardapio
* `id`: Integer (PK)
* `nome`: String(120)
* `descricao`: Text - Nullable
* `preco`: Float
* `categoria`: Enum (`Pizza`, `Bebida`, `Sobremesa`, `Lanche`, `Acompanhamento`, `Outros`)
* `disponivel`: Boolean
* `imagem_url`: String(255) - Nullable

### pedidos
* `id`: Integer (PK)
* `usuario_id`: FK → usuario
* `status`: Enum (`Pendente`, `Finalizado`, `Cancelado`)
* `preco`: Float (Valor total, calculado a partir dos itens)

### itens_pedidos
* `id`: Integer (PK)
* `pedido_id`: FK → pedidos
* `item_cardapio_id`: FK → itens_cardapio - Nullable
* `nome_snapshot`: String(100) — nome do item no momento do pedido
* `imagem_url_snapshot`: String - Nullable
* `sabor`: String(100) - Nullable
* `tamanho`: String(100) - Nullable
* `quantidade`: Integer
* `preco_unitario`: Float — copiado do cardápio, nunca enviado pelo cliente

## Migrações com Alembic

```bash
# Criar nova migration
alembic revision --autogenerate -m "descricao"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1
```

## Licença

Este projeto está sob a licença MIT.
