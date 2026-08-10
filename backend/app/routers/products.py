"""商品接口：列表/详情公开，增删改/图片上传仅管理员。"""

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.core.deps import get_current_admin, get_optional_current_user
from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services import cache

router = APIRouter(prefix="/api/products", tags=["products"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.get("", response_model=ProductListResponse)
def list_products(
    category_id: int | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    include_off_sale: bool = False,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    """商品列表：公开只显示上架商品；管理员可用 include_off_sale=true 查看全部。"""
    is_admin = current_user is not None and current_user.role == "admin"
    if include_off_sale and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")

    cache_key = cache.product_list_key(category_id, keyword, page, page_size, include_off_sale)
    cached = cache.get_json(cache_key)
    if cached is not None:
        return ProductListResponse.model_validate(cached)

    stmt = select(Product)
    if not include_off_sale:
        stmt = stmt.where(Product.is_on_sale.is_(True))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if keyword:
        stmt = stmt.where(
            or_(Product.name.like(f"%{keyword}%"), Product.description.like(f"%{keyword}%"))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    products = db.scalars(
        stmt.order_by(Product.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    result = ProductListResponse(
        items=products, total=total, page=page, page_size=page_size
    )
    cache.set_json(cache_key, result.model_dump(mode="json"))
    return result


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    """商品详情：下架商品仅管理员可见。"""
    cache_key = cache.product_detail_key(product_id)
    cached = cache.get_json(cache_key)
    if cached is not None:
        return ProductResponse.model_validate(cached)

    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    is_admin = current_user is not None and current_user.role == "admin"
    if not product.is_on_sale and not is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")

    if product.is_on_sale:
        cache.set_json(cache_key, ProductResponse.model_validate(product).model_dump(mode="json"))
    return product


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    if db.get(Category, data.category_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类不存在")
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    cache.invalidate_products()
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    updates = data.model_dump(exclude_unset=True)
    if "category_id" in updates and db.get(Category, updates["category_id"]) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类不存在")
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    cache.invalidate_products()
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    db.delete(product)
    db.commit()
    cache.invalidate_products()


@router.post("/{product_id}/image", response_model=ProductResponse)
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    """上传商品图片，保存到 backend/uploads/ 并返回 /uploads/ 开头的相对路径。"""
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只支持上传图片文件")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式：{ext or '未知'}",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"
    with open(UPLOAD_DIR / filename, "wb") as target:
        shutil.copyfileobj(file.file, target)

    product.image_url = f"/uploads/{filename}"
    db.commit()
    db.refresh(product)
    cache.invalidate_products()
    return product
