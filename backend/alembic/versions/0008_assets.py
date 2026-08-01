"""Creator media assets (clip recipe phase A)

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-02

"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), server_default="video"),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="uploaded"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("transcript", sa.JSON(), nullable=True),
        sa.Column("highlights", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_assets_user_id", "assets", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_assets_user_id", table_name="assets")
    op.drop_table("assets")
