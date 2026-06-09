"""AI paid entitlements

Revision ID: 021
"""
from alembic import op
import sqlalchemy as sa

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_entitlements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("vk_id", sa.Integer(), nullable=True),
        sa.Column("web_identifier", sa.String(255), nullable=True),
        sa.Column("plan_id", sa.String(32), nullable=False, server_default="pro"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payment_reference", sa.String(120), nullable=True),
        sa.Column("payment_amount", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("granted_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_entitlements_user_id", "ai_entitlements", ["user_id"])
    op.create_index("ix_ai_entitlements_vk_id", "ai_entitlements", ["vk_id"])
    op.create_index("ix_ai_entitlements_web_identifier", "ai_entitlements", ["web_identifier"])


def downgrade() -> None:
    op.drop_index("ix_ai_entitlements_web_identifier", "ai_entitlements")
    op.drop_index("ix_ai_entitlements_vk_id", "ai_entitlements")
    op.drop_index("ix_ai_entitlements_user_id", "ai_entitlements")
    op.drop_table("ai_entitlements")
