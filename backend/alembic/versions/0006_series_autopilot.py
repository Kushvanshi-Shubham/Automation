"""Series autopilot: series table + videos.series_id

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "series",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("topic_prompt", sa.Text(), nullable=True),
        sa.Column("style", sa.String(), nullable=False, server_default="viral_story"),
        sa.Column("output_type", sa.String(), nullable=False, server_default="narrated"),
        sa.Column("language", sa.String(), nullable=False, server_default="English"),
        sa.Column("voice_id", sa.String(), nullable=True),
        sa.Column("interval_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("auto_publish", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("channel_id", sa.Uuid(), sa.ForeignKey("channels.id"), nullable=True),
        sa.Column("publish_privacy", sa.String(), nullable=False, server_default="unlisted"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_series_user_id", "series", ["user_id"])
    op.create_index("ix_series_next_run_at", "series", ["next_run_at"])

    op.add_column("videos", sa.Column("series_id", sa.Uuid(), sa.ForeignKey("series.id"), nullable=True))
    op.create_index("ix_videos_series_id", "videos", ["series_id"])


def downgrade() -> None:
    op.drop_index("ix_videos_series_id", table_name="videos")
    op.drop_column("videos", "series_id")
    op.drop_table("series")
