"""Redis 会话存储：会话纪元、Refresh Token、Access Token 黑名单。

认证链路对 Redis 的读写失败一律 fail-closed（503 SERVICE_UNAVAILABLE），
不允许因缓存故障放行失效令牌；refresh/blacklist 键全部带 TTL，避免无限积累。
"""

import json

from app.config import settings
from app.core.exceptions import BusinessException
from app.core.security import hash_refresh_token
from app.services.cache import redis_client

PREFIX_REFRESH = "auth:refresh:"
PREFIX_EPOCH = "auth:epoch:"
PREFIX_BLACKLIST = "auth:blacklist:"

_SERVICE_UNAVAILABLE = "认证服务暂时不可用，请稍后重试"


def _unavailable() -> BusinessException:
    return BusinessException(
        "SERVICE_UNAVAILABLE", _SERVICE_UNAVAILABLE, status_code=503
    )


def get_epoch(user_id: int) -> int:
    """读取用户会话纪元；缺失视为 0。"""
    try:
        value = redis_client.get(f"{PREFIX_EPOCH}{user_id}")
    except Exception:
        raise _unavailable()
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def bump_epoch(user_id: int) -> int:
    """会话纪元 +1：使该用户所有已签发的 Access/Refresh 立即失效。"""
    try:
        return int(redis_client.incr(f"{PREFIX_EPOCH}{user_id}"))
    except Exception:
        raise _unavailable()


def store_refresh_token(token: str, user_id: int, epoch: int) -> None:
    """保存 Refresh Token 指纹，TTL = REFRESH_TOKEN_EXPIRE_DAYS。"""
    payload = json.dumps({"user_id": user_id, "ver": epoch})
    try:
        redis_client.set(
            f"{PREFIX_REFRESH}{hash_refresh_token(token)}",
            payload,
            ex=settings.refresh_token_expire_days * 24 * 3600,
        )
    except Exception:
        raise _unavailable()


def get_refresh_token_data(token: str) -> dict | None:
    """按指纹读取 Refresh Token 数据；不存在返回 None。"""
    try:
        raw = redis_client.get(f"{PREFIX_REFRESH}{hash_refresh_token(token)}")
    except Exception:
        raise _unavailable()
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def delete_refresh_token(token: str) -> None:
    """删除指定 Refresh Token（轮换 / logout / 失效时调用）。"""
    try:
        redis_client.delete(f"{PREFIX_REFRESH}{hash_refresh_token(token)}")
    except Exception:
        raise _unavailable()


def blacklist_access_jti(jti: str, ttl_seconds: int) -> None:
    """将 Access Token 的 jti 加入黑名单，TTL = 剩余有效期。"""
    if ttl_seconds <= 0:
        return
    try:
        redis_client.set(f"{PREFIX_BLACKLIST}{jti}", "1", ex=ttl_seconds)
    except Exception:
        raise _unavailable()


def is_access_blacklisted(jti: str) -> bool:
    try:
        return bool(redis_client.exists(f"{PREFIX_BLACKLIST}{jti}"))
    except Exception:
        raise _unavailable()
