"""V2.0-1.4 密码与用户输入安全回归测试。"""

from uuid import uuid4

import pytest

from app.core.security import hash_password, verify_password
from tests.conftest import client


def unique_username() -> str:
    return f"testpass{uuid4().hex[:8]}"


def register(payload: dict):
    return client.post("/api/auth/register", json=payload)


def login(payload: dict):
    return client.post("/api/auth/login", json=payload)


def base_payload(**overrides):
    payload = {
        "username": unique_username(),
        "password": "password123",
        "nickname": "密码测试",
    }
    payload.update(overrides)
    return payload


def test_register_normal_ascii_password():
    assert register(base_payload()).status_code == 201


def test_register_72_byte_ascii_password_ok():
    assert register(base_payload(password="a" * 72)).status_code == 201


def test_register_73_byte_ascii_password_rejected():
    assert register(base_payload(password="a" * 73)).status_code == 422


def test_register_chinese_password_ok():
    # 2 个汉字(6 字节) + 8 个 ASCII(8 字节) = 14 字节，字符数 10，均合规
    assert register(base_payload(password="密码12345678")).status_code == 201


def test_register_long_chinese_password_rejected():
    # 30 个汉字 = 90 字节，字符数 30 未超 72 但字节超限
    assert register(base_payload(password="密" * 30)).status_code == 422


def test_register_empty_password_rejected():
    assert register(base_payload(password="")).status_code == 422


def test_register_missing_password_rejected():
    payload = base_payload()
    del payload["password"]
    assert register(payload).status_code == 422


def test_register_non_string_password_rejected():
    assert register(base_payload(password=12345678)).status_code == 422


def test_login_normal():
    username = unique_username()
    register({"username": username, "password": "password123", "nickname": "x"})
    assert login({"username": username, "password": "password123"}).status_code == 200


def test_login_wrong_password_400():
    username = unique_username()
    register({"username": username, "password": "password123", "nickname": "x"})
    assert login({"username": username, "password": "wrong-pass"}).status_code == 400


def test_login_overlong_password_rejected_422():
    assert login({"username": "admin", "password": "x" * 73}).status_code == 422


def test_login_empty_password_rejected_422():
    assert login({"username": "admin", "password": ""}).status_code == 422


def test_login_non_string_password_rejected_422():
    assert login({"username": "admin", "password": 12345678}).status_code == 422


def test_hash_password_rejects_overlong_bytes():
    with pytest.raises(ValueError):
        hash_password("x" * 73)


def test_verify_password_rejects_overlong_bytes():
    with pytest.raises(ValueError):
        verify_password("x" * 73, hash_password("password123"))
