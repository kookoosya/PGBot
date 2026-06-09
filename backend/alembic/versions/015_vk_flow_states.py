"""vk flow states in postgres

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
        "vk_flow_states",
        sa.Column("peer_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("step", sa.String(length=32), nullable=False),
        sa.Column("data", sa.Text(), server_default="{}", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("peer_id"),
    )


def downgrade() -> None:
    op.drop_table("vk_flow_states")
