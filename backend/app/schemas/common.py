"""通用 Schema：分页上限常量与统一分页响应基类。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

# 全站统一的最大 page_size，避免单次查询拉取过多数据
MAX_PAGE_SIZE = 50

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """统一分页响应：items/total/page/page_size（字段名与前端类型保持一致）。"""

    items: list[T]
    total: int
    page: int
    page_size: int
