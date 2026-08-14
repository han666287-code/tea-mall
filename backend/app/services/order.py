"""订单业务逻辑：创建订单（事务）、支付、取消、查询。"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.sku import Sku
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.repositories.sku_repository import SkuRepository
from app.schemas.order import OrderCreate
from app.services import cache, product as product_service

STATUS_PENDING = "pending"
STATUS_PAID = "paid"
STATUS_CANCELLED = "cancelled"


def generate_order_no() -> str:
    """订单号：时间戳 + 随机 6 位字符，保证唯一。"""
    return datetime.now().strftime("%Y%m%d%H%M%S") + uuid4().hex[:6].upper()


def _get_order_for_user(db: Session, user_id: int, order_id: int) -> Order:
    """按归属取订单：不是本人的订单统一返回 404。"""
    order = OrderRepository(db).get_for_user(user_id, order_id)
    if order is None:
        raise BusinessException("ORDER_NOT_FOUND", "订单不存在", status_code=404)
    return order


def create_order(db: Session, user: User, data: OrderCreate) -> Order:
    """从购物车创建订单：校验 → 写订单/订单项 → 扣库存 → 清购物车，单事务完成。"""
    cart_items = list(
        db.scalars(
            select(CartItem).where(CartItem.user_id == user.id).order_by(CartItem.id.asc())
        )
    )
    if not cart_items:
        raise BusinessException("CART_EMPTY", "购物车为空", status_code=400)

    # 锁定购物车内所有 SKU 行（FOR UPDATE），防止并发下单超卖；
    # 按 id 排序锁定，避免多 SKU 订单之间产生死锁
    sku_ids = [item.sku_id for item in cart_items]
    locked_skus = SkuRepository(db).get_locked_by_ids(sku_ids)
    if len(locked_skus) != len(set(sku_ids)):
        raise BusinessException("SKU_NOT_FOUND", "商品 SKU 不存在或已失效", status_code=400)

    # 先校验全部商品，任何一项不满足则整单失败
    prepared: list[tuple[CartItem, Sku, Decimal]] = []
    total_amount = Decimal("0.00")
    for cart_item in cart_items:
        sku = locked_skus[cart_item.sku_id]
        product = sku.product
        if product is None:
            raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=400)
        if not product.is_on_sale:
            raise BusinessException(
                "PRODUCT_OFF_SALE", f"商品「{product.name}」已下架", status_code=400
            )
        if not sku.is_active:
            raise BusinessException(
                "SKU_DISABLED", f"商品「{product.name}」的该规格暂不可售", status_code=400
            )
        if cart_item.quantity > sku.stock:
            raise BusinessException(
                "INSUFFICIENT_STOCK",
                f"商品「{product.name}」库存不足",
                status_code=400,
            )
        subtotal = sku.price * cart_item.quantity
        total_amount += subtotal
        prepared.append((cart_item, sku, subtotal))

    order = Order(
        order_no=generate_order_no(),
        user_id=user.id,
        status=STATUS_PENDING,
        total_amount=total_amount,
        receiver_name=data.receiver_name,
        receiver_phone=data.receiver_phone,
        receiver_address=data.receiver_address,
    )
    affected_product_ids: set[int] = set()
    for cart_item, sku, subtotal in prepared:
        product = sku.product
        order.items.append(
            OrderItem(
                product_id=product.id,
                sku_id=sku.id,
                product_name=product.name,
                price=sku.price,
                quantity=cart_item.quantity,
                subtotal=subtotal,
            )
        )
        sku.stock -= cart_item.quantity
        affected_product_ids.add(product.id)

    try:
        db.add(order)
        for cart_item in cart_items:
            db.delete(cart_item)
        product_service.refresh_product_summaries(db, list(affected_product_ids))
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    cache.invalidate_products()  # 库存已变化，商品缓存需要失效
    return order


def list_orders(db: Session, user_id: int, page: int, page_size: int) -> tuple[list[Order], int]:
    return OrderRepository(db).list_for_user_paginated(user_id, page, page_size)


def get_order(db: Session, user: User, order_id: int) -> Order:
    return _get_order_for_user(db, user.id, order_id)


def pay_order(db: Session, user: User, order_id: int) -> Order:
    """模拟支付：仅 pending 状态可支付。"""
    order = _get_order_for_user(db, user.id, order_id)
    if order.status != STATUS_PENDING:
        raise BusinessException("ORDER_STATUS_INVALID", "当前状态不可支付", status_code=400)
    order.status = STATUS_PAID
    db.commit()
    return order


def cancel_order(db: Session, user: User, order_id: int) -> Order:
    """取消未支付订单并恢复库存。"""
    order = _get_order_for_user(db, user.id, order_id)
    if order.status != STATUS_PENDING:
        raise BusinessException("ORDER_STATUS_INVALID", "当前状态不可取消", status_code=400)
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
    order.status = STATUS_CANCELLED
    db.commit()
    cache.invalidate_products()
    return order
