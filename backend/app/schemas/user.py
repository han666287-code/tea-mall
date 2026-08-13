"""用户相关的请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

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
    nickname: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    token: str
    user: UserResponse
