"""应用配置：从环境变量 / .env 文件读取。"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录（config.py 位于 backend/app/）
BASE_DIR = Path(__file__).resolve().parent.parent
# 商品图片上传目录
UPLOAD_DIR = BASE_DIR / "uploads"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = (
        "mysql+pymysql://tea_mall:tea_mall_dev@localhost:3306/tea_mall?charset=utf8mb4"
    )
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-only-secret-change-in-production-0123456789"
    jwt_expire_days: int = 7


settings = Settings()
