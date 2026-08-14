"""FastAPI 依赖：从请求中解析当前登录用户。"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.core.security import ACCESS_TOKEN_TYPE, decode_access_token
from app.database import get_db
from app.models.user import User
from app.services import token_store

# auto_error=False：Authorization 头缺失时返回 None，由我们统一返回 401
bearer_scheme = HTTPBearer(auto_error=False)

UNAUTHORIZED_DETAIL = "token 无效或已过期"


def _extract_user_id(payload: dict) -> int | None:
    """从 JWT payload 提取用户 ID；sub 缺失或非法时返回 None。"""
    sub = payload.get("sub")
    if sub is None or isinstance(sub, bool):
        return None
    if isinstance(sub, int):
        value = sub
    elif isinstance(sub, str) and sub.isdigit():
        value = int(sub)
    else:
        return None
    if value <= 0:
        return None
    return value


def _auth_error(detail: str = "token 无效或已过期") -> BusinessException:
    """统一认证失败：401 + 稳定错误码 TOKEN_INVALID。"""
    return BusinessException("TOKEN_INVALID", detail, status_code=401)


def _validate_access_payload(payload: dict) -> tuple[int, str, int]:
    """校验 Access Token 的 type/jti/ver，返回 (user_id, jti, ver)。"""
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise _auth_error()
    user_id = _extract_user_id(payload)
    jti = payload.get("jti")
    ver = payload.get("ver")
    if user_id is None or not isinstance(jti, str) or not jti:
        raise _auth_error()
    if not isinstance(ver, int):
        raise _auth_error()
    return user_id, jti, ver


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """未携带有效 token 时返回 401。"""
    if credentials is None:
        raise _auth_error("未登录或登录已过期")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id, jti, ver = _validate_access_payload(payload)
    except Exception:
        raise _auth_error()
    if token_store.is_access_blacklisted(jti):
        raise _auth_error()
    epoch = token_store.get_epoch(user_id)
    if ver != epoch:
        raise _auth_error()
    user = db.get(User, user_id)
    if user is None:
        raise _auth_error()
    if user.status != "active":
        # Token 合法 ≠ 用户仍有效：禁用用户直接拒绝
        raise BusinessException("ACCOUNT_DISABLED", "账号已被禁用", status_code=401)
    request.state.auth = {"jti": jti, "exp": int(payload["exp"])}
    return user


def get_optional_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """可选的当前用户：未登录或 token 无效时返回 None，不报错。"""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id, jti, ver = _validate_access_payload(payload)
    except Exception:
        return None
    if token_store.is_access_blacklisted(jti):
        return None
    epoch = token_store.get_epoch(user_id)
    if ver != epoch:
        return None
    user = db.get(User, user_id)
    if user is None:
        return None
    if user.status != "active":
        # 禁用用户视为未登录（公开接口按游客处理）
        return None
    request.state.auth = {"jti": jti, "exp": int(payload["exp"])}
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """管理员权限依赖：普通用户调用返回 403。"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )
    return user
