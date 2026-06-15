"""Add poster_url for cinema and culture events

Revision ID: 019
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {c["name"] for c in inspect(bind).get_columns("village_events")}
    if "poster_url" in columns:
        return
    # PostgreSQL: safe if column was added manually on prod
    bind.execute(sa.text(
        "ALTER TABLE village_events ADD COLUMN IF NOT EXISTS poster_url VARCHAR(1000)"
    ))


def downgrade() -> None:
    op.drop_column("village_events", "poster_url")
