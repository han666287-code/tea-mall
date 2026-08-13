"""V2.0-1.1 安全配置与 JWT Secret 回归测试。

覆盖：正常 Secret 加载、缺失/过短/已知弱值拒绝启动、
JWT 正常签发与验证、过期 token 拒绝、错误签名拒绝。
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from pydantic import ValidationError

from app.config import WEAK_JWT_MARKERS, WEAK_JWT_SECRETS, Settings, settings
from app.core.security import create_access_token, decode_access_token

VALID_SECRET = "test-only-secret-0123456789abcdefghijklmnopqrstuvwxyz"


def make_settings(**overrides):
    kwargs = {"_env_file": None, "jwt_secret": VALID_SECRET}
    kwargs.update(overrides)
    return Settings(**kwargs)


def test_valid_secret_loads():
    s = make_settings()
    assert s.jwt_secret == VALID_SECRET


def test_missing_secret_rejected(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_short_secret_rejected():
    with pytest.raises(ValidationError):
        make_settings(jwt_secret="short-secret")


@pytest.mark.parametrize(
    "secret",
    [
        *sorted(WEAK_JWT_SECRETS),
        "dev-only-abcdefghijklmnopqrstuvwxyz0123456789",
        "CHANGE-ME-abcdefghijklmnopqrstuvwxyz0123456789",
    ],
)
def test_weak_secret_rejected(secret):
    with pytest.raises(ValidationError):
        make_settings(jwt_secret=secret)


def test_weak_marker_list_covers_known_defaults():
    for secret in WEAK_JWT_SECRETS:
        lowered = secret.lower()
        assert any(marker in lowered for marker in WEAK_JWT_MARKERS)


def test_jwt_roundtrip():
    token = create_access_token(user_id=1)
    payload = decode_access_token(token)
    assert payload["sub"] == "1"


def test_expired_token_rejected():
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": "1", "exp": now - timedelta(seconds=1)},
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_wrong_signature_rejected():
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": "1", "exp": now + timedelta(days=1)},
        "another-secret-that-is-long-enough-0123456789",
        algorithm="HS256",
    )
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token)
