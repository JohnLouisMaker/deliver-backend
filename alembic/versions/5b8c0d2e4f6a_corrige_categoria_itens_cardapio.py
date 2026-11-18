"""corrige categoria de itens_cardapio (backfill + enum NOT NULL)

Revision ID: 5b8c0d2e4f6a
Revises: 4a7b9c1d2e3f
Create Date: 2026-11-06 12:00:00.000000

O banco tinha `itens_cardapio.categoria` como VARCHAR nullable, divergindo do
model (enum `categoriaenum` NOT NULL). Esta migration faz o backfill das 12
linhas autorizadas, converte a coluna para o enum e aplica NOT NULL sem
descartar dados.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5b8c0d2e4f6a"
down_revision: Union[str, None] = "4a7b9c1d2e3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CATEGORIA_POR_ID = {
    1: "PIZZA",  # Marguerita Clássica
    2: "PIZZA",  # Pepperoni Toscana
    3: "PIZZA",  # 4 Queijos Cremosa
    4: "PIZZA",  # Frango Barbecue
    5: "PIZZA",  # Veggie Mediterrânea
    6: "PIZZA",  # Trufa Negra
    7: "PIZZA",  # Pesto e Tomate
    8: "ACOMPANHAMENTO",  # Bruschetta Mediterrânea
    9: "SOBREMESA",  # Brownie Belga
    10: "SOBREMESA",  # Cheesecake de Frutas Vermelhas
    11: "BEBIDA",  # Refrigerante Lata
    12: "BEBIDA",  # Suco Natural
}

CATEGORIA_VALUES = (
    "PIZZA",
    "BEBIDA",
    "SOBREMESA",
    "LANCHE",
    "ACOMPANHAMENTO",
    "OUTROS",
)


def upgrade() -> None:
    bind = op.get_bind()

    for item_id, categoria in CATEGORIA_POR_ID.items():
        op.execute(
            sa.text("UPDATE itens_cardapio SET categoria = :categoria WHERE id = :id").bindparams(
                categoria=categoria, id=item_id
            )
        )

    sem_categoria = bind.execute(sa.text("SELECT count(*) FROM itens_cardapio WHERE categoria IS NULL")).scalar()
    if sem_categoria:
        raise RuntimeError(
            f"Existem itens do cardápio sem categoria mapeada; migration abortada ({sem_categoria} linha(s))."
        )

    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE itens_cardapio ALTER COLUMN categoria TYPE categoriaenum USING categoria::categoriaenum"
        )
        op.execute("ALTER TABLE itens_cardapio ALTER COLUMN categoria SET NOT NULL")

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("itens_cardapio")}
    if "ix_itens_cardapio_categoria" not in indexes:
        op.create_index(
            "ix_itens_cardapio_categoria",
            "itens_cardapio",
            ["categoria"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("itens_cardapio")}
    if "ix_itens_cardapio_categoria" in indexes:
        op.drop_index("ix_itens_cardapio_categoria", table_name="itens_cardapio")

    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE itens_cardapio ALTER COLUMN categoria DROP NOT NULL")
        op.execute(
            "ALTER TABLE itens_cardapio ALTER COLUMN categoria TYPE character varying(120) USING categoria::text"
        )
