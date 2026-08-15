"""V2.0-7.2 认证与权限安全测试：缺口补充。

覆盖：
- 提示词第 10 项：Access Token 过期后可按设计正常 Refresh；
- 安全要求：用户不能通过修改请求参数（注册携带 role=admin）提升权限。
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt as pyjwt

from app.config import settings
from tests.conftest import client


def unique_username() -> str:
    return f"testp7{uuid4().hex[:8]}"


def register_and_login() -> dict:
    username = unique_username()
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "阶段七用户"},
    )
    assert response.status_code == 201
    return client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    ).json()


def make_expired_access_token(token: str) -> str:
    """保留原 claims（sub/type/jti/ver 等），仅将 exp 改为过去时间。"""
    payload = pyjwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    payload["exp"] = int(
        (datetime.now(timezone.utc) - timedelta(seconds=1)).timestamp()
    )
    return pyjwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def test_expired_access_token_refresh_succeeds():
    """过期 Access 访问返回 401，用有效 Refresh 正常换发并访问业务接口。"""
    body = register_and_login()
    expired = make_expired_access_token(body["token"])
    headers = {"Authorization": f"Bearer {expired}"}

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 401
    assert me.json()["code"] == "TOKEN_INVALID"

    refreshed = client.post(
        "/api/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert refreshed.status_code == 200
    new_body = refreshed.json()
    assert new_body["token"]
    assert new_body["refresh_token"] != body["refresh_token"]

    me_again = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {new_body['token']}"}
    )
    assert me_again.status_code == 200

    # 换发后旧 refresh 已轮换失效（回归既有设计）
    reuse = client.post(
        "/api/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert reuse.status_code == 401
    assert reuse.json()["code"] == "REFRESH_TOKEN_INVALID"


def test_register_payload_role_field_cannot_promote():
    """注册请求携带 role=admin 被忽略，账号仍为普通用户，Admin 接口返回 403。"""
    username = unique_username()
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "nickname": "尝试提权",
            "role": "admin",
        },
    )
    assert response.status_code == 201

    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "user"

    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.get("/api/auth/me", headers=headers).json()["role"] == "user"

    admin = client.get("/api/admin/users", headers=headers)
    assert admin.status_code == 403
