"""管理端业务逻辑：全部订单查询、状态流转、用户管理（RBAC）。"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.order import Order
from app.models.sku import Sku
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.services import cache
from app.services import token_store
from app.services import product as product_service

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
        # 取消订单（含已支付订单）恢复库存：与用户取消路径一致，
        # 恢复 SKU 库存并重算商品汇总，避免商品级库存与 SKU 库存漂移。
        affected_product_ids: set[int] = set()
        for item in order.items:
            affected_product_ids.add(item.product_id)
            if item.sku_id is None:
                # SKU 已被删除的历史订单项无法恢复库存，跳过
                continue
            sku = db.get(Sku, item.sku_id)
            if sku is not None:
                sku.stock += item.quantity
        product_service.refresh_product_summaries(db, list(affected_product_ids))
        cache.invalidate_products()

    order.status = new_status
    db.commit()
    return order


def list_users(
    db: Session, keyword: str | None, page: int, page_size: int
) -> tuple[list[User], int]:
    """分页查询用户列表，支持按用户名/昵称/邮箱模糊搜索。"""
    query = select(User)
    if keyword:
        like = f"%{keyword}%"
        query = query.where(
            or_(
                User.username.like(like),
                User.nickname.like(like),
                User.email.like(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    users = db.scalars(
        query.order_by(User.id.asc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(users), int(total or 0)


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise BusinessException("USER_NOT_FOUND", "用户不存在", status_code=404)
    return user


def update_user_status(
    db: Session, operator: User, user_id: int, status: str
) -> User:
    """禁用/启用用户；禁止操作自己与主账号；禁用时使该用户全部 Token 立即失效。"""
    if user_id == operator.id:
        raise BusinessException(
            "SELF_OPERATION_FORBIDDEN", "不能操作自己的账号", status_code=400
        )
    user = _get_user_or_404(db, user_id)
    if user.is_root:
        raise BusinessException(
            "ROOT_PROTECTED", "主账号不能被禁用", status_code=400
        )
    user.status = status
    db.commit()
    if status == "disabled":
        token_store.bump_epoch(user.id)
    return user


def update_user_role(
    db: Session, operator: User, user_id: int, role: str
) -> User:
    """分配/回收管理员角色；禁止修改自己的角色与主账号。"""
    if user_id == operator.id:
        raise BusinessException(
            "SELF_OPERATION_FORBIDDEN", "不能修改自己的角色", status_code=400
        )
    user = _get_user_or_404(db, user_id)
    if user.is_root:
        raise BusinessException(
            "ROOT_PROTECTED", "主账号角色不可修改", status_code=400
        )
    user.role = role
    db.commit()
    return user
