"""Series: mood, length and visual engine

An autopilot episode never passes through the studio, so whatever the series
is configured with is what ships. It could pick a format but not a mood, not
a length, and not a visual engine — every episode was 60 seconds of stock
footage regardless of what the series was for.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Sub-flavour of the format (sad/love/nostalgic shayari, hype/chill music).
    op.add_column("series", sa.Column("mood", sa.String(), nullable=True))
    # Target spoken length. Null keeps the generator's own default.
    op.add_column("series", sa.Column("duration_seconds", sa.Integer(), nullable=True))
    # pexels | stock_image | ai_image. Null means the old hardcoded behaviour.
    op.add_column("series", sa.Column("visual_engine", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("series", "visual_engine")
    op.drop_column("series", "duration_seconds")
    op.drop_column("series", "mood")
