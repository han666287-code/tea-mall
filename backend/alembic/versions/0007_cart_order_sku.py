"""cart and order sku

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 购物车：新增 sku_id（必填），唯一约束改为 user_id+sku_id（同 SKU 累加）
    op.add_column("cart_items", sa.Column("sku_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE cart_items ci
        JOIN (SELECT product_id, MIN(id) AS sku_id FROM skus GROUP BY product_id) s
          ON s.product_id = ci.product_id
        SET ci.sku_id = s.sku_id
        WHERE ci.sku_id IS NULL
        """
    )
    op.create_foreign_key(
        "fk_cart_items_sku_id",
        "cart_items",
        "skus",
        ["sku_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_cart_items_sku_id", "cart_items", ["sku_id"], unique=False)
    op.drop_constraint("uq_cart_user_product", "cart_items", type_="unique")
    op.create_unique_constraint("uq_cart_user_sku", "cart_items", ["user_id", "sku_id"])
    op.alter_column(
        "cart_items", "sku_id", existing_type=sa.Integer(), nullable=False
    )

    # 订单明细：新增可空 sku_id（SKU 删除后置 NULL，历史快照不受影响）
    op.add_column("order_items", sa.Column("sku_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE order_items oi
        JOIN (SELECT product_id, MIN(id) AS sku_id FROM skus GROUP BY product_id) s
          ON s.product_id = oi.product_id
        SET oi.sku_id = s.sku_id
        WHERE oi.sku_id IS NULL
        """
    )
    op.create_foreign_key(
        "fk_order_items_sku_id",
        "order_items",
        "skus",
        ["sku_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_order_items_sku_id", "order_items", ["sku_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_order_items_sku_id", table_name="order_items")
    op.drop_constraint("fk_order_items_sku_id", "order_items", type_="foreignkey")
    op.drop_column("order_items", "sku_id")

    op.drop_constraint("uq_cart_user_sku", "cart_items", type_="unique")
    op.drop_constraint("fk_cart_items_sku_id", "cart_items", type_="foreignkey")
    op.drop_index("ix_cart_items_sku_id", table_name="cart_items")
    op.drop_column("cart_items", "sku_id")
    op.create_unique_constraint(
        "uq_cart_user_product", "cart_items", ["user_id", "product_id"]
    )
