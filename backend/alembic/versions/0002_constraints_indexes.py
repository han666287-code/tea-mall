"""constraints and indexes

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-14
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # order_items.product_id 是外键列且被订单查询使用，补齐索引
    op.create_index(
        op.f("ix_order_items_product_id"), "order_items", ["product_id"], unique=False
    )
    # 数据一致性：库存/价格/数量/金额不允许非法值（MySQL 8.0.16+ 强制生效）
    op.create_check_constraint(
        "ck_products_stock_non_negative", "products", "stock >= 0"
    )
    op.create_check_constraint(
        "ck_products_price_non_negative", "products", "price >= 0"
    )
    op.create_check_constraint(
        "ck_cart_items_quantity_positive", "cart_items", "quantity >= 1"
    )
    op.create_check_constraint(
        "ck_order_items_quantity_positive", "order_items", "quantity >= 1"
    )
    op.create_check_constraint(
        "ck_orders_total_amount_non_negative", "orders", "total_amount >= 0"
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_orders_total_amount_non_negative", "orders", type_="check"
    )
    op.drop_constraint(
        "ck_order_items_quantity_positive", "order_items", type_="check"
    )
    op.drop_constraint(
        "ck_cart_items_quantity_positive", "cart_items", type_="check"
    )
    op.drop_constraint(
        "ck_products_price_non_negative", "products", type_="check"
    )
    op.drop_constraint(
        "ck_products_stock_non_negative", "products", type_="check"
    )
    # MySQL 不允许直接删除被外键使用的索引（1553）：
    # 先删 order_items.product_id 的外键，再删索引，再重建外键（MySQL 会自动生成支撑索引）
    bind = op.get_bind()
    inspector = inspect(bind)
    fk_name = next(
        fk["name"]
        for fk in inspector.get_foreign_keys("order_items")
        if fk["constrained_columns"] == ["product_id"]
    )
    op.drop_constraint(fk_name, "order_items", type_="foreignkey")
    op.drop_index(op.f("ix_order_items_product_id"), table_name="order_items")
    op.create_foreign_key(None, "order_items", "products", ["product_id"], ["id"])
