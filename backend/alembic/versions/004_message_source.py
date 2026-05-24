"""add message source_type/source_id for dedupe

Revision ID: 004
Revises: 003
Create Date: 2026-05-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("message", sa.Column("source_type", sa.String(20), nullable=True))
    op.add_column("message", sa.Column("source_id", sa.BigInteger(), nullable=True))
    op.create_index(
        "uq_message_user_source",
        "message",
        ["user_id", "source_type", "source_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_message_user_source", table_name="message")
    op.drop_column("message", "source_id")
    op.drop_column("message", "source_type")
