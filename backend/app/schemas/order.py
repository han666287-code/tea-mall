"""订单相关的请求/响应模型。"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import PageResponse


class OrderCreate(BaseModel):
    receiver_name: str = Field(min_length=1, max_length=50)
    receiver_phone: str = Field(min_length=1, max_length=20)
    receiver_address: str = Field(min_length=1, max_length=200)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    sku_id: int | None
    product_name: str
    price: Decimal
    quantity: int
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    order_no: str
    status: str
    total_amount: Decimal
    username: str | None = None
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = {"from_attributes": True}


class OrderListResponse(PageResponse[OrderResponse]):
    """订单分页响应（字段与前端 OrderListResult 一致）。"""


class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "paid", "shipped", "completed", "cancelled"]
