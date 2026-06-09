"""Places map schema

Revision ID: 003
Revises: 002
Create Date: 2026-06-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "places",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("opening_hours", sa.String(length=500), nullable=True),
        sa.Column("osm_id", sa.String(length=50), nullable=True),
        sa.Column("external_source", sa.String(length=30), nullable=True),
        sa.Column("avg_rating", sa.Float(), server_default="0", nullable=False),
        sa.Column("review_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("complaint_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("osm_id"),
    )
    op.create_index("ix_places_name", "places", ["name"])
    op.create_index("ix_places_category", "places", ["category"])
    op.create_index("ix_places_lat", "places", ["latitude"])
    op.create_index("ix_places_lng", "places", ["longitude"])

    op.create_table(
        "place_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("place_id", sa.Integer(), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("vk_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["place_id"], ["places.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_place_reviews_place_id", "place_reviews", ["place_id"])

    op.create_table(
        "place_complaints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("place_id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=True),
        sa.Column("complaint_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price_tagged", sa.String(length=50), nullable=True),
        sa.Column("price_charged", sa.String(length=50), nullable=True),
        sa.Column("receipt_info", sa.Text(), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=True),
        sa.Column("vk_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="new", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["place_id"], ["places.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_place_complaints_place_id", "place_complaints", ["place_id"])


def downgrade() -> None:
    op.drop_table("place_complaints")
    op.drop_table("place_reviews")
    op.drop_table("places")
