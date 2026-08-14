"""应用配置：从环境变量 / .env 文件读取。"""

from pathlib import Path
from urllib.parse import urlsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录（config.py 位于 backend/app/）
BASE_DIR = Path(__file__).resolve().parent.parent
# 商品图片上传目录
UPLOAD_DIR = BASE_DIR / "uploads"

# 历史/示例中出现过的公开默认 JWT Secret，命中即拒绝启动
WEAK_JWT_SECRETS = {
    "dev-only-secret-change-in-production-0123456789",
    "dev-only-secret-please-change-in-production-0123456789",
    "change-me-to-a-random-string-at-least-32-bytes",
}
# 常见不安全占位符标记（大小写不敏感）
WEAK_JWT_MARKERS = ("dev-only", "change-me", "changeme", "please-change")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = (
        "mysql+pymysql://tea_mall:tea_mall_dev@localhost:3306/tea_mall?charset=utf8mb4"
    )
    redis_url: str = "redis://localhost:6379/0"
    # 必填：缺失或不符合要求时拒绝启动
    jwt_secret: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    # 测试环境标识：pytest 通过 conftest 强制开启
    testing: bool = False

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if not value:
            raise ValueError("JWT_SECRET 不能为空")
        if len(value.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET 长度不足 32 字节，请生成随机字符串")
        lowered = value.lower()
        if value in WEAK_JWT_SECRETS or any(
            marker in lowered for marker in WEAK_JWT_MARKERS
        ):
            raise ValueError("JWT_SECRET 命中已知不安全默认值，请生成随机字符串")
        return value


def _database_name_from_url(url: str) -> str:
    """从 SQLAlchemy URL 中提取数据库名（不包含口令等敏感信息）。"""
    remainder = url.split("://", 1)[1] if "://" in url else url
    path = remainder.split("?", 1)[0].split("#", 1)[0]
    if "/" not in path:
        return ""
    return path.rsplit("/", 1)[1]


def _redis_db_index(url: str) -> int | None:
    path = urlsplit(url).path
    if not path:
        return None
    try:
        return int(path.lstrip("/"))
    except ValueError:
        return None


def ensure_testing_environment() -> None:
    """破坏性测试操作的环境保护：非测试环境直接拒绝执行。"""
    if not settings.testing:
        raise RuntimeError("拒绝执行：当前不是测试环境（TESTING 未开启）")
    if _database_name_from_url(settings.database_url) != "tea_mall_test":
        raise RuntimeError("拒绝执行：DATABASE_URL 必须指向测试数据库 tea_mall_test")
    if _redis_db_index(settings.redis_url) != 15:
        raise RuntimeError("拒绝执行：REDIS_URL 必须指向测试 Redis（DB 15）")


settings = Settings()
