"""管理端接口：订单管理、用户管理（RBAC）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.user import User
from app.schemas.common import MAX_PAGE_SIZE, PageResponse
from app.schemas.order import OrderListResponse, OrderResponse, OrderStatusUpdate
from app.schemas.user import UserResponse, UserRoleUpdate, UserStatusUpdate
from app.services import admin as admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/orders", response_model=OrderListResponse)
def list_orders(
    order_status: str | None = Query(default=None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    """全部订单列表，支持按状态筛选（仅管理员）。"""
    orders, total = admin_service.list_all_orders(db, order_status, page, page_size)
    return OrderListResponse(items=orders, total=total, page=page, page_size=page_size)


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    """更新订单状态，非法流转返回 400（仅管理员）。"""
    return admin_service.update_order_status(db, order_id, data.status)


@router.get("/users", response_model=PageResponse[UserResponse])
def list_users(
    keyword: str | None = Query(default=None, max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    """用户列表，支持关键词搜索与分页（仅管理员）。"""
    users, total = admin_service.list_users(db, keyword, page, page_size)
    return PageResponse(items=users, total=total, page=page, page_size=page_size)


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """禁用/启用用户；禁止操作自己；禁用后该用户全部 Token 失效。"""
    return admin_service.update_user_status(db, admin, user_id, data.status)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """分配/回收管理员角色；禁止修改自己的角色。"""
    return admin_service.update_user_role(db, admin, user_id, data.role)
