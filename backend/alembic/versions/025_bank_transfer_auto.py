"""Bank transfer columns and inbox tracking

Revision ID: 025
"""
from alembic import op
import sqlalchemy as sa

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_payment_orders", sa.Column("payment_code", sa.String(32), nullable=True))
    op.add_column("ai_payment_orders", sa.Column("matched_reference", sa.Text(), nullable=True))
    op.create_index("ix_ai_payment_orders_payment_code", "ai_payment_orders", ["payment_code"], unique=True)

    op.create_table(
        "bank_inbox_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_uid", sa.String(128), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_bank_inbox_messages_message_uid", "bank_inbox_messages", ["message_uid"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_bank_inbox_messages_message_uid", "bank_inbox_messages")
    op.drop_table("bank_inbox_messages")
    op.drop_index("ix_ai_payment_orders_payment_code", "ai_payment_orders")
    op.drop_column("ai_payment_orders", "matched_reference")
    op.drop_column("ai_payment_orders", "payment_code")
