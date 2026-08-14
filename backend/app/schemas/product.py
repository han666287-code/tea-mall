"""商品相关的请求/响应模型。"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import PageResponse


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category_id: int
    price: Decimal = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    description: str = Field(default="", max_length=2000)
    image_url: str = Field(default="", max_length=255)
    is_on_sale: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category_id: int | None = None
    price: Decimal | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=2000)
    image_url: str | None = Field(default=None, max_length=255)
    is_on_sale: bool | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    category_id: int
    category_name: str | None = None
    price: Decimal
    stock: int
    description: str
    image_url: str
    is_on_sale: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(PageResponse[ProductResponse]):
    """商品分页响应（字段与前端 ProductListResult 一致）。"""
