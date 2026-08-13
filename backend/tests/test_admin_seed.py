"""V2.0-1.2 管理员账号与密码安全回归测试。

覆盖：环境变量创建管理员、幂等、bcrypt 哈希、可登录、
弱密码/缺失/过短/超长密码拒绝、--reset-admin-password 重置路径。
"""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.models.user import User
from tests.conftest import client
from seed import create_admin, reset_admin_password


def unique_admin_username() -> str:
    return f"testadmin{uuid4().hex[:8]}"


def set_admin_env(monkeypatch, username: str, password: str) -> None:
    monkeypatch.setenv("ADMIN_USERNAME", username)
    monkeypatch.setenv("ADMIN_PASSWORD", password)


def get_user(username: str) -> User | None:
    with SessionLocal() as db:
        return db.scalar(select(User).where(User.username == username))


def login(username: str, password: str):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_create_admin_success_and_login(monkeypatch):
    username = unique_admin_username()
    password = "Test-Admin-Pass-2026!"
    set_admin_env(monkeypatch, username, password)

    create_admin()

    user = get_user(username)
    assert user is not None
    assert user.role == "admin"
    assert user.password_hash.startswith("$2b$")
    assert user.password_hash != password

    # 配置密码可登录，历史弱密码 admin123 不成立
    assert login(username, password).status_code == 200
    assert login(username, "admin123").status_code == 400


def test_create_admin_idempotent(monkeypatch):
    username = unique_admin_username()
    password = "Test-Admin-Pass-2026!"
    set_admin_env(monkeypatch, username, password)

    create_admin()
    first_hash = get_user(username).password_hash
    create_admin()

    with SessionLocal() as db:
        count = len(db.scalars(select(User).where(User.username == username)).all())
    assert count == 1
    assert get_user(username).password_hash == first_hash


@pytest.mark.parametrize(
    "weak_password",
    [
        "admin12345678",  # 包含历史默认 admin123
        "123456789012",   # 命中弱密码名单
    ],
)
def test_create_admin_rejects_weak_password(monkeypatch, weak_password):
    username = unique_admin_username()
    set_admin_env(monkeypatch, username, weak_password)
    with pytest.raises(SystemExit):
        create_admin()
    assert get_user(username) is None


def test_create_admin_rejects_missing_password(monkeypatch):
    username = unique_admin_username()
    monkeypatch.setenv("ADMIN_USERNAME", username)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    with pytest.raises(SystemExit):
        create_admin()
    assert get_user(username) is None


def test_create_admin_rejects_short_password(monkeypatch):
    username = unique_admin_username()
    set_admin_env(monkeypatch, username, "shortpass1")
    with pytest.raises(SystemExit):
        create_admin()
    assert get_user(username) is None


def test_create_admin_rejects_overlong_password(monkeypatch):
    username = unique_admin_username()
    set_admin_env(monkeypatch, username, "x" * 73)
    with pytest.raises(SystemExit):
        create_admin()
    assert get_user(username) is None


def test_reset_admin_password(monkeypatch):
    username = unique_admin_username()
    old_password = "Old-Admin-Pass-2026!"
    new_password = "New-Admin-Pass-2026!"
    set_admin_env(monkeypatch, username, old_password)
    create_admin()
    old_hash = get_user(username).password_hash
    assert login(username, old_password).status_code == 200

    set_admin_env(monkeypatch, username, new_password)
    reset_admin_password()

    user = get_user(username)
    assert user.password_hash != old_hash
    assert user.password_hash.startswith("$2b$")
    assert login(username, old_password).status_code == 400
    assert login(username, new_password).status_code == 200


def test_reset_admin_password_nonexistent_user(monkeypatch):
    username = unique_admin_username()
    set_admin_env(monkeypatch, username, "New-Admin-Pass-2026!")
    with pytest.raises(SystemExit):
        reset_admin_password()
