"""V2.0-1.3 JWT 异常与认证安全回归测试。

覆盖：格式错误/签名错误/过期/缺少 sub/缺少 exp/sub 非法类型
全部统一 401 且不泄露 token 与 payload；公开端点对非法 token 降级为匿名；
正常登录流程不受影响。
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt as pyjwt
import pytest

from app.config import settings
from tests.conftest import client

PROTECTED_URL = "/api/auth/me"
PUBLIC_URL = "/api/products"


def sign(payload: dict, secret: str | None = None) -> str:
    return pyjwt.encode(payload, secret or settings.jwt_secret, algorithm="HS256")


def future_exp() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=1)


def get_me(token: str):
    return client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})


@pytest.mark.parametrize("token", ["not-a-jwt", "a.b.c", ""])
def test_malformed_token_returns_401(token):
    assert get_me(token).status_code == 401


def test_wrong_signature_returns_401():
    token = sign(
        {"sub": "1", "exp": future_exp()},
        secret="another-secret-that-is-long-enough-0123456789",
    )
    assert get_me(token).status_code == 401


def test_expired_token_returns_401():
    token = sign({"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)})
    assert get_me(token).status_code == 401


def test_missing_sub_returns_401():
    token = sign({"exp": future_exp()})
    assert get_me(token).status_code == 401


def test_missing_exp_returns_401():
    token = sign({"sub": "1"})
    assert get_me(token).status_code == 401


def test_sub_object_returns_401():
    token = sign({"sub": {"id": 1}, "exp": future_exp()})
    assert get_me(token).status_code == 401


def test_sub_list_returns_401():
    token = sign({"sub": ["1"], "exp": future_exp()})
    assert get_me(token).status_code == 401


def test_sub_non_numeric_string_returns_401():
    token = sign({"sub": "abc", "exp": future_exp()})
    assert get_me(token).status_code == 401


@pytest.mark.parametrize("sub", [0, -5])
def test_sub_non_positive_number_returns_401(sub):
    token = sign({"sub": sub, "exp": future_exp()})
    assert get_me(token).status_code == 401


def test_sub_number_nonexistent_user_returns_401():
    token = sign({"sub": 99999999, "exp": future_exp()})
    assert get_me(token).status_code == 401


def test_sub_string_nonexistent_user_returns_401():
    token = sign({"sub": "99999999", "exp": future_exp()})
    assert get_me(token).status_code == 401


def test_401_response_does_not_leak_token_or_payload():
    token = sign({"sub": {"id": 1}, "exp": future_exp()})
    response = get_me(token)
    assert response.status_code == 401
    body_text = response.text
    assert token not in body_text
    assert "Traceback" not in body_text
    assert "sub" not in body_text
    assert response.json()["detail"] in {"token 无效或已过期", "未登录或登录已过期"}


def test_optional_endpoint_ignores_malformed_token():
    response = client.get(PUBLIC_URL, headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 200


def test_optional_endpoint_ignores_bad_sub():
    token = sign({"sub": {"id": 1}, "exp": future_exp()})
    response = client.get(PUBLIC_URL, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_valid_token_flow_unaffected():
    username = f"testjwt{uuid4().hex[:8]}"
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "JWT 测试"},
    )
    login_response = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    response = client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == username
