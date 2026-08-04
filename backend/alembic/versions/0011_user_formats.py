"""Teach a style: personal formats learned from the creator's own reels

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-04

"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_formats",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        # learning -> ready | failed
        sa.Column("status", sa.String(), nullable=False, server_default="learning"),
        sa.Column("error_message", sa.Text(), nullable=True),
        # The analysis summary, for display
        sa.Column("profile", sa.JSON(), nullable=True),
        sa.Column("script_recipe", sa.Text(), nullable=True),
        sa.Column("caption_style", sa.String(), nullable=True),
        sa.Column("music_mood", sa.String(), nullable=True),
        sa.Column("tone", sa.String(), nullable=True),
        sa.Column("output_type", sa.String(), nullable=False, server_default="narrated"),
        # The asset ids (as strings) this style was learned from
        sa.Column("source_asset_ids", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_formats_user_id", "user_formats", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_formats_user_id", table_name="user_formats")
    op.drop_table("user_formats")
