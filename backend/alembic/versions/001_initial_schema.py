"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("telegram_chat_id", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("vk_id", sa.BigInteger(), nullable=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("telegram_id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("vk_id"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_vk_id", "users", ["vk_id"])

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="NEW"),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("vk_message_id", sa.BigInteger(), nullable=True),
        sa.Column("vk_peer_id", sa.BigInteger(), nullable=True),
        sa.Column("resident_id", sa.Integer(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("parent_issue_id", sa.Integer(), nullable=True),
        sa.Column("confirmation_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_spam", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolution_text", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["parent_issue_id"], ["issues.id"]),
        sa.ForeignKeyConstraint(["resident_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_issues_status", "issues", ["status"])
    op.create_index("ix_issues_category", "issues", ["category"])
    op.create_index("ix_issues_created_at", "issues", ["created_at"])

    op.create_table(
        "issue_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("vk_photo_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "issue_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "issue_duplicates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("duplicate_of_id", sa.Integer(), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["duplicate_of_id"], ["issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ai_analysis",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("duplicate_probability", sa.Float(), nullable=True),
        sa.Column("suggested_department", sa.String(length=255), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issue_id"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=True),
        sa.Column("recipient_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=50), nullable=False, server_default="telegram"),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_status", "notifications", ["status"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("ai_analysis")
    op.drop_table("issue_duplicates")
    op.drop_table("issue_comments")
    op.drop_table("issue_photos")
    op.drop_table("issues")
    op.drop_table("users")
    op.drop_table("departments")
    op.drop_table("roles")
