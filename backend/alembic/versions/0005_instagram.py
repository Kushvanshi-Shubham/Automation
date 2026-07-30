"""Instagram: ig_accounts + multi-platform publishes ledger

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ig_accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("ig_user_id", sa.String(), nullable=False, unique=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("page_id", sa.String(), nullable=True),
        sa.Column("access_token", sa.String(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ig_accounts_user_id", "ig_accounts", ["user_id"])

    op.create_table(
        "publishes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("video_id", sa.Uuid(), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="publishing"),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_publishes_video_id", "publishes", ["video_id"])
    op.create_index("ix_publishes_user_id", "publishes", ["user_id"])


def downgrade() -> None:
    op.drop_table("publishes")
    op.drop_table("ig_accounts")
