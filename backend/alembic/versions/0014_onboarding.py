"""Remember a creator's niche and language, and whether they've been asked

A new account landed on an empty dashboard with three credits and no idea
what to do — no first question, no default, nothing. Trends were shown for
every category at once, so the first thing a gaming creator saw was mostly
irrelevant to them.

Three columns rather than one JSON blob, because each is read on its own:
`niche` defaults the trend filter, `language` defaults the script language,
and `onboarded_at` decides whether to ask at all.

Existing users are backfilled to created_at, not NULL: they have already
found their way around, and dropping them into a first-run flow now would
read as the app having forgotten them.

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Niche key from services/niches.py; null means "no preference yet".
    op.add_column("users", sa.Column("niche", sa.String(), nullable=True))
    # Script language from services/voices.LANGUAGES.
    op.add_column("users", sa.Column("language", sa.String(), nullable=True))
    op.add_column("users", sa.Column("onboarded_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE users SET onboarded_at = created_at WHERE onboarded_at IS NULL")


def downgrade() -> None:
    op.drop_column("users", "onboarded_at")
    op.drop_column("users", "language")
    op.drop_column("users", "niche")
