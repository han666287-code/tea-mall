"""分类业务逻辑：列表（缓存）、创建、更新、删除。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.category import Category
from app.repositories.product_repository import ProductRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import cache


def list_categories(db: Session) -> list[Category] | list[dict]:
    """分类列表（公开，带 Redis 缓存）。"""
    cached = cache.get_json(cache.KEY_CATEGORIES)
    if cached is not None:
        return [CategoryResponse.model_validate(item) for item in cached]
    categories = db.scalars(
        select(Category).order_by(Category.sort_order.asc(), Category.id.asc())
    ).all()
    payload = [
        CategoryResponse.model_validate(c).model_dump(mode="json") for c in categories
    ]
    cache.set_json(cache.KEY_CATEGORIES, payload)
    return payload


def create_category(db: Session, data: CategoryCreate) -> Category:
    exists = db.scalar(select(Category).where(Category.name == data.name))
    if exists:
        raise BusinessException("CATEGORY_NAME_TAKEN", "分类名称已存在", status_code=400)
    category = Category(name=data.name, sort_order=data.sort_order)
    db.add(category)
    db.commit()
    db.refresh(category)
    cache.invalidate_categories()
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise BusinessException("CATEGORY_NOT_FOUND", "分类不存在", status_code=404)
    if data.name is not None and data.name != category.name:
        exists = db.scalar(select(Category).where(Category.name == data.name))
        if exists:
            raise BusinessException(
                "CATEGORY_NAME_TAKEN", "分类名称已存在", status_code=400
            )
        category.name = data.name
    if data.sort_order is not None:
        category.sort_order = data.sort_order
    db.commit()
    cache.invalidate_categories()
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = db.get(Category, category_id)
    if category is None:
        raise BusinessException("CATEGORY_NOT_FOUND", "分类不存在", status_code=404)
    product_count = ProductRepository(db).count_by_category(category_id)
    if product_count:
        raise BusinessException(
            "CATEGORY_IN_USE", "该分类下存在商品，无法删除", status_code=400
        )
    db.delete(category)
    db.commit()
    cache.invalidate_categories()
