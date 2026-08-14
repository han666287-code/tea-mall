"""V2.0-3.5 用户状态与异常账户处理测试。"""

from uuid import uuid4

from sqlalchemy import select

from app.database import SessionLocal
from app.models.user import User
from tests.conftest import client


def unique_username() -> str:
    return f"teststat{uuid4().hex[:8]}"


def register_and_login() -> tuple[str, dict]:
    username = unique_username()
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "状态测试"},
    )
    assert response.status_code == 201
    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login.status_code == 200
    return username, login.json()


def set_status_in_db(username: str, status: str) -> None:
    """直接改库状态（绕过管理端 API，不触发 epoch 递增）。"""
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        assert user is not None
        user.status = status
        db.commit()


def test_active_user_accesses_protected_api():
    _, body = register_and_login()
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert response.status_code == 200


def test_disabled_user_token_rejected_without_epoch_bump():
    """直接改库禁用（Token 纪元未变）：认证仍拦截，证明不依赖 JWT 本身。"""
    username, body = register_and_login()
    set_status_in_db(username, "disabled")
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "ACCOUNT_DISABLED"


def test_disabled_user_optional_endpoint_treated_as_anonymous():
    username, body = register_and_login()
    set_status_in_db(username, "disabled")
    response = client.get(
        "/api/products", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert response.status_code == 200


def test_admin_disable_blocks_login_refresh_and_sessions(admin_headers):
    username, body = register_and_login()
    uid = client.get(
        f"/api/admin/users?keyword={username}", headers=admin_headers
    ).json()["items"][0]["id"]
    client.patch(
        f"/api/admin/users/{uid}/status",
        json={"status": "disabled"},
        headers=admin_headers,
    )

    # 旧 access 已失效
    me = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert me.status_code == 401

    # 重新登录被拒：403 ACCOUNT_DISABLED
    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login.status_code == 403
    assert login.json()["code"] == "ACCOUNT_DISABLED"

    # refresh 被拒
    refresh = client.post(
        "/api/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert refresh.status_code in (401, 403)

    # 启用后恢复登录
    client.patch(
        f"/api/admin/users/{uid}/status",
        json={"status": "active"},
        headers=admin_headers,
    )
    assert (
        client.post(
            "/api/auth/login", json={"username": username, "password": "password123"}
        ).status_code
        == 200
    )


def test_regular_user_cannot_change_status_via_profile():
    _, body = register_and_login()
    response = client.put(
        "/api/auth/me",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {body['token']}"},
    )
    assert response.status_code == 422
