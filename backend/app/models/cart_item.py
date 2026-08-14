"""购物车条目模型。"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        # 同一用户对同一 SKU 只保留一行，重复加购时累加数量
        UniqueConstraint("user_id", "sku_id", name="uq_cart_user_sku"),
        CheckConstraint("quantity >= 1", name="ck_cart_items_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # product_id 保留为快捷字段（冗余，来源为 sku.product_id）
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    sku_id: Mapped[int] = mapped_column(
        ForeignKey("skus.id", ondelete="CASCADE"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User")
    product = relationship("Product")
    sku = relationship("Sku")
