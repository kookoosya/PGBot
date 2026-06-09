"""add region to village events

Revision ID: 016
"""
from alembic import op
import sqlalchemy as sa

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "village_events",
        sa.Column("region", sa.String(50), server_default="pushkin_gory", nullable=False),
    )
    op.create_index("ix_village_events_region", "village_events", ["region"])


def downgrade() -> None:
    op.drop_index("ix_village_events_region", table_name="village_events")
    op.drop_column("village_events", "region")
