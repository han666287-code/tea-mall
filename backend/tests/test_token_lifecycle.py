"""V2.0-3.2 登录与 Token 生命周期测试。

覆盖：Access/Refresh 签发、claims、刷新轮换、旧 refresh 复用失败、
logout 撤销、会话纪元失效、Redis 键 TTL、Redis 故障 503。
"""

from uuid import uuid4

import pytest

from app.config import settings
from app.core import security
from app.services import token_store
from app.services.cache import redis_client
from tests.conftest import client


def unique_username() -> str:
    return f"testtok{uuid4().hex[:8]}"


def register_and_login() -> dict:
    username = unique_username()
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "Token 测试"},
    )
    assert response.status_code == 201
    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login.status_code == 200
    return login.json()


def test_login_returns_access_and_refresh():
    body = register_and_login()
    assert body["token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.access_token_expire_minutes * 60
    assert body["user"]["username"].startswith("testtok")


def test_access_token_works_on_me():
    body = register_and_login()
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert response.status_code == 200


def test_access_token_has_type_jti_ver_claims():
    body = register_and_login()
    payload = security.decode_access_token(body["token"])
    assert payload["type"] == "access"
    assert payload["jti"]
    assert isinstance(payload["ver"], int)
    assert payload["sub"] == str(body["user"]["id"])


def test_refresh_token_cannot_access_api():
    body = register_and_login()
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['refresh_token']}"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "TOKEN_INVALID"


def test_refresh_rotates_and_old_refresh_rejected():
    body = register_and_login()
    response = client.post(
        "/api/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert response.status_code == 200
    new_body = response.json()
    assert new_body["token"]
    assert new_body["refresh_token"] != body["refresh_token"]

    # 旧 refresh 复用失败（轮换后已删除）
    reuse = client.post(
        "/api/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert reuse.status_code == 401
    assert reuse.json()["code"] == "REFRESH_TOKEN_INVALID"

    # 新 refresh 可再次刷新
    again = client.post(
        "/api/auth/refresh", json={"refresh_token": new_body["refresh_token"]}
    )
    assert again.status_code == 200


def test_refresh_with_invalid_token_rejected():
    response = client.post("/api/auth/refresh", json={"refresh_token": "garbage-token"})
    assert response.status_code == 401
    assert response.json()["code"] == "REFRESH_TOKEN_INVALID"


def test_logout_blacklists_access_and_deletes_refresh():
    body = register_and_login()
    headers = {"Authorization": f"Bearer {body['token']}"}
    logout = client.post(
        "/api/auth/logout",
        json={"refresh_token": body["refresh_token"]},
        headers=headers,
    )
    assert logout.status_code == 200

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 401
    assert me.json()["code"] == "TOKEN_INVALID"

    refresh = client.post(
        "/api/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert refresh.status_code == 401


def test_logout_without_refresh_token_still_revokes_access():
    body = register_and_login()
    headers = {"Authorization": f"Bearer {body['token']}"}
    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_epoch_bump_invalidates_all_tokens():
    body = register_and_login()
    payload = security.decode_access_token(body["token"])
    user_id = int(payload["sub"])
    token_store.bump_epoch(user_id)

    me = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert me.status_code == 401

    refresh = client.post(
        "/api/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert refresh.status_code == 401
    assert refresh.json()["code"] == "REFRESH_TOKEN_INVALID"


def test_redis_keys_have_ttl():
    body = register_and_login()
    payload = security.decode_access_token(body["token"])

    refresh_fp = security.hash_refresh_token(body["refresh_token"])
    refresh_ttl = redis_client.ttl(f"auth:refresh:{refresh_fp}")
    assert refresh_ttl > 0
    assert refresh_ttl <= settings.refresh_token_expire_days * 24 * 3600

    client.post(
        "/api/auth/logout",
        json={"refresh_token": body["refresh_token"]},
        headers={"Authorization": f"Bearer {body['token']}"},
    )
    blacklist_ttl = redis_client.ttl(f"auth:blacklist:{payload['jti']}")
    assert blacklist_ttl > 0
    assert blacklist_ttl <= settings.access_token_expire_minutes * 60


def test_redis_failure_returns_503(monkeypatch):
    body = register_and_login()

    def boom(*args, **kwargs):
        raise RuntimeError("redis down")

    monkeypatch.setattr(token_store.redis_client, "get", boom)
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    assert "Traceback" not in response.text


def test_multi_device_independent_sessions():
    """同一用户两次登录产生两个独立会话，互不影响。"""
    username = unique_username()
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "多端"},
    )
    login1 = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    ).json()
    login2 = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    ).json()
    assert login1["refresh_token"] != login2["refresh_token"]

    # 注销设备 1，设备 2 不受影响
    client.post(
        "/api/auth/logout",
        json={"refresh_token": login1["refresh_token"]},
        headers={"Authorization": f"Bearer {login1['token']}"},
    )
    assert (
        client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {login1['token']}"}
        ).status_code
        == 401
    )
    assert (
        client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {login2['token']}"}
        ).status_code
        == 200
    )
    refresh2 = client.post(
        "/api/auth/refresh", json={"refresh_token": login2["refresh_token"]}
    )
    assert refresh2.status_code == 200
