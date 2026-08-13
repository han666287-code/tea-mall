"""用户认证接口测试：注册、登录、当前用户鉴权。"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt as pyjwt
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def unique_username() -> str:
    return f"testuser{uuid4().hex[:8]}"


def register_user(username: str, password: str = "password123", nickname: str = "测试用户"):
    return client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "nickname": nickname},
    )


def login(username: str, password: str = "password123"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_register_success():
    response = register_user(unique_username())
    assert response.status_code == 201
    data = response.json()
    assert data["username"].startswith("testuser")
    assert data["role"] == "user"
    assert "password" not in data


def test_register_duplicate_username():
    username = unique_username()
    assert register_user(username).status_code == 201
    response = register_user(username)
    assert response.status_code == 400
    assert response.json()["detail"] == "用户名已存在"


def test_register_password_too_short():
    response = register_user(unique_username(), password="123")
    assert response.status_code == 422


def test_login_success():
    username = unique_username()
    register_user(username)
    response = login(username)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["username"] == username


def test_login_wrong_password():
    username = unique_username()
    register_user(username)
    response = login(username, password="wrong-password")
    assert response.status_code == 400
    assert response.json()["detail"] == "用户名或密码错误"


def test_me_without_token():
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_token():
    username = unique_username()
    register_user(username)
    token = login(username).json()["token"]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == username


def test_me_with_invalid_token():
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-valid-token"})
    assert response.status_code == 401


def test_me_with_expired_token():
    now = datetime.now(timezone.utc)
    token = pyjwt.encode(
        {"sub": "1", "exp": now - timedelta(seconds=1)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
