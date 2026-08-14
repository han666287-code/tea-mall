"""统一异常处理器：所有异常转为稳定的 `{detail, code}` 响应。

规则：
- BusinessException → 对应 4xx；
- HTTPException → 保持原状态码，code 为 http_<status>；
- RequestValidationError → 422，保留原始校验错误数组；
- IntegrityError → 409（完整日志仅服务端可见）；
- 未知异常 → 500，响应体不泄露 traceback、路径、密钥等内部细节。
"""

import logging

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BusinessException

logger = logging.getLogger("uvicorn.error")


def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": f"http_{exc.status_code}"},
        headers=exc.headers,
    )


def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        # 与 FastAPI 默认行为一致：errors 中可能含 ValueError 等不可直接序列化对象
        content={"detail": jsonable_encoder(exc.errors()), "code": "validation_error"},
    )


def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.error("数据库约束冲突（IntegrityError）：%s", exc, exc_info=True)
    return JSONResponse(
        status_code=409,
        content={"detail": "数据冲突或违反约束", "code": "integrity_error"},
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("未处理异常：%s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "code": "internal_error"},
    )
