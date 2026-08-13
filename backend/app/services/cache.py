"""Redis 缓存工具：分类列表、商品列表/详情（TTL 5 分钟）。

所有方法都做了异常兜底：Redis 不可用时自动退化为直接查数据库，不影响功能。
"""

import json

from redis import Redis

from app.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

CACHE_TTL_SECONDS = 300

KEY_CATEGORIES = "cache:categories"
KEY_PRODUCTS_PREFIX = "cache:products"
KEY_PRODUCT_PREFIX = "cache:product"


def get_json(key: str):
    """读取 JSON 缓存，未命中或异常返回 None。"""
    try:
        value = redis_client.get(key)
    except Exception:
        return None
    if value is None:
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def set_json(key: str, data, ttl: int = CACHE_TTL_SECONDS) -> None:
    """写入 JSON 缓存，失败时静默忽略。"""
    try:
        redis_client.set(key, json.dumps(data, ensure_ascii=False, default=str), ex=ttl)
    except Exception:
        pass


def invalidate(pattern: str) -> None:
    """按通配符删除缓存键。"""
    try:
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
    except Exception:
        pass


def invalidate_categories() -> None:
    """分类数据变更后调用。"""
    invalidate(KEY_CATEGORIES)
    invalidate_products()


def invalidate_products() -> None:
    """商品数据变更后调用（列表与详情缓存全部失效）。"""
    invalidate(f"{KEY_PRODUCTS_PREFIX}:*")
    invalidate(f"{KEY_PRODUCT_PREFIX}:*")


def clear_all() -> None:
    """清空所有业务缓存（仅限测试环境；非测试环境拒绝执行）。"""
    if not settings.testing:
        raise RuntimeError("拒绝执行：clear_all 仅允许在测试环境（TESTING=1）使用")
    invalidate("cache:*")


def product_list_key(
    category_id: int | None,
    keyword: str | None,
    page: int,
    page_size: int,
    include_off_sale: bool,
) -> str:
    category = category_id if category_id is not None else "all"
    kw = keyword if keyword else "all"
    scope = "all" if include_off_sale else "on"
    return f"{KEY_PRODUCTS_PREFIX}:{category}:{kw}:{page}:{page_size}:{scope}"


def product_detail_key(product_id: int) -> str:
    return f"{KEY_PRODUCT_PREFIX}:{product_id}"
