import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Carrega o .env do backend para o Alembic funcionar sem export manual.
load_dotenv()

# Add the app directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the models
from app.models.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

db_url = (os.getenv("DATABASE_URL") or "").strip()
if not db_url:
    # Fallback apenas para o valor do alembic.ini (intencionalmente vazio no repo).
    db_url = (config.get_main_option("sqlalchemy.url") or "").strip()

if not db_url:
    raise SystemExit(
        "DATABASE_URL não definida. Configure a URL do PostgreSQL no arquivo .env do backend "
        "(ex.: DATABASE_URL=postgresql+psycopg2://usuario:senha@host:5432/banco) "
        "ou exporte a variável no ambiente antes de executar o Alembic."
    )

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# DDL de migration exige session mode (5432); o transaction pooler (6543) não é seguro.
db_url = db_url.replace(":6543/", ":5432/")

config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
