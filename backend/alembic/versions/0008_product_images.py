"""product images

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_images",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('main', 'detail')", name="ck_product_images_kind"
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_product_images_product_id"),
        "product_images",
        ["product_id"],
        unique=False,
    )

    # 存量商品主图回填为 kind=main 行
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id, image_url FROM products WHERE image_url <> ''")
    ).fetchall()
    for row in rows:
        bind.execute(
            sa.text(
                "INSERT INTO product_images (product_id, url, kind, sort_order, created_at) "
                "VALUES (:product_id, :url, 'main', 0, now())"
            ),
            {"product_id": row[0], "url": row[1]},
        )


def downgrade() -> None:
    op.drop_table("product_images")
