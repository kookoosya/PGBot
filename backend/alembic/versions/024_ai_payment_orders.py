"""AI payment orders for YooKassa

Revision ID: 024
"""
from alembic import op
import sqlalchemy as sa

revision = "024"
down_revision = "023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_payment_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.String(32), nullable=False),
        sa.Column("amount_rub", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("provider", sa.String(32), server_default="yookassa", nullable=False),
        sa.Column("external_id", sa.String(64), nullable=True),
        sa.Column("confirmation_url", sa.Text(), nullable=True),
        sa.Column("entitlement_id", sa.Integer(), sa.ForeignKey("ai_entitlements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_payment_orders_user_id", "ai_payment_orders", ["user_id"])
    op.create_index("ix_ai_payment_orders_status", "ai_payment_orders", ["status"])
    op.create_index("ix_ai_payment_orders_external_id", "ai_payment_orders", ["external_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_ai_payment_orders_external_id", "ai_payment_orders")
    op.drop_index("ix_ai_payment_orders_status", "ai_payment_orders")
    op.drop_index("ix_ai_payment_orders_user_id", "ai_payment_orders")
    op.drop_table("ai_payment_orders")
