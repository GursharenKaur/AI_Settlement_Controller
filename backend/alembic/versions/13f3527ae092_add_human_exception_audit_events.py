"""add human exception audit events

Revision ID: 13f3527ae092
Revises: 3aa18e2e7797
Create Date: 2026-09-04 16:42:19.826800
"""

from typing import Sequence, Union

from alembic import op


revision: str = "13f3527ae092"
down_revision: Union[str, Sequence[str], None] = "3aa18e2e7797"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE public.auditeventtype "
        "ADD VALUE IF NOT EXISTS 'EXCEPTION_ACKNOWLEDGED'"
    )
    op.execute(
        "ALTER TYPE public.auditeventtype "
        "ADD VALUE IF NOT EXISTS 'EXCEPTION_RESOLVED'"
    )


def downgrade() -> None:
    # PostgreSQL does not support removing individual values
    # from an enum type safely with ALTER TYPE.
    pass