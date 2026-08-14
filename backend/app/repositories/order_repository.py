"""订单数据访问层：只包含 SQLAlchemy 查询，不放业务规则。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.order import Order


class OrderRepository:
    """订单查询封装（被 order/admin 服务复用）。"""

    _LOAD_OPTIONS = (selectinload(Order.items), joinedload(Order.user))

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: int) -> Order | None:
        return self.db.get(Order, order_id, options=self._LOAD_OPTIONS)

    def get_for_user(self, user_id: int, order_id: int) -> Order | None:
        return self.db.scalar(
            select(Order)
            .options(*self._LOAD_OPTIONS)
            .where(Order.id == order_id, Order.user_id == user_id)
        )

    def list_for_user_paginated(
        self, user_id: int, page: int, page_size: int
    ) -> tuple[list[Order], int]:
        total = (
            self.db.scalar(
                select(func.count()).select_from(Order).where(Order.user_id == user_id)
            )
            or 0
        )
        orders = list(
            self.db.scalars(
                select(Order)
                .options(*self._LOAD_OPTIONS)
                .where(Order.user_id == user_id)
                .order_by(Order.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return orders, total

    def list_all_paginated(
        self, order_status: str | None, page: int, page_size: int
    ) -> tuple[list[Order], int]:
        stmt = select(Order)
        if order_status:
            stmt = stmt.where(Order.status == order_status)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        orders = list(
            self.db.scalars(
                stmt.options(*self._LOAD_OPTIONS)
                .order_by(Order.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return orders, total
