"""usa Numeric para valores monetários

Revision ID: 6c9d1e2f3a4b
Revises: 5b8c0d2e4f6a
Create Date: 2026-11-16 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6c9d1e2f3a4b"
down_revision: Union[str, None] = "5b8c0d2e4f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUNAS_MONETARIAS = (
    ("itens_cardapio", "preco"),
    ("pedidos", "preco"),
    ("pedidos", "troco_para"),
    ("itens_pedidos", "preco_unitario"),
)


def upgrade() -> None:
    bind = op.get_bind()
    for tabela, coluna in COLUNAS_MONETARIAS:
        if bind.dialect.name == "postgresql":
            op.alter_column(
                tabela,
                coluna,
                existing_type=sa.Float(),
                type_=sa.Numeric(precision=10, scale=2),
                postgresql_using=f"{coluna}::numeric(10, 2)",
            )
        else:
            with op.batch_alter_table(tabela) as batch_op:
                batch_op.alter_column(
                    coluna,
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=10, scale=2),
                )


def downgrade() -> None:
    bind = op.get_bind()
    for tabela, coluna in COLUNAS_MONETARIAS:
        if bind.dialect.name == "postgresql":
            op.alter_column(
                tabela,
                coluna,
                existing_type=sa.Numeric(precision=10, scale=2),
                type_=sa.Float(),
                postgresql_using=f"{coluna}::double precision",
            )
        else:
            with op.batch_alter_table(tabela) as batch_op:
                batch_op.alter_column(
                    coluna,
                    existing_type=sa.Numeric(precision=10, scale=2),
                    type_=sa.Float(),
                )
