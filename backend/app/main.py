"""应用入口：创建 FastAPI 实例，启动时自动建表。"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from redis import Redis
from sqlalchemy import text

from app.config import UPLOAD_DIR, settings
from app.database import Base, engine
from app.routers import admin, auth, cart, categories, orders, products

logger = logging.getLogger("uvicorn.error")

DB_STARTUP_MAX_ATTEMPTS = 20
DB_STARTUP_RETRY_DELAY_SECONDS = 2.0


def _create_tables_with_retry() -> None:
    """启动建表：数据库未就绪时有限重试，避免 MySQL 尚未完成初始化导致随机失败。"""
    last_error: Exception | None = None
    for attempt in range(1, DB_STARTUP_MAX_ATTEMPTS + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as exc:
            last_error = exc
            logger.warning(
                "数据库未就绪（第 %s/%s 次）：%s",
                attempt,
                DB_STARTUP_MAX_ATTEMPTS,
                exc,
            )
            time.sleep(DB_STARTUP_RETRY_DELAY_SECONDS)
    raise RuntimeError(
        f"数据库在 {DB_STARTUP_MAX_ATTEMPTS * DB_STARTUP_RETRY_DELAY_SECONDS:.0f} 秒内未能就绪，"
        "请检查 DATABASE_URL 配置与 MySQL 服务状态"
    ) from last_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建尚未存在的表（带有限重试，配置错误会在重试耗尽后明确失败退出）
    _create_tables_with_retry()
    yield


app = FastAPI(title="Tea Mall API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(admin.router)

# 商品图片静态文件服务
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"message": "Tea Mall API"}


@app.get("/api/health")
def health():
    """检查数据库与 Redis 是否可用，用于本地环境验证。"""
    result = {"status": "ok", "database": False, "redis": False}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["database"] = True
    except Exception:
        result["status"] = "error"

    try:
        redis_client = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        redis_client.ping()
        result["redis"] = True
    except Exception:
        result["status"] = "error"
    return result
