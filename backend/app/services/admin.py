"""管理端业务逻辑：全部订单查询与状态流转校验。"""

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.order import Order
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.services import cache

# 合法状态流转：当前状态 -> 允许的新状态集合
ALLOWED_TRANSITIONS = {
    "pending": {"paid", "cancelled"},
    "paid": {"shipped", "cancelled"},
    "shipped": {"completed"},
    "completed": set(),
    "cancelled": set(),
}


def list_all_orders(
    db: Session, order_status: str | None, page: int, page_size: int
) -> tuple[list[Order], int]:
    return OrderRepository(db).list_all_paginated(order_status, page, page_size)


def update_order_status(db: Session, order_id: int, new_status: str) -> Order:
    """更新订单状态；非法流转返回 400，取消时恢复库存。"""
    order = OrderRepository(db).get_by_id(order_id)
    if order is None:
        raise BusinessException("ORDER_NOT_FOUND", "订单不存在", status_code=404)

    allowed = ALLOWED_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise BusinessException(
            "ORDER_STATUS_INVALID",
            f"订单状态不能从 {order.status} 变更为 {new_status}",
            status_code=400,
        )

    if new_status == "cancelled":
        # 取消订单（含已支付订单）恢复库存
        for item in order.items:
            product = ProductRepository(db).get_by_id(item.product_id)
            if product is not None:
                product.stock += item.quantity
        cache.invalidate_products()

    order.status = new_status
    db.commit()
    return order
