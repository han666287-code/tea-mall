"""add users.status

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 存量行自动为 active；CHECK 约束由 MySQL 8 强制生效
    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'active'"),
            comment="active / disabled",
        ),
    )
    op.create_check_constraint(
        "ck_users_status", "users", "status IN ('active','disabled')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_status", "users", type_="check")
    op.drop_column("users", "status")
