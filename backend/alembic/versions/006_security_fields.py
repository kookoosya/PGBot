"""Security fields on users

Revision ID: 006
Revises: 005
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_changed_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
