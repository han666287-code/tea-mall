"""Redis 缓存工具：分类列表、商品列表/详情。

键名注册表（V2.0-6 键名规范）：
- ``cache:categories``                            分类列表
- ``cache:products:{category|all}:{kw|all}:{page}:{page_size}:{scope}``
                                                   商品列表（scope: on=仅上架 / all=含下架）
- ``cache:product:{id}``                           商品详情（仅上架商品落缓存）
- ``auth:*``                                       认证专用命名空间（token_store 独占，本模块不得写入）

设计约束：
1. 缓存不是数据源：MySQL 始终是权威，缓存只加速读。
2. TTL 必须显式：商品/分类缓存统一使用 ``settings.product_cache_ttl_seconds``
   （默认 300 秒，<=0 时回退默认值并告警）。
3. Redis 故障降级：商品/分类缓存读失败回退 MySQL、写失败不影响业务；
   认证链路（token_store）保持 fail-closed（503），本模块不得改变其语义。
4. 日志只记录操作类型与异常类，不记录 Key 值、Token 等敏感内容。
"""

import json
import logging

from redis import Redis

from app.config import settings

logger = logging.getLogger("app.cache")

# 统一客户端：业务缓存与认证会话共用；短超时保证 Redis 故障时快速失败、不拖垮请求
redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)

DEFAULT_CACHE_TTL_SECONDS = 300

KEY_CATEGORIES = "cache:categories"
KEY_PRODUCTS_PREFIX = "cache:products"
KEY_PRODUCT_PREFIX = "cache:product"


def _ttl_seconds() -> int:
    """商品/分类缓存 TTL；配置缺失或 <=0 时回退默认值并告警。"""
    ttl = settings.product_cache_ttl_seconds
    if ttl is None or ttl <= 0:
        logger.warning(
            "PRODUCT_CACHE_TTL_SECONDS 非法（%s），回退默认 %s 秒",
            ttl,
            DEFAULT_CACHE_TTL_SECONDS,
        )
        return DEFAULT_CACHE_TTL_SECONDS
    return ttl


def get_json(key: str):
    """读取 JSON 缓存，未命中或 Redis 异常返回 None（调用方回退 MySQL）。"""
    try:
        value = redis_client.get(key)
    except Exception as exc:
        logger.warning("cache get 失败，回退数据库查询：%s", type(exc).__name__)
        return None
    if value is None:
        return None
    try:
        return json.loads(value)
    except Exception as exc:
        logger.warning("cache get 反序列化失败：%s", type(exc).__name__)
        return None


def set_json(key: str, data, ttl: int | None = None) -> None:
    """写入 JSON 缓存，失败时记录日志但不影响业务（调用方继续返回 MySQL 数据）。"""
    try:
        redis_client.set(
            key,
            json.dumps(data, ensure_ascii=False, default=str),
            ex=_ttl_seconds() if ttl is None else ttl,
        )
    except Exception as exc:
        logger.warning("cache set 失败：%s", type(exc).__name__)


def delete(key: str) -> None:
    """删除单个缓存键，失败仅记日志。"""
    try:
        redis_client.delete(key)
    except Exception as exc:
        logger.warning("cache delete 失败：%s", type(exc).__name__)


def exists(key: str) -> bool:
    """判断缓存键是否存在；Redis 异常时按不存在处理（不阻断业务）。"""
    try:
        return bool(redis_client.exists(key))
    except Exception as exc:
        logger.warning("cache exists 失败：%s", type(exc).__name__)
        return False


def invalidate(pattern: str) -> None:
    """按通配符删除缓存键，失败仅记日志。"""
    try:
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
    except Exception as exc:
        logger.warning("cache invalidate 失败：%s", type(exc).__name__)


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
