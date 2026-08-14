"""V2.0-2.3 统一异常处理回归测试。"""

from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.core.exception_handlers import (
    business_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    validation_exception_handler,
)
from app.core.exceptions import BusinessException
from tests.conftest import client


class DemoBody(BaseModel):
    name: str


def _build_handler_app() -> TestClient:
    """独立的小应用：注册与主应用一致的异常处理器，验证响应形状。"""
    app = FastAPI()
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    @app.get("/biz")
    def biz():
        raise BusinessException("DEMO_ERROR", "演示业务错误", status_code=400)

    @app.get("/http")
    def http_err():
        raise HTTPException(status_code=401, detail="未授权")

    @app.get("/boom")
    def boom():
        raise RuntimeError("内部秘密路径 C:\\secret\\traceback")

    @app.get("/integrity")
    def integrity():
        raise IntegrityError("INSERT ...", {}, Exception("duplicate key"))

    @app.post("/validate")
    def validate(data: DemoBody):
        return data

    # ServerErrorMiddleware 在返回 500 响应后会重抛异常供服务器记录日志，
    # 测试需关闭 raise_server_exceptions 才能拿到 500 响应体
    return TestClient(app, raise_server_exceptions=False)


def test_business_exception_shape():
    response = _build_handler_app().get("/biz")
    assert response.status_code == 400
    assert response.json() == {"detail": "演示业务错误", "code": "DEMO_ERROR"}


def test_http_exception_shape():
    response = _build_handler_app().get("/http")
    assert response.status_code == 401
    assert response.json() == {"detail": "未授权", "code": "http_401"}


def test_unknown_exception_500_no_leak():
    response = _build_handler_app().get("/boom")
    assert response.status_code == 500
    assert response.json() == {"detail": "服务器内部错误", "code": "internal_error"}
    text = response.text
    assert "Traceback" not in text
    assert "secret" not in text


def test_integrity_error_409():
    response = _build_handler_app().get("/integrity")
    assert response.status_code == 409
    assert response.json() == {"detail": "数据冲突或违反约束", "code": "integrity_error"}


def test_validation_error_adds_code_keeps_detail():
    response = _build_handler_app().post("/validate", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert isinstance(body["detail"], list)


def test_real_business_errors_have_codes(normal_user_headers):
    username = f"testdup{uuid4().hex[:8]}"
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": ""},
    )
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": ""},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "用户名已存在", "code": "USERNAME_TAKEN"}

    response = client.post(
        "/api/cart/items",
        json={"product_id": 999999, "quantity": 1},
        headers=normal_user_headers,
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "商品不存在", "code": "PRODUCT_NOT_FOUND"}


def test_invalid_jwt_401_with_code():
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer invalid.token.value"}
    )
    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "TOKEN_INVALID"
    assert "token" in body["detail"]
