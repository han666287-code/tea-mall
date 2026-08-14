"""订单接口：创建、我的订单列表/详情、模拟支付、取消（均需登录，仅本人订单）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse
from app.schemas.common import MAX_PAGE_SIZE
from app.services import order as order_service

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.create_order(db, current_user, data)


@router.get("", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders, total = order_service.list_orders(db, current_user.id, page, page_size)
    return OrderListResponse(items=orders, total=total, page=page, page_size=page_size)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.get_order(db, current_user, order_id)


@router.post("/{order_id}/pay", response_model=OrderResponse)
def pay_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.pay_order(db, current_user, order_id)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.cancel_order(db, current_user, order_id)
