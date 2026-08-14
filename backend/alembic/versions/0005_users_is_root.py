"""add users.is_root

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_root",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
            comment="主账号标记：不可被降级或禁用",
        ),
    )
    # 存量默认管理员标记为主账号；自定义 ADMIN_USERNAME 的主账号由 seed.py 标记
    op.execute("UPDATE users SET is_root = 1 WHERE username = 'admin'")


def downgrade() -> None:
    op.drop_column("users", "is_root")
