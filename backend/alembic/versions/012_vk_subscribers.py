"""vk subscribers

Revision ID: 012
"""
from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vk_subscribers",
        sa.Column("peer_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("peer_id"),
    )


def downgrade() -> None:
    op.drop_table("vk_subscribers")
