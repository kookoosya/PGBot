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
        op.add_column("village_events", sa.Column("vk_posted_at", sa.DateTime(timezone=True), nullable=True))
    if "vk_post_id" not in columns:
        op.add_column("village_events", sa.Column("vk_post_id", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("village_events", "vk_post_id")
    op.drop_column("village_events", "vk_posted_at")
