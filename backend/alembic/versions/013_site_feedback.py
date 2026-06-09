"""site feedback

Revision ID: 013_site_feedback
Revises: 012_vk_subscribers
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "site_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("contact", sa.String(length=200), nullable=True),
        sa.Column("page", sa.String(length=120), nullable=True),
        sa.Column("visitor_key", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="new", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_site_feedback_visitor_key", "site_feedback", ["visitor_key"])
    op.create_index("ix_site_feedback_created_at", "site_feedback", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_site_feedback_created_at", table_name="site_feedback")
    op.drop_index("ix_site_feedback_visitor_key", table_name="site_feedback")
    op.drop_table("site_feedback")
