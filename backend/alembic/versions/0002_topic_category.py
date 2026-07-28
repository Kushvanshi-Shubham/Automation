"""Add topics.category for niche clustering

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-29

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("topics", sa.Column("category", sa.String(), nullable=True))
    op.create_index("ix_topics_category", "topics", ["category"])


def downgrade() -> None:
    op.drop_index("ix_topics_category", table_name="topics")
    op.drop_column("topics", "category")
