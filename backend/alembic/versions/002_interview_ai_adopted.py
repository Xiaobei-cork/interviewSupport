"""add interview ai_adopted flag

Revision ID: 002
Revises: 001
Create Date: 2026-05-21

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interview_record",
        sa.Column("ai_adopted", sa.SmallInteger(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("interview_record", "ai_adopted")
