"""AI usage and user verification

Revision ID: 002
Revises: 001
Create Date: 2026-06-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("organization", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("position", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("verification_status", sa.String(length=30), server_default="not_required", nullable=False))
    op.add_column("users", sa.Column("verification_note", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("verified_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_users_verified_by", "users", "users", ["verified_by_id"], ["id"])

    op.create_table(
        "ai_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=20), server_default="web", nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("message_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_identifier", "ai_usage", ["identifier"])
    op.create_index("ix_ai_usage_usage_date", "ai_usage", ["usage_date"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_usage_date", "ai_usage")
    op.drop_index("ix_ai_usage_identifier", "ai_usage")
    op.drop_table("ai_usage")
    op.drop_constraint("fk_users_verified_by", "users", type_="foreignkey")
    op.drop_column("users", "verified_by_id")
    op.drop_column("users", "verified_at")
    op.drop_column("users", "verification_note")
    op.drop_column("users", "verification_status")
    op.drop_column("users", "position")
    op.drop_column("users", "organization")
