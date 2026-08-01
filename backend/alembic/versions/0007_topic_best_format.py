"""Best-format recommendation per topic

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-02

"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("topics", sa.Column("best_format", sa.String(), nullable=True))
    op.add_column("topics", sa.Column("format_reason", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("topics", "format_reason")
    op.drop_column("topics", "best_format")
