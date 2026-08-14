"""SKU 与规格模型：商品 → SKU → 规格/规格值。

结构：
    products (1) ── (N) product_specs ── (N) product_spec_values
    products (1) ── (N) skus ── (N) sku_spec_values (N) ── (1) product_spec_values

SKU 独立决定价格与库存；同一商品所有 SKU 共用同一组规格名，
每个 SKU 每个规格取一个值，组合唯一由 skus.spec_signature 保证。
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductSpec(Base):
    """商品级规格名（如：净含量、包装）。"""

    __tablename__ = "product_specs"
    __table_args__ = (
        UniqueConstraint("product_id", "name", name="uq_product_specs_product_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product = relationship("Product", back_populates="specs")
    values = relationship(
        "ProductSpecValue",
        back_populates="spec",
        cascade="all, delete-orphan",
        order_by="ProductSpecValue.id",
    )


class ProductSpecValue(Base):
    """规格值（如：100g），归属于某个规格名。"""

    __tablename__ = "product_spec_values"
    __table_args__ = (
        UniqueConstraint("spec_id", "value", name="uq_product_spec_values_spec_value"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    spec_id: Mapped[int] = mapped_column(
        ForeignKey("product_specs.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[str] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    spec = relationship("ProductSpec", back_populates="values")
    skus = relationship(
        "Sku",
        secondary="sku_spec_values",
        back_populates="spec_values",
        order_by="Sku.id",
    )


class Sku(Base):
    """SKU：独立价格与库存，通过 sku_spec_values 关联规格值。"""

    __tablename__ = "skus"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_skus_price_non_negative"),
        CheckConstraint("stock >= 0", name="ck_skus_stock_non_negative"),
        UniqueConstraint("product_id", "sku_code", name="uq_skus_product_sku_code"),
        UniqueConstraint(
            "product_id", "spec_signature", name="uq_skus_product_spec_signature"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    sku_code: Mapped[str] = mapped_column(String(64))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    # 排序后的规格值 id 串，唯一约束防止同商品重复组合
    spec_signature: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    product = relationship("Product", back_populates="skus")
    spec_values = relationship(
        "ProductSpecValue",
        secondary="sku_spec_values",
        back_populates="skus",
        order_by="ProductSpecValue.id",
    )

    @property
    def specs(self) -> list[dict[str, str]]:
        """按规格排序输出 [{name, value}]，供响应模型直接使用。"""
        items = []
        for spec_value in sorted(
            self.spec_values,
            key=lambda sv: (
                sv.spec.sort_order if sv.spec else 0,
                sv.spec.id if sv.spec else 0,
                sv.sort_order,
                sv.id,
            ),
        ):
            items.append({"name": spec_value.spec.name, "value": spec_value.value})
        return items


class SkuSpecValue(Base):
    """SKU 与规格值的多对多关联。"""

    __tablename__ = "sku_spec_values"
    __table_args__ = (
        # 按规格值反向查询（如清理孤立规格值）需要索引
        Index("ix_sku_spec_values_spec_value_id", "spec_value_id"),
    )

    sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id", ondelete="CASCADE"), primary_key=True
    )
    spec_value_id: Mapped[int] = mapped_column(
        ForeignKey("product_spec_values.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
