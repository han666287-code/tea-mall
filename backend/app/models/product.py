"""商品模型。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        # 数据一致性：库存与价格不允许为负
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(255), default="")
    is_on_sale: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    category = relationship("Category")
    skus = relationship(
        "Sku",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="Sku.id",
    )
    specs = relationship(
        "ProductSpec",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductSpec.id",
    )
    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order.asc(), ProductImage.id.asc()",
    )

    @property
    def category_name(self) -> str | None:
        """便于响应模型直接输出分类名称。"""
        return self.category.name if self.category else None
