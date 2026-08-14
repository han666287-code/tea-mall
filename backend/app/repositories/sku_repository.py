"""SKU 数据访问层：只包含 SQLAlchemy 查询，不放业务规则。"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product
from app.models.sku import ProductSpecValue, Sku


SKU_LOADS = (
    selectinload(Sku.product).selectinload(Product.category),
    selectinload(Sku.product)
    .selectinload(Product.skus)
    .selectinload(Sku.spec_values)
    .selectinload(ProductSpecValue.spec),
    selectinload(Sku.spec_values).selectinload(ProductSpecValue.spec),
)


class SkuRepository:
    """SKU 查询封装（被 cart/order 服务复用）。"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, sku_id: int) -> Sku | None:
        return self.db.scalar(
            select(Sku).options(*SKU_LOADS).where(Sku.id == sku_id)
        )

    def get_locked_by_ids(self, sku_ids: list[int]) -> dict[int, Sku]:
        """按 id 排序加行锁（FOR UPDATE），返回 {sku_id: Sku}，供下单防超卖。"""
        rows = self.db.scalars(
            select(Sku)
            .options(*SKU_LOADS)
            .where(Sku.id.in_(sku_ids))
            .order_by(Sku.id)
            .with_for_update()
        )
        return {sku.id: sku for sku in rows}
