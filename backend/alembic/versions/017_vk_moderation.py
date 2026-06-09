"""VK bot moderation tables

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
        "vk_user_moderation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vk_user_id", sa.Integer(), nullable=False),
        sa.Column("peer_id", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("banned_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_violation_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vk_user_moderation_vk_user_id", "vk_user_moderation", ["vk_user_id"], unique=True)
    op.create_index("ix_vk_user_moderation_peer_id", "vk_user_moderation", ["peer_id"])

    op.create_table(
        "vk_moderation_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vk_user_id", sa.Integer(), nullable=False),
        sa.Column("peer_id", sa.Integer(), nullable=False),
        sa.Column("message_excerpt", sa.String(500), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("warning_number", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vk_moderation_logs_vk_user_id", "vk_moderation_logs", ["vk_user_id"])
    op.create_index("ix_vk_moderation_logs_created_at", "vk_moderation_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("vk_moderation_logs")
    op.drop_table("vk_user_moderation")
