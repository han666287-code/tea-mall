"""购物车相关的请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    id: int
    quantity: int
    product: ProductResponse
    created_at: datetime

    model_config = {"from_attributes": True}
