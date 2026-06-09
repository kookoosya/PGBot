"""village events table

Revision ID: 015
"""
from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "village_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("category", sa.String(50), server_default="other", nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("is_published", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_village_events_starts_at", "village_events", ["starts_at"])
    op.create_index("ix_village_events_is_published", "village_events", ["is_published"])
    op.create_index("ix_village_events_category", "village_events", ["category"])


def downgrade() -> None:
    op.drop_index("ix_village_events_category", table_name="village_events")
    op.drop_index("ix_village_events_is_published", table_name="village_events")
    op.drop_index("ix_village_events_starts_at", table_name="village_events")
    op.drop_table("village_events")
