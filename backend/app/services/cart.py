"""购物车业务逻辑：加购、改数量、删除、列表与归属校验。"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate


def get_cart_items(db: Session, user_id: int) -> list[CartItem]:
    return list(
        db.scalars(
            select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id.desc())
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if not product.is_on_sale:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="商品已下架")
    if quantity > product.stock:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="库存不足")


def add_to_cart(db: Session, user: User, data: CartItemCreate) -> CartItem:
    product = db.get(Product, data.product_id)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="购物车项不存在")
    _check_product_available(item.product, quantity)
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item


def remove_from_cart(db: Session, user: User, item_id: int) -> None:
    item = get_cart_item_for_user(db, user.id, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="购物车项不存在")
    db.delete(item)
    db.commit()
