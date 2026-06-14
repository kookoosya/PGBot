"""Track VK wall posts for events

Revision ID: 020
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {c["name"] for c in inspect(bind).get_columns("village_events")}
    if "vk_posted_at" not in columns:
        bind.execute(sa.text(
            "ALTER TABLE village_events ADD COLUMN IF NOT EXISTS vk_posted_at TIMESTAMPTZ"
        ))
    if "vk_post_id" not in columns:
        bind.execute(sa.text(
            "ALTER TABLE village_events ADD COLUMN IF NOT EXISTS vk_post_id VARCHAR(50)"
        ))


def downgrade() -> None:
    op.drop_column("village_events", "vk_post_id")
    op.drop_column("village_events", "vk_posted_at")
