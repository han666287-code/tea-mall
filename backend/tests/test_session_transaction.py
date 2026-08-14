"""V2.0-2.2 Session / 事务管理回归测试。"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.main import app
from app.models.user import User
from tests.conftest import client


def test_get_db_rolls_back_and_closes_on_error():
    """未处理异常时 get_db 必须回滚并关闭会话。"""
    db_gen = get_db()
    db = next(db_gen)
    db.add(
        User(
            username=f"testrollback{uuid4().hex[:8]}",
            password_hash="x",
            nickname="",
            role="user",
        )
    )
    with pytest.raises(RuntimeError):
        db_gen.throw(RuntimeError("forced failure"))
    assert not db.in_transaction()  # 事务已回滚
    with SessionLocal() as check:
        assert check.scalar(select(User).where(User.username.like("testrollback%"))) is None


def test_route_commit_failure_rolls_back_no_partial_data(admin_headers, monkeypatch):
    """提交期抛错时，请求不应留下部分数据，且后续请求正常。"""
    name = f"testrollback{uuid4().hex[:6]}"

    def forced_commit_failure(self):
        raise RuntimeError("forced commit failure")

    monkeypatch.setattr(Session, "commit", forced_commit_failure)
    # 使用不重抛异常的 TestClient，验证统一 500 响应体（{detail, code}）
    no_raise_client = TestClient(app, raise_server_exceptions=False)
    response = no_raise_client.post(
        "/api/categories",
        json={"name": name, "sort_order": 0},
        headers=admin_headers,
    )
    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    monkeypatch.undo()
    categories = client.get("/api/categories").json()
    assert all(category["name"] != name for category in categories)


def test_update_flows_response_schema_stable(admin_headers, normal_user_headers):
    """移除更新类操作的冗余 refresh 后，响应字段与数值保持稳定。"""
    category_name = f"testupd{uuid4().hex[:6]}"
    category = client.post(
        "/api/categories",
        json={"name": category_name, "sort_order": 0},
        headers=admin_headers,
    ).json()
    updated = client.put(
        f"/api/categories/{category['id']}",
        json={"name": category_name + "x", "sort_order": 5},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert set(updated.json().keys()) == {"id", "name", "sort_order", "created_at"}
    assert updated.json()["name"] == category_name + "x"
    assert updated.json()["sort_order"] == 5

    product = client.post(
        "/api/products",
        json={
            "name": f"testupdprod{uuid4().hex[:6]}",
            "category_id": category["id"],
            "price": 10,
            "stock": 5,
        },
        headers=admin_headers,
    ).json()
    updated = client.put(
        f"/api/products/{product['id']}",
        json={"price": 12, "stock": 3},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["price"] == "12.00"
    assert updated.json()["stock"] == 3

    cart_item = client.post(
        "/api/cart/items",
        json={"product_id": product["id"], "quantity": 1},
        headers=normal_user_headers,
    ).json()
    updated = client.put(
        f"/api/cart/items/{cart_item['id']}",
        json={"quantity": 2},
        headers=normal_user_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["quantity"] == 2

    order = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=normal_user_headers,
    )
    assert order.status_code == 201
    order_id = order.json()["id"]
    paid = client.post(f"/api/orders/{order_id}/pay", headers=normal_user_headers)
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"
