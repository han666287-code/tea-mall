"""应用入口：创建 FastAPI 实例，启动时自动建表。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis import Redis
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 0：启动时创建尚未存在的表（ORM 模型从 Phase 1 开始添加）
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Tea Mall API", lifespan=lifespan)


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
