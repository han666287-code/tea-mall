"""商品相关的请求/响应模型。"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import PageResponse


class SkuSpecItem(BaseModel):
    """SKU 的单个规格名/值。"""

    name: str = Field(min_length=1, max_length=50)
    value: str = Field(min_length=1, max_length=100)


class SkuPayload(BaseModel):
    """创建/替换 SKU 的载荷；sku_code 缺省时由服务层自动生成。"""

    sku_code: str | None = Field(default=None, min_length=1, max_length=64)
    price: Decimal = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    is_active: bool = True
    specs: list[SkuSpecItem] = Field(default_factory=list, max_length=20)


class SkuResponse(BaseModel):
    """SKU 响应：独立价格/库存，specs 为 [{name, value}]。"""

    id: int
    product_id: int
    sku_code: str
    price: Decimal
    stock: int
    is_active: bool
    specs: list[SkuSpecItem] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductImageResponse(BaseModel):
    id: int
    url: str
    kind: str
    sort_order: int

    model_config = {"from_attributes": True}


class ProductImageRemove(BaseModel):
    url: str = Field(min_length=1, max_length=255)


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category_id: int
    price: Decimal = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    description: str = Field(default="", max_length=2000)
    image_url: str = Field(default="", max_length=255)
    is_on_sale: bool = True
    # 可选：创建商品时直接携带 SKU 列表；缺省时自动生成默认 SKU
    skus: list[SkuPayload] | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category_id: int | None = None
    price: Decimal | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=2000)
    image_url: str | None = Field(default=None, max_length=255)
    is_on_sale: bool | None = None
    # 可选：整体替换 SKU 列表；price/stock 仅单 SKU 商品可直接修改
    skus: list[SkuPayload] | None = None


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
    skus: list[SkuResponse]
    images: list[ProductImageResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(PageResponse[ProductResponse]):
    """商品分页响应（字段与前端 ProductListResult 一致）。"""
