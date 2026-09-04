from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3aa18e2e7797"
down_revision: Union[str, Sequence[str], None] = "e7f4a9c21b6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exception_records",
        sa.Column("resolution_reason", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "exception_records",
        sa.Column("resolution_note", sa.Text(), nullable=True),
    )
    op.add_column(
        "exception_records",
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("exception_records", "resolved_at")
    op.drop_column("exception_records", "resolution_note")
    op.drop_column("exception_records", "resolution_reason")