"""Feedback memory: standing creator notes applied to future generations

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-04

"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feedback_notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        # Format key from services/formats.py; NULL = applies to every video
        sa.Column("format", sa.String(), nullable=True),
        sa.Column("note", sa.String(length=300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_feedback_notes_user_id", "feedback_notes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_feedback_notes_user_id", table_name="feedback_notes")
    op.drop_table("feedback_notes")
