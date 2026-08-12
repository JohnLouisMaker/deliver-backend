# AGENTS.md — deliver-backend

## Stack
- FastAPI + SQLAlchemy 2 + PostgreSQL + Alembic
- Auth: JWT (access + refresh) com python-jose + passlib/bcrypt
- Upload de imagem em `static/uploads/`

## Arquitetura
- `app/routes/` → routers
- `app/models/models.py` → SQLAlchemy
- `app/schemas/schemas.py` → Pydantic
- `app/dependencies.py` → session + auth
- Routers: `/auth`, `/pedidos`, `/cardapio`

## Regras Críticas
- NUNCA confie no preço enviado pelo client (preço vem do banco)
- NUNCA misture inglês/português nos nomes de domínio (código está em português)
- SEMPRE use `Depends(make_session)` para sessão de banco
- SEMPRE crie migration Alembic ao alterar models
- SEMPRE atualize o README ao criar/alterar rota
- NUNCA invente rotas que não existem no código (README está desatualizado)
- Prefira código mínimo (Ponytail)

## Comandos
- `uvicorn app.main:app --reload`
- `alembic upgrade head`
- `python -m app.seed`
- Docs: `http://127.0.0.1:8000/docs`

## Atenção
- `requirements.txt` está em UTF-16
- Dockerfile com path errado (`main:app` → deve ser `app.main:app`)
- Engine/Base duplicados em `database.py` e `models.py`
- Ver detalhes em `docs/` ou no README