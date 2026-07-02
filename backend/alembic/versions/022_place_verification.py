"""place verification and scope fields

Revision ID: 022
Revises: 021
Create Date: 2026-06-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("places", sa.Column("scope", sa.String(30), nullable=True))
    op.add_column("places", sa.Column("verification_status", sa.String(30), nullable=True))
    op.add_column("places", sa.Column("verification_source_url", sa.String(500), nullable=True))
    op.add_column("places", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("places", sa.Column("verification_note", sa.String(500), nullable=True))
    op.create_index("ix_places_scope", "places", ["scope"])


def downgrade() -> None:
    op.drop_index("ix_places_scope", table_name="places")
    op.drop_column("places", "verification_note")
    op.drop_column("places", "verified_at")
    op.drop_column("places", "verification_source_url")
    op.drop_column("places", "verification_status")
    op.drop_column("places", "scope")
