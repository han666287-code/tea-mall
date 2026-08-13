"""FastAPI 依赖：从请求中解析当前登录用户。"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

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


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """未携带有效 token 时返回 401。"""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = _extract_user_id(payload)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=UNAUTHORIZED_DETAIL)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=UNAUTHORIZED_DETAIL)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """可选的当前用户：未登录或 token 无效时返回 None，不报错。"""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = _extract_user_id(payload)
        if user_id is None:
            return None
        return db.get(User, user_id)
    except Exception:
        return None


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """管理员权限依赖：普通用户调用返回 403。"""
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user
