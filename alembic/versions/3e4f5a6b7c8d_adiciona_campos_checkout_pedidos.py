"""adiciona campos de checkout na tabela pedidos

Revision ID: 3e4f5a6b7c8d
Revises: 2a3b4c5d6e7f
Create Date: 2026-10-01 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3e4f5a6b7c8d"
down_revision: Union[str, None] = "2a3b4c5d6e7f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'formapagamentoenum'
            ) THEN
                CREATE TYPE formapagamentoenum AS ENUM (
                    'DINHEIRO',
                    'CARTAO_CREDITO',
                    'CARTAO_DEBITO',
                    'PIX',
                    'VALE_ALIMENTACAO'
                );
            END IF;
        END
        $;
    """)

    op.add_column("pedidos", sa.Column("endereco_entrega", sa.Text(), nullable=True))
    op.add_column(
        "pedidos",
        sa.Column(
            "forma_pagamento",
            sa.Enum(
                "DINHEIRO",
                "CARTAO_CREDITO",
                "CARTAO_DEBITO",
                "PIX",
                "VALE_ALIMENTACAO",
                name="formapagamentoenum",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column("pedidos", sa.Column("troco_para", sa.Float(), nullable=True))
    op.add_column("pedidos", sa.Column("observacao", sa.Text(), nullable=True))
    op.add_column("pedidos", sa.Column("telefone_contato", sa.String(20), nullable=True))
    op.add_column(
        "pedidos",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("pedidos", "created_at")
    op.drop_column("pedidos", "telefone_contato")
    op.drop_column("pedidos", "observacao")
    op.drop_column("pedidos", "troco_para")
    op.drop_column("pedidos", "forma_pagamento")
    op.drop_column("pedidos", "endereco_entrega")