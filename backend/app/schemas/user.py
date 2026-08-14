"""用户相关的请求/响应模型。"""

from datetime import datetime

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

MAX_PASSWORD_UTF8_BYTES = 72


def _check_password_utf8_bytes(value: str) -> str:
    """bcrypt 上限按 UTF-8 字节计算，而非字符数。"""
    if len(value.encode("utf-8")) > MAX_PASSWORD_UTF8_BYTES:
        raise ValueError("密码过长：UTF-8 编码后不能超过 72 字节")
    return value


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)
    nickname: str = Field(default="", max_length=50)
    email: EmailStr | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        """邮箱规范化：去空白、小写、空串转 None；长度不超过 120。"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip().lower()
            if not value:
                return None
            if len(value) > 120:
                raise ValueError("邮箱长度不能超过 120 个字符")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_utf8_bytes(cls, value: str) -> str:
        return _check_password_utf8_bytes(value)


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=1)

    @field_validator("password")
    @classmethod
    def validate_password_utf8_bytes(cls, value: str) -> str:
        return _check_password_utf8_bytes(value)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None
    nickname: str
    role: str
    status: str
    is_root: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=200)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(default=None, max_length=200)


class UpdateProfileRequest(BaseModel):
    """用户资料更新：仅允许 nickname / email；禁止 role、status、username、id。"""

    model_config = {"extra": "forbid"}

    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip().lower()
            if not value:
                return None
            if len(value) > 120:
                raise ValueError("邮箱长度不能超过 120 个字符")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("没有要修改的字段")
        return self


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=6, max_length=72)

    @field_validator("old_password", "new_password")
    @classmethod
    def validate_password_utf8_bytes(cls, value: str) -> str:
        return _check_password_utf8_bytes(value)


class UserStatusUpdate(BaseModel):
    status: Literal["active", "disabled"]


class UserRoleUpdate(BaseModel):
    role: Literal["user", "admin"]
