"""page visits tracking

Revision ID: 010
Revises: 009
Create Date: 2026-06-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "page_visits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("visitor_key", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("visited_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_page_visits_path", "page_visits", ["path"])
    op.create_index("ix_page_visits_visitor_key", "page_visits", ["visitor_key"])
    op.create_index("ix_page_visits_visited_at", "page_visits", ["visited_at"])


def downgrade() -> None:
    op.drop_index("ix_page_visits_visited_at", table_name="page_visits")
    op.drop_index("ix_page_visits_visitor_key", table_name="page_visits")
    op.drop_index("ix_page_visits_path", table_name="page_visits")
    op.drop_table("page_visits")
