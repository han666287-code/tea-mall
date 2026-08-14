"""密码哈希与 JWT 签发/解析工具。"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt

from app.config import settings

MAX_PASSWORD_UTF8_BYTES = 72
ACCESS_TOKEN_TYPE = "access"


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


def create_access_token(user_id: int, epoch: int = 0) -> str:
    """签发 Access Token：含 type/jti/ver，有效期 ACCESS_TOKEN_EXPIRE_MINUTES。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "jti": uuid4().hex,
        "ver": epoch,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token() -> str:
    """生成 Refresh Token 明文（仅返回一次，Redis 只存指纹）。"""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Refresh Token 的 SHA-256 指纹。"""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> dict:
    """解析 JWT，无效、过期或缺少 sub/exp 会抛出异常。"""
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"require": ["sub", "exp"]},
    )
