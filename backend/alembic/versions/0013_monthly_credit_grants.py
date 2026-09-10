"""Track when a user's credits were last renewed

Credits were granted exactly once, at signup, and never again — the only
other additions were refunds. So every user hit a permanent wall after
three renders, with no way past it while checkout returns 501.

The grant task needs to know when it last topped someone up. A calendar
month would have done, but a per-user timestamp means someone signing up
on the 30th does not get a second month's credits the next day.

Existing rows are backfilled to created_at, so their first renewal is a
month after they signed up rather than immediately.

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("credits_granted_at", sa.DateTime(timezone=True), nullable=True))
    # Null would read as "never granted" and top everyone up on the next
    # tick, handing existing users a free month they were not owed.
    op.execute("UPDATE users SET credits_granted_at = created_at WHERE credits_granted_at IS NULL")


def downgrade() -> None:
    op.drop_column("users", "credits_granted_at")
