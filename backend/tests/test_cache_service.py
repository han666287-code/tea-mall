"""V2.0-6.1 Redis Cache 基础封装测试：连接、get/set/delete/exists、TTL、键名、故障兜底。"""

import pytest

from app.config import settings
from app.services import cache


def _sample_data() -> dict:
    return {"id": 1, "name": "测试商品", "price": "10.00", "tags": ["茶", "绿茶"]}


def test_cache_client_uses_test_redis():
    """缓存客户端必须指向测试 Redis（DB15），且带快速失败超时。"""
    pool_kwargs = cache.redis_client.connection_pool.connection_kwargs
    assert settings.testing is True
    assert settings.redis_url.endswith("/15")
    assert pool_kwargs.get("db") == 15
    assert pool_kwargs.get("socket_connect_timeout") == 2
    assert pool_kwargs.get("socket_timeout") == 2


def test_set_get_roundtrip():
    key = "cache:test:roundtrip"
    data = _sample_data()
    cache.set_json(key, data)
    assert cache.get_json(key) == data


def test_get_missing_returns_none():
    assert cache.get_json("cache:test:missing") is None


def test_delete_removes_key():
    key = "cache:test:delete"
    cache.set_json(key, _sample_data())
    assert cache.exists(key) is True
    cache.delete(key)
    assert cache.exists(key) is False
    assert cache.get_json(key) is None


def test_exists_false_for_missing_key():
    assert cache.exists("cache:test:never-exists") is False


def test_set_json_ttl_matches_config():
    key = "cache:test:ttl"
    cache.set_json(key, _sample_data())
    ttl = cache.redis_client.ttl(key)
    assert ttl > 0
    assert ttl <= settings.product_cache_ttl_seconds


def test_set_json_ttl_fallback_when_config_invalid(monkeypatch):
    """配置 <=0 时回退默认 300 秒并仍正常写入。"""
    monkeypatch.setattr(settings, "product_cache_ttl_seconds", 0)
    key = "cache:test:ttl-fallback"
    cache.set_json(key, _sample_data())
    ttl = cache.redis_client.ttl(key)
    assert ttl == cache.DEFAULT_CACHE_TTL_SECONDS


def test_product_list_key_format():
    key = cache.product_list_key(
        category_id=3,
        keyword="龙井",
        page=2,
        page_size=12,
        include_off_sale=False,
    )
    assert key == "cache:products:3:龙井:2:12:on"


def test_product_list_key_defaults():
    key = cache.product_list_key(
        category_id=None,
        keyword=None,
        page=1,
        page_size=12,
        include_off_sale=True,
    )
    assert key == "cache:products:all:all:1:12:all"


def test_product_detail_key_format():
    assert cache.product_detail_key(42) == "cache:product:42"


def test_business_cache_keys_do_not_collide_with_auth_namespace():
    """业务缓存与认证 Key 命名空间隔离，互不扫描/互不删除。"""
    cache.set_json("cache:test:namespace", _sample_data())
    cache.redis_client.set("auth:test:namespace", "keep")
    cache.invalidate("cache:*")
    assert cache.redis_client.exists("cache:test:namespace") == 0
    assert cache.redis_client.exists("auth:test:namespace") == 1
    cache.redis_client.delete("auth:test:namespace")


def test_get_json_failure_falls_back_to_none(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("redis down")

    monkeypatch.setattr(cache.redis_client, "get", boom)
    assert cache.get_json("cache:test:boom") is None


def test_set_json_failure_is_silent(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("redis down")

    monkeypatch.setattr(cache.redis_client, "set", boom)
    # 不抛异常，调用方继续返回 MySQL 数据
    cache.set_json("cache:test:boom", _sample_data())


def test_delete_and_exists_failure_are_handled(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("redis down")

    monkeypatch.setattr(cache.redis_client, "delete", boom)
    monkeypatch.setattr(cache.redis_client, "exists", boom)
    cache.delete("cache:test:boom")
    assert cache.exists("cache:test:boom") is False
