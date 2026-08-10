"""分类接口：列表公开，增删改仅管理员。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import cache

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """分类列表（公开，带 Redis 缓存）。"""
    cached = cache.get_json(cache.KEY_CATEGORIES)
    if cached is not None:
        return [CategoryResponse.model_validate(item) for item in cached]

    categories = db.scalars(
        select(Category).order_by(Category.sort_order.asc(), Category.id.asc())
    ).all()
    payload = [CategoryResponse.model_validate(c).model_dump(mode="json") for c in categories]
    cache.set_json(cache.KEY_CATEGORIES, payload)
    return payload


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    exists = db.scalar(select(Category).where(Category.name == data.name))
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类名称已存在")
    category = Category(name=data.name, sort_order=data.sort_order)
    db.add(category)
    db.commit()
    db.refresh(category)
    cache.invalidate_categories()
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    if data.name is not None and data.name != category.name:
        exists = db.scalar(select(Category).where(Category.name == data.name))
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类名称已存在")
        category.name = data.name
    if data.sort_order is not None:
        category.sort_order = data.sort_order
    db.commit()
    db.refresh(category)
    cache.invalidate_categories()
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    product_count = db.scalar(
        select(func.count()).select_from(Product).where(Product.category_id == category_id)
    )
    if product_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="该分类下存在商品，无法删除"
        )
    db.delete(category)
    db.commit()
    cache.invalidate_categories()
