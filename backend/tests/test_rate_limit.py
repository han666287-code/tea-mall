"""V2.0-5.4 登录限流测试。

覆盖：正常登录不受影响、连续错误登录触发用户阈值 429、
同一 IP 高频请求触发 IP 阈值、X-Forwarded-For 取首值、
删除 Redis 键模拟窗口过期后恢复、rate 键存在 TTL、Redis 故障 fail-open。
"""

from uuid import uuid4

from app.config import settings
from app.services import rate_limit
from app.services.cache import redis_client
from tests.conftest import client


def unique_username() -> str:
    return f"testratelimit{uuid4().hex[:8]}"


def register_user(username: str, password: str = "password123") -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "nickname": "限流测试"},
    )
    assert response.status_code == 201


def login(username: str, password: str = "password123", headers: dict | None = None):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
        headers=headers,
    )


def test_normal_login_unaffected():
    """正常用户登录不受限流影响（默认阈值内多次登录均成功）。"""
    username = unique_username()
    register_user(username)
    assert login(username).status_code == 200
    assert login(username).status_code == 200


def test_consecutive_wrong_logins_trigger_user_limit(monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_max_per_user", 3)
    username = unique_username()

    for _ in range(3):
        response = login(username, password="wrongpass")
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_CREDENTIALS"

    blocked = login(username, password="wrongpass")
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "RATE_LIMITED"
    assert blocked.json()["detail"] == "请求过于频繁，请稍后再试"
    assert "wrongpass" not in blocked.text


def test_ip_high_frequency_trigger(monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_max_per_ip", 3)
    monkeypatch.setattr(settings, "login_rate_limit_max_per_user", 100)

    for _ in range(3):
        assert login(unique_username(), password="wrongpass").status_code == 400

    blocked = login(unique_username(), password="wrongpass")
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "RATE_LIMITED"


def test_x_forwarded_for_first_value_used(monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_max_per_ip", 1)

    first = login(
        unique_username(),
        password="wrongpass",
        headers={"X-Forwarded-For": "203.0.113.9"},
    )
    assert first.status_code == 400

    blocked = login(
        unique_username(),
        password="wrongpass",
        headers={"X-Forwarded-For": "203.0.113.9"},
    )
    assert blocked.status_code == 429

    other_ip = login(
        unique_username(),
        password="wrongpass",
        headers={"X-Forwarded-For": "198.51.100.7"},
    )
    assert other_ip.status_code == 400


def test_rate_limit_recovers_after_window_expiry(monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_max_per_user", 2)
    username = unique_username()
    register_user(username)

    for _ in range(2):
        assert login(username, password="wrongpass").status_code == 400
    assert login(username, password="wrongpass").status_code == 429

    # 删除 Redis 键模拟窗口过期，恢复后可正常登录
    redis_client.delete(
        f"auth:rate:login:user:{username.lower()}",
        "auth:rate:login:ip:testclient",
    )
    assert login(username).status_code == 200


def test_rate_limit_keys_have_ttl():
    username = unique_username()
    login(username, password="wrongpass")

    window = settings.login_rate_limit_window_seconds
    user_ttl = redis_client.ttl(f"auth:rate:login:user:{username.lower()}")
    ip_ttl = redis_client.ttl("auth:rate:login:ip:testclient")
    assert user_ttl > 0
    assert user_ttl <= window
    assert ip_ttl > 0
    assert ip_ttl <= window


def test_redis_failure_fails_open(monkeypatch):
    """Redis 限流键写入失败时放行，不影响正常登录。"""
    username = unique_username()
    register_user(username)

    class _BoomRedis:
        def set(self, *args, **kwargs):
            raise RuntimeError("redis down")

        def incr(self, *args, **kwargs):
            raise RuntimeError("redis down")

    monkeypatch.setattr(rate_limit, "redis_client", _BoomRedis())
    assert login(username).status_code == 200
