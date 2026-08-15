"""商品接口：列表/详情公开，增删改/图片上传仅管理员。"""

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_optional_current_admin
from app.database import get_db
from app.models.user import User
from app.schemas.common import MAX_PAGE_SIZE
from app.schemas.product import (
    ProductCreate,
    ProductImageRemove,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    SkuPayload,
)
from app.services import product as product_service

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    category_id: int | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=MAX_PAGE_SIZE),
    include_off_sale: bool = False,
    db: Session = Depends(get_db),
    current_admin: User | None = Depends(get_optional_current_admin),
):
    """商品列表：公开只显示上架商品；管理员可用 include_off_sale=true 查看全部。"""
    return product_service.list_products(
        db,
        category_id=category_id,
        keyword=keyword,
        page=page,
        page_size=page_size,
        include_off_sale=include_off_sale,
        is_admin=current_admin is not None,
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: User | None = Depends(get_optional_current_admin),
):
    """商品详情：下架商品仅管理员可见。"""
    return product_service.get_product(
        db, product_id, is_admin=current_admin is not None
    )


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return product_service.create_product(db, data)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return product_service.update_product(db, product_id, data)


@router.put("/{product_id}/skus", response_model=ProductResponse)
def replace_skus(
    product_id: int,
    skus: list[SkuPayload],
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    """批量替换商品 SKU（含规格定义）；仅管理员可操作。"""
    return product_service.replace_skus(db, product_id, skus)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    product_service.delete_product(db, product_id)


@router.post("/{product_id}/image", response_model=ProductResponse)
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    """上传商品图片，保存到 backend/uploads/ 并返回 /uploads/ 开头的相对路径。"""
    return product_service.upload_product_image(db, product_id, file)


@router.post("/{product_id}/images", response_model=ProductResponse)
def upload_product_images(
    product_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    """上传商品多张详情图（追加 kind=detail 行）；仅管理员可操作。"""
    return product_service.upload_product_images(db, product_id, files)


@router.delete("/{product_id}/images", response_model=ProductResponse)
def remove_product_image(
    product_id: int,
    data: ProductImageRemove,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    """移除一张详情图；仅管理员可操作。"""
    return product_service.remove_product_image(db, product_id, data.url)
