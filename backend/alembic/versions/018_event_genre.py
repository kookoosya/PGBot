"""Add genre field for cinema events

Revision ID: 018
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {c["name"] for c in inspect(bind).get_columns("village_events")}
    if "genre" not in columns:
        op.add_column("village_events", sa.Column("genre", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("village_events", "genre")
