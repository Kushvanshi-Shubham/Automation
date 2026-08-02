"""Series format: autopilot runs a full pipeline recipe

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-02

"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Format key from services/formats.py; NULL = custom (legacy style/output_type)
    op.add_column("series", sa.Column("format", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("series", "format")
