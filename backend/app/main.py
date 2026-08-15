"""应用入口：创建 FastAPI 实例。

数据库表结构由 Alembic 管理（Docker 通过 docker-entrypoint.sh、本地开发手动执行
`alembic upgrade head`），应用启动不再调用 create_all。
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from app.config import UPLOAD_DIR
from app.core import exception_handlers
from app.core.exceptions import BusinessException
from app.database import engine
from app.routers import admin, auth, cart, categories, orders, products
from app.services import cache

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Tea Mall API")
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(admin.router)

# 统一异常处理：业务异常 4xx、未知异常 500，错误体统一为 {detail, code}
app.add_exception_handler(BusinessException, exception_handlers.business_exception_handler)
app.add_exception_handler(HTTPException, exception_handlers.http_exception_handler)
app.add_exception_handler(RequestValidationError, exception_handlers.validation_exception_handler)
app.add_exception_handler(IntegrityError, exception_handlers.integrity_error_handler)
app.add_exception_handler(Exception, exception_handlers.generic_exception_handler)

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
        cache.redis_client.ping()
        result["redis"] = True
    except Exception:
        result["status"] = "error"
    return result
