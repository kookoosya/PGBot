"""vk enhancements: categories, ai sessions, digest

Revision ID: 014
"""
from alembic import op
import sqlalchemy as sa

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vk_subscribers",
        sa.Column("categories", sa.String(80), server_default="all", nullable=False),
    )
    op.add_column(
        "vk_subscribers",
        sa.Column("last_digest_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "vk_ai_sessions",
        sa.Column("peer_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("messages", sa.Text(), server_default="[]", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("peer_id"),
    )


def downgrade() -> None:
    op.drop_table("vk_ai_sessions")
    op.drop_column("vk_subscribers", "last_digest_at")
    op.drop_column("vk_subscribers", "categories")
