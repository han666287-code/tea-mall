"""购物车业务逻辑：加购、改数量、删除、列表与归属校验。"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessException
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.sku import ProductSpecValue, Sku
from app.models.user import User
from app.repositories.sku_repository import SkuRepository
from app.schemas.cart import CartItemCreate


CART_LOADS = (
    selectinload(CartItem.product).selectinload(Product.category),
    selectinload(CartItem.product)
    .selectinload(Product.skus)
    .selectinload(Sku.spec_values)
    .selectinload(ProductSpecValue.spec),
    selectinload(CartItem.sku)
    .selectinload(Sku.spec_values)
    .selectinload(ProductSpecValue.spec),
)


def get_cart_items(db: Session, user_id: int) -> list[CartItem]:
    return list(
        db.scalars(
            select(CartItem)
            .options(*CART_LOADS)
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.id.desc())
        )
    )


def get_cart_item_for_user(db: Session, user_id: int, item_id: int) -> CartItem | None:
    """按归属取购物车项：不是本人的条目返回 None（对外统一 404）。"""
    return db.scalar(
        select(CartItem)
        .options(*CART_LOADS)
        .where(CartItem.id == item_id, CartItem.user_id == user_id)
    )


def _check_sku_available(sku: Sku | None, quantity: int) -> None:
    """校验 SKU 存在、商品上架、SKU 启用与库存。"""
    if sku is None:
        raise BusinessException("SKU_NOT_FOUND", "SKU 不存在", status_code=404)
    product = sku.product
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    if not product.is_on_sale:
        raise BusinessException("PRODUCT_OFF_SALE", "商品已下架", status_code=400)
    if not sku.is_active:
        raise BusinessException("SKU_DISABLED", "该规格暂不可售", status_code=400)
    if quantity > sku.stock:
        raise BusinessException("INSUFFICIENT_STOCK", "库存不足", status_code=400)


def add_to_cart(db: Session, user: User, data: CartItemCreate) -> CartItem:
    sku = SkuRepository(db).get_by_id(data.sku_id)
    _check_sku_available(sku, data.quantity)

    item = db.scalar(
        select(CartItem).where(
            CartItem.user_id == user.id, CartItem.sku_id == data.sku_id
        )
    )
    if item is None:
        item = CartItem(
            user_id=user.id,
            product_id=sku.product_id,
            sku_id=sku.id,
            quantity=data.quantity,
        )
        db.add(item)
    else:
        # 同一 SKU 重复加购：数量累加，仍不能超过库存
        new_quantity = item.quantity + data.quantity
        _check_sku_available(sku, new_quantity)
        item.quantity = new_quantity

    db.commit()
    db.refresh(item)
    return item


def update_quantity(db: Session, user: User, item_id: int, quantity: int) -> CartItem:
    item = get_cart_item_for_user(db, user.id, item_id)
    if item is None:
        raise BusinessException("CART_ITEM_NOT_FOUND", "购物车项不存在", status_code=404)
    _check_sku_available(item.sku, quantity)
    item.quantity = quantity
    db.commit()
    return item


def remove_from_cart(db: Session, user: User, item_id: int) -> None:
    item = get_cart_item_for_user(db, user.id, item_id)
    if item is None:
        raise BusinessException("CART_ITEM_NOT_FOUND", "购物车项不存在", status_code=404)
    db.delete(item)
    db.commit()
