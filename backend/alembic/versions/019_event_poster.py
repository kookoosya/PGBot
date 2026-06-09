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
    if "poster_url" not in columns:
        op.add_column("village_events", sa.Column("poster_url", sa.String(1000), nullable=True))


def downgrade() -> None:
    op.drop_column("village_events", "poster_url")
