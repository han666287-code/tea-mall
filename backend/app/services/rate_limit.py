"""登录限流：基于 Redis 固定窗口计数器，键前缀 `auth:rate:`。

设计要点：
- 同一 IP / 用户名在窗口内请求数超过阈值时返回 429 `RATE_LIMITED`；
- 首次请求通过 `SET NX EX` 建键并携带 TTL，窗口过期自动恢复，键不无限积累；
- Redis 异常 fail-open：记录日志并放行，避免限流器故障误伤正常登录；
- 错误文案为通用提示，不泄露用户名/密码等敏感认证信息。
"""

import logging

from fastapi import Request

from app.config import settings
from app.core.exceptions import BusinessException
from app.services.cache import redis_client

PREFIX_RATE = "auth:rate:"
RATE_LIMITED_DETAIL = "请求过于频繁，请稍后再试"

logger = logging.getLogger("uvicorn.error")


def _client_ip(request: Request) -> str:
    """取客户端 IP：优先 X-Forwarded-For 首值（nginx 代理场景），否则直连地址。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",", 1)[0].strip()
        if first:
            return first
    if request.client is not None:
        return request.client.host
    return "unknown"


def _increment_and_check(key: str, max_attempts: int, window_seconds: int) -> None:
    """固定窗口计数并检查阈值；0 或负数视为关闭该维度限流。"""
    if max_attempts <= 0 or window_seconds <= 0:
        return
    try:
        created = redis_client.set(key, 1, ex=window_seconds, nx=True)
        count = 1 if created else int(redis_client.incr(key))
    except Exception:
        logger.warning("登录限流不可用，已放行请求：%s", key)
        return
    if count > max_attempts:
        raise BusinessException("RATE_LIMITED", RATE_LIMITED_DETAIL, status_code=429)


def check_login_rate_limit(username: str, request: Request) -> None:
    """登录接口限流：先按 IP、再按用户名累计，任一维度超限即返回 429。"""
    _increment_and_check(
        f"{PREFIX_RATE}login:ip:{_client_ip(request)}",
        settings.login_rate_limit_max_per_ip,
        settings.login_rate_limit_window_seconds,
    )
    _increment_and_check(
        f"{PREFIX_RATE}login:user:{username.strip().lower()}",
        settings.login_rate_limit_max_per_user,
        settings.login_rate_limit_window_seconds,
    )
