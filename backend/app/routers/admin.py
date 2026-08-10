"""管理端接口：订单列表（按状态筛选）、订单状态流转。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.schemas.order import OrderListResponse, OrderResponse, OrderStatusUpdate
from app.services import admin as admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/orders", response_model=OrderListResponse)
def list_orders(
    order_status: str | None = Query(default=None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
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
