"""Classified payment and moderation fields

Revision ID: 007
Revises: 006
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "classified_ads",
        sa.Column("payment_status", sa.String(length=20), server_default="approved", nullable=False),
    )
    op.add_column("classified_ads", sa.Column("payment_reference", sa.String(length=200), nullable=True))
    op.add_column("classified_ads", sa.Column("placement_fee", sa.Integer(), server_default="150", nullable=False))
    op.create_index("ix_classified_ads_payment_status", "classified_ads", ["payment_status"])


def downgrade() -> None:
    op.drop_index("ix_classified_ads_payment_status", table_name="classified_ads")
    op.drop_column("classified_ads", "placement_fee")
    op.drop_column("classified_ads", "payment_reference")
    op.drop_column("classified_ads", "payment_status")
