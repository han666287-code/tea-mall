"""购物车业务逻辑：加购、改数量、删除、列表与归属校验。"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessException
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import CartItemCreate


def get_cart_items(db: Session, user_id: int) -> list[CartItem]:
    return list(
        db.scalars(
            select(CartItem)
            .options(
                selectinload(CartItem.product).selectinload(Product.category)
            )
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.id.desc())
        )
    )


def get_cart_item_for_user(db: Session, user_id: int, item_id: int) -> CartItem | None:
    """按归属取购物车项：不是本人的条目返回 None（对外统一 404）。"""
    return db.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user_id)
    )


def _check_product_available(product: Product | None, quantity: int) -> None:
    """校验商品上架状态与库存。"""
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    if not product.is_on_sale:
        raise BusinessException("PRODUCT_OFF_SALE", "商品已下架", status_code=400)
    if quantity > product.stock:
        raise BusinessException("INSUFFICIENT_STOCK", "库存不足", status_code=400)


def add_to_cart(db: Session, user: User, data: CartItemCreate) -> CartItem:
    product = ProductRepository(db).get_by_id(data.product_id)
    _check_product_available(product, data.quantity)

    item = db.scalar(
        select(CartItem).where(
            CartItem.user_id == user.id, CartItem.product_id == data.product_id
        )
    )
    if item is None:
        item = CartItem(
            user_id=user.id, product_id=data.product_id, quantity=data.quantity
        )
        db.add(item)
    else:
        # 同一商品重复加购：数量累加，仍不能超过库存
        new_quantity = item.quantity + data.quantity
        _check_product_available(product, new_quantity)
        item.quantity = new_quantity

    db.commit()
    db.refresh(item)
    return item


def update_quantity(db: Session, user: User, item_id: int, quantity: int) -> CartItem:
    item = get_cart_item_for_user(db, user.id, item_id)
    if item is None:
        raise BusinessException("CART_ITEM_NOT_FOUND", "购物车项不存在", status_code=404)
    _check_product_available(item.product, quantity)
    item.quantity = quantity
    db.commit()
    return item


def remove_from_cart(db: Session, user: User, item_id: int) -> None:
    item = get_cart_item_for_user(db, user.id, item_id)
    if item is None:
        raise BusinessException("CART_ITEM_NOT_FOUND", "购物车项不存在", status_code=404)
    db.delete(item)
    db.commit()
