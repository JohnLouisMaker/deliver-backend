"""cria tabela de precos por tamanho de pizza

Revision ID: 4a7b9c1d2e3f
Revises: 3e4f5a6b7c8d
Create Date: 2026-11-06 10:00:00.000000

Modela o preco oficial de cada combinacao sabor do cardapio x tamanho.
A unicidade (item_cardapio_id, tamanho) impede precos duplicados/ambiguos e
os CHECKs impedem tamanho invalido e preco ausente ou nao positivo.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4a7b9c1d2e3f"
down_revision: Union[str, None] = "3e4f5a6b7c8d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "itens_cardapio_precos_tamanho",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_cardapio_id", sa.Integer(), nullable=False),
        sa.Column("tamanho", sa.String(length=10), nullable=False),
        sa.Column("preco", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint(
            "tamanho IN ('pequena', 'media', 'grande')",
            name="ck_itens_cardapio_precos_tamanho_tamanho_valido",
        ),
        sa.CheckConstraint(
            "preco > 0",
            name="ck_itens_cardapio_precos_tamanho_preco_positivo",
        ),
        sa.ForeignKeyConstraint(
            ["item_cardapio_id"],
            ["itens_cardapio.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "item_cardapio_id",
            "tamanho",
            name="uq_itens_cardapio_precos_tamanho_item_tamanho",
        ),
    )
    op.create_index(
        "ix_itens_cardapio_precos_tamanho_item_cardapio_id",
        "itens_cardapio_precos_tamanho",
        ["item_cardapio_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_itens_cardapio_precos_tamanho_item_cardapio_id",
        table_name="itens_cardapio_precos_tamanho",
    )
    op.drop_table("itens_cardapio_precos_tamanho")
