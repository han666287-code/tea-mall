"""管理端业务逻辑：全部订单查询与状态流转校验。"""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.product import Product
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
    stmt = select(Order)
    if order_status:
        stmt = stmt.where(Order.status == order_status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    orders = list(
        db.scalars(
            stmt.order_by(Order.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return orders, total


def update_order_status(db: Session, order_id: int, new_status: str) -> Order:
    """更新订单状态；非法流转返回 400，取消时恢复库存。"""
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    allowed = ALLOWED_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单状态不能从 {order.status} 变更为 {new_status}",
        )

    if new_status == "cancelled":
        # 取消订单（含已支付订单）恢复库存
        for item in order.items:
            product = db.get(Product, item.product_id)
            if product is not None:
                product.stock += item.quantity
        cache.invalidate_products()

    order.status = new_status
    db.commit()
    db.refresh(order)
    return order
