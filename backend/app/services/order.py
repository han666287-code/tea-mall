"""订单业务逻辑：创建订单（事务）、支付、取消、查询。"""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate
from app.services import cache

STATUS_PENDING = "pending"
STATUS_PAID = "paid"
STATUS_CANCELLED = "cancelled"


def generate_order_no() -> str:
    """订单号：时间戳 + 随机 6 位字符，保证唯一。"""
    return datetime.now().strftime("%Y%m%d%H%M%S") + uuid4().hex[:6].upper()


def _get_order_for_user(db: Session, user_id: int, order_id: int) -> Order:
    """按归属取订单：不是本人的订单统一返回 404。"""
    order = db.scalar(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


def create_order(db: Session, user: User, data: OrderCreate) -> Order:
    """从购物车创建订单：校验 → 写订单/订单项 → 扣库存 → 清购物车，单事务完成。"""
    cart_items = list(
        db.scalars(
            select(CartItem).where(CartItem.user_id == user.id).order_by(CartItem.id.asc())
        )
    )
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="购物车为空")

    # 先校验全部商品，任何一项不满足则整单失败
    prepared: list[tuple[Product, int, Decimal, Decimal]] = []
    total_amount = Decimal("0.00")
    for cart_item in cart_items:
        product = cart_item.product
        if product is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="商品不存在")
        if not product.is_on_sale:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"商品「{product.name}」已下架"
            )
        if cart_item.quantity > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"商品「{product.name}」库存不足",
            )
        subtotal = product.price * cart_item.quantity
        total_amount += subtotal
        prepared.append((product, cart_item.quantity, product.price, subtotal))

    order = Order(
        order_no=generate_order_no(),
        user_id=user.id,
        status=STATUS_PENDING,
        total_amount=total_amount,
        receiver_name=data.receiver_name,
        receiver_phone=data.receiver_phone,
        receiver_address=data.receiver_address,
    )
    for product, quantity, price, subtotal in prepared:
        order.items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                price=price,
                quantity=quantity,
                subtotal=subtotal,
            )
        )
        product.stock -= quantity

    try:
        db.add(order)
        for cart_item in cart_items:
            db.delete(cart_item)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    cache.invalidate_products()  # 库存已变化，商品缓存需要失效
    return order


def list_orders(db: Session, user_id: int, page: int, page_size: int) -> tuple[list[Order], int]:
    total = db.scalar(
        select(func.count()).select_from(Order).where(Order.user_id == user_id)
    ) or 0
    orders = list(
        db.scalars(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return orders, total


def get_order(db: Session, user: User, order_id: int) -> Order:
    return _get_order_for_user(db, user.id, order_id)


def pay_order(db: Session, user: User, order_id: int) -> Order:
    """模拟支付：仅 pending 状态可支付。"""
    order = _get_order_for_user(db, user.id, order_id)
    if order.status != STATUS_PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可支付")
    order.status = STATUS_PAID
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, user: User, order_id: int) -> Order:
    """取消未支付订单并恢复库存。"""
    order = _get_order_for_user(db, user.id, order_id)
    if order.status != STATUS_PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可取消")
    for item in order.items:
        product = db.get(Product, item.product_id)
        if product is not None:
            product.stock += item.quantity
    order.status = STATUS_CANCELLED
    db.commit()
    db.refresh(order)
    cache.invalidate_products()
    return order
