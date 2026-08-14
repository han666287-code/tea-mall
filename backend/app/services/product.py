"""商品业务逻辑：列表（筛选/分页/缓存）、详情、增删改、图片上传。"""

from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.core.exceptions import BusinessException
from app.models.category import Category
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services import cache

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


def list_products(
    db: Session,
    *,
    category_id: int | None,
    keyword: str | None,
    page: int,
    page_size: int,
    include_off_sale: bool,
    is_admin: bool,
) -> ProductListResponse:
    """商品列表：公开只显示上架商品；管理员可用 include_off_sale=true 查看全部。"""
    if include_off_sale and not is_admin:
        raise BusinessException(
            "ADMIN_PERMISSION_REQUIRED", "需要管理员权限", status_code=403
        )

    cache_key = cache.product_list_key(
        category_id, keyword, page, page_size, include_off_sale
    )
    cached = cache.get_json(cache_key)
    if cached is not None:
        return ProductListResponse.model_validate(cached)

    products, total = ProductRepository(db).list_for_page(
        category_id=category_id,
        keyword=keyword,
        include_off_sale=include_off_sale,
        page=page,
        page_size=page_size,
    )
    result = ProductListResponse(
        items=products, total=total, page=page, page_size=page_size
    )
    cache.set_json(cache_key, result.model_dump(mode="json"))
    return result


def get_product(db: Session, product_id: int, *, is_admin: bool) -> Product:
    """商品详情：下架商品仅管理员可见。"""
    cache_key = cache.product_detail_key(product_id)
    cached = cache.get_json(cache_key)
    if cached is not None:
        return ProductResponse.model_validate(cached)

    product = db.get(Product, product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    if not product.is_on_sale and not is_admin:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)

    if product.is_on_sale:
        cache.set_json(
            cache_key, ProductResponse.model_validate(product).model_dump(mode="json")
        )
    return product


def create_product(db: Session, data: ProductCreate) -> Product:
    if db.get(Category, data.category_id) is None:
        raise BusinessException(
            "PRODUCT_CATEGORY_NOT_FOUND", "分类不存在", status_code=400
        )
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    cache.invalidate_products()
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    updates = data.model_dump(exclude_unset=True)
    if "category_id" in updates and db.get(Category, updates["category_id"]) is None:
        raise BusinessException(
            "PRODUCT_CATEGORY_NOT_FOUND", "分类不存在", status_code=400
        )
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    cache.invalidate_products()
    return product


def delete_product(db: Session, product_id: int) -> None:
    product = db.get(Product, product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    db.delete(product)
    db.commit()
    cache.invalidate_products()


def save_product_image(file) -> str:
    """校验并保存上传图片，返回随机文件名；超限清理半成品文件。"""
    if not (file.content_type or "").startswith("image/"):
        raise BusinessException(
            "UNSUPPORTED_IMAGE_TYPE", "只支持上传图片文件", status_code=400
        )
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise BusinessException(
            "UNSUPPORTED_IMAGE_TYPE",
            f"不支持的图片格式：{ext or '未知'}",
            status_code=400,
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"
    target_path = UPLOAD_DIR / filename
    written = 0
    try:
        with open(target_path, "wb") as target:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_UPLOAD_SIZE_BYTES:
                    raise BusinessException(
                        "FILE_TOO_LARGE",
                        "文件过大：单个图片不能超过 10MB",
                        status_code=413,
                    )
                target.write(chunk)
    except BusinessException:
        # 超限时清理半成品文件，避免残留
        target_path.unlink(missing_ok=True)
        raise
    return filename


def upload_product_image(db: Session, product_id: int, file) -> Product:
    """上传商品图片：保存文件并更新 image_url。"""
    product = db.get(Product, product_id)
    if product is None:
        raise BusinessException("PRODUCT_NOT_FOUND", "商品不存在", status_code=404)
    filename = save_product_image(file)
    product.image_url = f"/uploads/{filename}"
    db.commit()
    cache.invalidate_products()
    return product
