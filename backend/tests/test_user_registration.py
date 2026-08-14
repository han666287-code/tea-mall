"""V2.0-3.1 用户注册体系测试。

覆盖：带邮箱注册、重复邮箱、邮箱格式/长度校验、规范化、
空邮箱转 None、密码只存 bcrypt Hash、响应无敏感字段、数据库唯一约束。
"""

from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError as SAIntegrityError

from app.database import SessionLocal
from app.main import app
from app.models.user import User

client = TestClient(app)


def unique_username() -> str:
    return f"testreg{uuid4().hex[:8]}"


def unique_email() -> str:
    return f"{uuid4().hex[:10]}@example.com"


def register(
    username: str,
    password: str = "password123",
    nickname: str = "注册测试",
    email: str | None = None,
):
    payload = {"username": username, "password": password, "nickname": nickname}
    if email is not None:
        payload["email"] = email
    return client.post("/api/auth/register", json=payload)


def test_register_with_email_success():
    email = unique_email()
    response = register(unique_username(), email=email)
    assert response.status_code == 201
    assert response.json()["email"] == email
    assert response.json()["role"] == "user"


def test_register_duplicate_email_returns_400():
    email = unique_email()
    assert register(unique_username(), email=email).status_code == 201
    response = register(unique_username(), email=email)
    assert response.status_code == 400
    assert response.json()["code"] == "EMAIL_TAKEN"
    assert response.json()["detail"] == "邮箱已被注册"


def test_register_invalid_email_returns_422():
    response = register(unique_username(), email="not-an-email")
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_register_email_too_long_returns_422():
    response = register(unique_username(), email=f"{'a' * 130}@example.com")
    assert response.status_code == 422


def test_register_email_normalized():
    response = register(unique_username(), email="  User@Example.COM  ")
    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"


def test_register_empty_email_becomes_null():
    response = register(unique_username(), email="")
    assert response.status_code == 201
    assert response.json()["email"] is None


def test_register_without_email_keeps_null():
    response = register(unique_username())
    assert response.status_code == 201
    assert response.json()["email"] is None


def test_password_stored_as_hash_not_plaintext():
    username = unique_username()
    password = "password123"
    assert register(username, password=password).status_code == 201
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        assert user is not None
        assert user.password_hash != password
        assert user.password_hash.startswith("$2")
        assert bcrypt.checkpw(
            password.encode("utf-8"), user.password_hash.encode("utf-8")
        )


def test_register_response_has_no_password_fields():
    response = register(unique_username(), email=unique_email())
    body = response.json()
    assert "password" not in body
    assert "password_hash" not in body


def test_db_unique_constraint_blocks_duplicate_email():
    """数据库唯一索引真实生效：绕过应用层直插重复邮箱必须抛 IntegrityError。"""
    email = unique_email()
    assert register(unique_username(), email=email).status_code == 201
    with pytest.raises(SAIntegrityError):
        with SessionLocal() as db:
            db.add(
                User(
                    username=unique_username(),
                    password_hash=bcrypt.hashpw(
                        b"password123", bcrypt.gensalt()
                    ).decode("utf-8"),
                    email=email,
                )
            )
            db.commit()


def test_register_duplicate_email_with_direct_insert_returns_400_not_500():
    """邮箱冲突数据来自数据库直插时，注册接口仍返回稳定业务码而非 500。"""
    email = unique_email()
    with SessionLocal() as db:
        db.add(
            User(
                username=unique_username(),
                password_hash=bcrypt.hashpw(
                    b"password123", bcrypt.gensalt()
                ).decode("utf-8"),
                email=email,
            )
        )
        db.commit()
    response = register(unique_username(), email=email)
    assert response.status_code == 400
    assert response.json()["code"] == "EMAIL_TAKEN"
