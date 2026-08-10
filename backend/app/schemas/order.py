"""订单相关的请求/响应模型。"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    receiver_name: str = Field(min_length=1, max_length=50)
    receiver_phone: str = Field(min_length=1, max_length=20)
    receiver_address: str = Field(min_length=1, max_length=200)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
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
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
