"""adiciona colunas reset_code_hash, reset_code_expires_at, reset_code_attempts na tabela usuario

Revision ID: 2a3b4c5d6e7f
Revises: c92d0da20f84
Create Date: 2026-08-15 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2a3b4c5d6e7f"
down_revision: Union[str, None] = "c92d0da20f84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuario",
        sa.Column("reset_code_hash", sa.String(64), nullable=True),
    )
    op.add_column(
        "usuario",
        sa.Column("reset_code_expires_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "usuario",
        sa.Column("reset_code_attempts", sa.Integer(), server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("usuario", "reset_code_attempts")
    op.drop_column("usuario", "reset_code_expires_at")
    op.drop_column("usuario", "reset_code_hash")