"""V2.0-1.6 测试 Redis 隔离回归测试。"""

from app.config import settings
from app.services import cache


def test_redis_url_points_to_test_db():
    assert settings.testing is True
    assert settings.redis_url.endswith("/15")


def test_cache_client_uses_test_redis_db():
    db = cache.redis_client.connection_pool.connection_kwargs.get("db")
    assert db == 15
