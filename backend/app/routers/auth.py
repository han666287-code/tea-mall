"""用户认证接口：注册、登录、刷新、登出、当前用户。"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services import auth as auth_service
from app.services import rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户（默认角色为普通用户）。"""
    return auth_service.register_user(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """登录，返回 JWT token 和用户信息。"""
    rate_limit.check_login_rate_limit(data.username, request)
    user = auth_service.authenticate_user(db, data)
    return auth_service.build_token_response(user)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新当前用户资料（昵称/邮箱），禁止修改角色与状态。"""
    return auth_service.update_user_profile(db, current_user, data)


@router.put("/me/password")
def change_my_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改密码：验证旧密码后重新哈希，并使全部旧 Token 失效。"""
    auth_service.change_password(db, current_user, data)
    return {"detail": "密码修改成功"}


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """使用 Refresh Token 换取新的 Access + Refresh（轮换）。"""
    return auth_service.refresh_user_token(db, data.refresh_token)


@router.post("/logout")
def logout(
    request: Request,
    data: LogoutRequest | None = None,
    current_user: User = Depends(get_current_user),
):
    """退出登录：撤销当前 Access Token 与 Refresh Token。"""
    claims = getattr(request.state, "auth", {})
    auth_service.logout_user(
        jti=claims.get("jti", ""),
        exp=claims.get("exp", 0),
        refresh_token=data.refresh_token if data else None,
    )
    return {"detail": "已退出登录"}
