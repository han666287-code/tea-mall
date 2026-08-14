"""分类接口：列表公开，增删改仅管理员。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category as category_service

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """分类列表（公开，带 Redis 缓存）。"""
    return category_service.list_categories(db)


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return category_service.create_category(db, data)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return category_service.update_category(db, category_id, data)


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    category_service.delete_category(db, category_id)
