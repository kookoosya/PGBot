"""map yandex ratings and taxi

Revision ID: 009
Revises: 008
Create Date: 2026-06-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("places", sa.Column("yandex_id", sa.String(50), nullable=True))
    op.add_column("places", sa.Column("external_rating", sa.Float(), server_default="0", nullable=False))
    op.add_column("places", sa.Column("external_review_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("places", sa.Column("yandex_url", sa.String(500), nullable=True))
    op.create_index("ix_places_yandex_id", "places", ["yandex_id"], unique=True)

    op.create_table(
        "taxi_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("phones_extra", sa.String(200), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_24h", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("rating", sa.Float(), server_default="0", nullable=False),
        sa.Column("price_from", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )


def downgrade() -> None:
    op.drop_table("taxi_services")
    op.drop_index("ix_places_yandex_id", table_name="places")
    op.drop_column("places", "yandex_url")
    op.drop_column("places", "external_review_count")
    op.drop_column("places", "external_rating")
    op.drop_column("places", "yandex_id")
