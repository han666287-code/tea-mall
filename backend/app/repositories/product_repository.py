"""商品数据访问层：只包含 SQLAlchemy 查询，不放业务规则。"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product


class ProductRepository:
    """商品查询封装（被 product/cart/order/category 服务复用）。"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def get_locked_by_ids(self, product_ids: list[int]) -> dict[int, Product]:
        """按 id 排序加行锁（FOR UPDATE），返回 {product_id: product}，供下单防超卖。"""
        rows = self.db.scalars(
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        )
        return {product.id: product for product in rows}

    def count_by_category(self, category_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(Product)
                .where(Product.category_id == category_id)
            )
            or 0
        )

    def list_for_page(
        self,
        *,
        category_id: int | None,
        keyword: str | None,
        include_off_sale: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        """按筛选条件分页查询，返回 (products, total)，排序与既有接口一致。"""
        stmt = select(Product)
        if not include_off_sale:
            stmt = stmt.where(Product.is_on_sale.is_(True))
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if keyword:
            stmt = stmt.where(
                or_(
                    Product.name.like(f"%{keyword}%"),
                    Product.description.like(f"%{keyword}%"),
                )
            )
        total = (
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        products = list(
            self.db.scalars(
                stmt.options(selectinload(Product.category))
                .order_by(Product.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return products, total
