"""vk ai mode state in postgres

Revision ID: 017
"""
from alembic import op
import sqlalchemy as sa

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vk_ai_modes",
        sa.Column("peer_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("peer_id"),
    )


def downgrade() -> None:
    op.drop_table("vk_ai_modes")
