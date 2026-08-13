"""密码哈希与 JWT 签发/解析工具。"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

MAX_PASSWORD_UTF8_BYTES = 72


def _ensure_password_within_bcrypt_limit(password: str) -> None:
    """bcrypt 只接受不超过 72 字节的输入，超限直接抛错而非让 bcrypt 异常外泄。"""
    if len(password.encode("utf-8")) > MAX_PASSWORD_UTF8_BYTES:
        raise ValueError(f"password exceeds {MAX_PASSWORD_UTF8_BYTES} UTF-8 bytes")


def hash_password(password: str) -> str:
    """生成 bcrypt 密码哈希。"""
    _ensure_password_within_bcrypt_limit(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    _ensure_password_within_bcrypt_limit(password)
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    """为用户签发 JWT（默认 7 天有效）。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """解析 JWT，无效、过期或缺少 sub/exp 会抛出异常。"""
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"require": ["sub", "exp"]},
    )
