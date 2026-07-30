"""Creation Workflow v2: videos.output_type

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column("output_type", sa.String(), nullable=False, server_default="narrated"),
    )


def downgrade() -> None:
    op.drop_column("videos", "output_type")
