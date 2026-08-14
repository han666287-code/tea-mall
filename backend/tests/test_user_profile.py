"""V2.0-3.3 用户信息与账户安全测试。

覆盖：查询/修改自己、邮箱唯一（排除自身）、清空邮箱、空更新拒绝、
禁止修改 role/username、修改密码（旧密码校验、弱新密码拒绝、
成功后旧 Token 全部失效）、敏感字段不泄露。
"""

from uuid import uuid4

import bcrypt
from sqlalchemy import select

from app.database import SessionLocal
from app.models.user import User
from tests.conftest import client


def unique_username() -> str:
    return f"testprof{uuid4().hex[:8]}"


def unique_email() -> str:
    return f"{uuid4().hex[:10]}@example.com"


def register_and_login(email: str | None = None) -> tuple[str, dict]:
    username = unique_username()
    payload = {"username": username, "password": "password123", "nickname": "资料测试"}
    if email:
        payload["email"] = email
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login.status_code == 200
    return username, login.json()


def headers_of(body: dict) -> dict:
    return {"Authorization": f"Bearer {body['token']}"}


def test_me_returns_profile_without_sensitive_fields():
    _, body = register_and_login()
    response = client.get("/api/auth/me", headers=headers_of(body))
    assert response.status_code == 200
    data = response.json()
    assert "id" in data and "username" in data and "email" in data
    assert "password" not in data and "password_hash" not in data


def test_me_requires_token():
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_update_nickname_ok():
    username, body = register_and_login()
    response = client.put(
        "/api/auth/me", json={"nickname": "新昵称"}, headers=headers_of(body)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "新昵称"
    assert data["username"] == username


def test_update_email_normalized():
    _, body = register_and_login()
    response = client.put(
        "/api/auth/me", json={"email": "  New@Example.COM  "}, headers=headers_of(body)
    )
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"


def test_update_email_taken_returns_400():
    email = unique_email()
    register_and_login(email=email)
    _, body2 = register_and_login()
    response = client.put(
        "/api/auth/me", json={"email": email}, headers=headers_of(body2)
    )
    assert response.status_code == 400
    assert response.json()["code"] == "EMAIL_TAKEN"


def test_update_email_to_own_email_ok():
    email = unique_email()
    _, body = register_and_login(email=email)
    response = client.put(
        "/api/auth/me", json={"email": email}, headers=headers_of(body)
    )
    assert response.status_code == 200
    assert response.json()["email"] == email


def test_clear_email_by_empty_string():
    email = unique_email()
    _, body = register_and_login(email=email)
    response = client.put(
        "/api/auth/me", json={"email": ""}, headers=headers_of(body)
    )
    assert response.status_code == 200
    assert response.json()["email"] is None


def test_empty_update_rejected():
    _, body = register_and_login()
    response = client.put("/api/auth/me", json={}, headers=headers_of(body))
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_extra_fields_role_username_rejected():
    _, body = register_and_login()
    for payload in ({"role": "admin"}, {"username": "hacked"}, {"id": 1}):
        response = client.put("/api/auth/me", json=payload, headers=headers_of(body))
        assert response.status_code == 422, payload


def test_change_password_success_invalidates_all_tokens():
    _, body = register_and_login()
    response = client.put(
        "/api/auth/me/password",
        json={"old_password": "password123", "new_password": "newpass456"},
        headers=headers_of(body),
    )
    assert response.status_code == 200
    assert response.json()["detail"] == "密码修改成功"

    # 旧 access / refresh 全部失效
    me = client.get("/api/auth/me", headers=headers_of(body))
    assert me.status_code == 401
    refresh = client.post(
        "/api/auth/refresh", json={"refresh_token": body["refresh_token"]}
    )
    assert refresh.status_code == 401

    # 新密码可登录，旧密码不可
    assert (
        client.post(
            "/api/auth/login", json={"username": body["user"]["username"], "password": "newpass456"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/login", json={"username": body["user"]["username"], "password": "password123"}
        ).status_code
        == 400
    )


def test_change_password_wrong_old_password():
    _, body = register_and_login()
    response = client.put(
        "/api/auth/me/password",
        json={"old_password": "wrong-old", "new_password": "newpass456"},
        headers=headers_of(body),
    )
    assert response.status_code == 400
    assert response.json()["code"] == "OLD_PASSWORD_INCORRECT"


def test_change_password_weak_new_password():
    _, body = register_and_login()
    response = client.put(
        "/api/auth/me/password",
        json={"old_password": "password123", "new_password": "123"},
        headers=headers_of(body),
    )
    assert response.status_code == 422


def test_password_hash_updated_in_db():
    username, body = register_and_login()
    response = client.put(
        "/api/auth/me/password",
        json={"old_password": "password123", "new_password": "newpass456"},
        headers=headers_of(body),
    )
    assert response.status_code == 200
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        assert user is not None
        assert bcrypt.checkpw(b"newpass456", user.password_hash.encode("utf-8"))
        assert not bcrypt.checkpw(b"password123", user.password_hash.encode("utf-8"))
