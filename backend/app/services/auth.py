"""用户注册 / 登录业务逻辑。"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse, UserResponse


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def register_user(db: Session, data: RegisterRequest) -> User:
    """注册普通用户，用户名重复时返回 400。"""
    if get_user_by_username(db, data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: LoginRequest) -> User:
    """校验用户名密码，失败统一返回 400，避免暴露用户是否存在。"""
    user = get_user_by_username(db, data.username)
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    return user


def build_token_response(user: User) -> TokenResponse:
    """登录成功后生成 token 与用户信息。"""
    return TokenResponse(
        token=create_access_token(user.id),
        user=UserResponse.model_validate(user),
    )
