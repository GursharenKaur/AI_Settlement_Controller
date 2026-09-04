"""add audit status transition evidence

Revision ID: e7f4a9c21b6d
Revises: 832533f1f844
Create Date: 2026-09-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7f4a9c21b6d"
down_revision: Union[str, Sequence[str], None] = "832533f1f844"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "audit_logs",
        sa.Column(
            "previous_status",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "audit_logs",
        sa.Column(
            "new_status",
            sa.String(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column(
        "audit_logs",
        "new_status",
    )

    op.drop_column(
        "audit_logs",
        "previous_status",
    )