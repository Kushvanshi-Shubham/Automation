"""BYO API keys: user_api_keys table

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_api_keys",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("key_encrypted", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )
    op.create_index("ix_user_api_keys_user_id", "user_api_keys", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_api_keys_user_id", table_name="user_api_keys")
    op.drop_table("user_api_keys")
