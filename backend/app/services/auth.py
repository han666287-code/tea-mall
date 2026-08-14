"""用户注册 / 登录业务逻辑。"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import BusinessException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services import token_store


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_user_by_email(db: Session, email: str | None) -> User | None:
    """按规范化邮箱查用户；空邮箱直接返回 None。"""
    if not email:
        return None
    return db.scalar(select(User).where(User.email == email))


def get_user_by_email_excluding(
    db: Session, email: str, exclude_user_id: int
) -> User | None:
    """查重邮箱但排除当前用户（用于资料编辑）。"""
    return db.scalar(
        select(User).where(User.email == email, User.id != exclude_user_id)
    )


def register_user(db: Session, data: RegisterRequest) -> User:
    """注册普通用户：用户名/邮箱重复返回 400，数据库冲突兜底映射业务码。"""
    if get_user_by_username(db, data.username):
        raise BusinessException("USERNAME_TAKEN", "用户名已存在", status_code=400)
    if data.email and get_user_by_email(db, data.email):
        raise BusinessException("EMAIL_TAKEN", "邮箱已被注册", status_code=400)
    try:
        password_hash = hash_password(data.password)
    except ValueError:
        raise BusinessException("PASSWORD_FORMAT", "密码格式不正确", status_code=400)
    user = User(
        username=data.username,
        email=data.email,
        password_hash=password_hash,
        nickname=data.nickname,
        role="user",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # 并发/直插导致的唯一冲突：回滚后复核字段，映射为稳定业务码
        db.rollback()
        if get_user_by_username(db, data.username):
            raise BusinessException("USERNAME_TAKEN", "用户名已存在", status_code=400)
        if data.email and get_user_by_email(db, data.email):
            raise BusinessException("EMAIL_TAKEN", "邮箱已被注册", status_code=400)
        raise
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: LoginRequest) -> User:
    """校验用户名密码，失败统一返回 400，避免暴露用户是否存在。"""
    user = get_user_by_username(db, data.username)
    if user is None:
        raise BusinessException("INVALID_CREDENTIALS", "用户名或密码错误", status_code=400)
    try:
        password_ok = verify_password(data.password, user.password_hash)
    except ValueError:
        password_ok = False
    if not password_ok:
        raise BusinessException("INVALID_CREDENTIALS", "用户名或密码错误", status_code=400)
    if user.status != "active":
        raise BusinessException("ACCOUNT_DISABLED", "账号已被禁用", status_code=403)
    return user


def build_token_response(user: User) -> TokenResponse:
    """登录/刷新成功后生成 Access + Refresh 会话凭证。"""
    epoch = token_store.get_epoch(user.id)
    access_token = create_access_token(user.id, epoch)
    refresh_token = create_refresh_token()
    token_store.store_refresh_token(refresh_token, user.id, epoch)
    return TokenResponse(
        token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


def refresh_user_token(db: Session, refresh_token: str) -> TokenResponse:
    """校验并轮换 Refresh Token；旧 refresh 使用一次即失效。"""
    data = token_store.get_refresh_token_data(refresh_token)
    if data is None:
        raise BusinessException(
            "REFRESH_TOKEN_INVALID", "refresh token 无效或已过期", status_code=401
        )
    user_id = data.get("user_id")
    ver = data.get("ver")
    if not isinstance(user_id, int) or not isinstance(ver, int):
        raise BusinessException(
            "REFRESH_TOKEN_INVALID", "refresh token 无效或已过期", status_code=401
        )
    user = db.get(User, user_id)
    if user is None:
        raise BusinessException(
            "REFRESH_TOKEN_INVALID", "refresh token 无效或已过期", status_code=401
        )
    if user.status != "active":
        raise BusinessException("ACCOUNT_DISABLED", "账号已被禁用", status_code=401)
    epoch = token_store.get_epoch(user_id)
    if ver != epoch:
        raise BusinessException(
            "REFRESH_TOKEN_INVALID", "refresh token 无效或已过期", status_code=401
        )
    # 轮换：删除旧指纹，签发新对
    token_store.delete_refresh_token(refresh_token)
    return build_token_response(user)


def logout_user(jti: str, exp: int, refresh_token: str | None) -> None:
    """退出登录：黑名单当前 Access Token，并删除对应 Refresh Token。"""
    now = int(datetime.now(timezone.utc).timestamp())
    token_store.blacklist_access_jti(jti, max(int(exp) - now, 1))
    if refresh_token:
        token_store.delete_refresh_token(refresh_token)


def update_user_profile(
    db: Session, user: User, data: UpdateProfileRequest
) -> User:
    """更新当前用户资料：仅 nickname / email，邮箱唯一性排除自身。"""
    if "email" in data.model_fields_set:
        email = data.email
        if email and get_user_by_email_excluding(db, email, user.id):
            raise BusinessException("EMAIL_TAKEN", "邮箱已被注册", status_code=400)
        user.email = email
    if "nickname" in data.model_fields_set:
        user.nickname = data.nickname or ""
    db.commit()
    db.refresh(user)
    return user


def change_password(
    db: Session, user: User, data: ChangePasswordRequest
) -> None:
    """修改密码：验证旧密码 → 校验新密码 → 重新哈希 → 使全部旧 Token 失效。"""
    try:
        old_ok = verify_password(data.old_password, user.password_hash)
    except ValueError:
        old_ok = False
    if not old_ok:
        raise BusinessException("OLD_PASSWORD_INCORRECT", "旧密码不正确", status_code=400)
    try:
        new_hash = hash_password(data.new_password)
    except ValueError:
        raise BusinessException("PASSWORD_FORMAT", "密码格式不正确", status_code=400)
    user.password_hash = new_hash
    db.commit()
    # 会话纪元 +1：所有设备已签发 Access/Refresh 立即失效
    token_store.bump_epoch(user.id)
