"""V2.0-2.6 N+1 查询回归测试：统计关键列表/详情接口的 SQL 查询次数。"""

from uuid import uuid4

from sqlalchemy import event

from app.database import engine
from tests.conftest import client

_COUNT = {"n": 0}


@event.listens_for(engine, "before_cursor_execute")
def _count_queries(conn, cursor, statement, parameters, context, executemany):
    _COUNT["n"] += 1


def _reset() -> None:
    _COUNT["n"] = 0


def _create_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": f"testq{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_product(admin_headers: dict, category_id: int, stock: int = 10) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": f"testqprod{uuid4().hex[:6]}",
            "category_id": category_id,
            "price": 10,
            "stock": stock,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def _create_order(user_headers: dict) -> int:
    response = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=user_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_product_list_query_count(admin_headers):
    category_id = _create_category(admin_headers)
    for _ in range(5):
        _create_product(admin_headers, category_id)
    _reset()
    response = client.get("/api/products", params={"page": 1, "page_size": 5})
    assert response.status_code == 200
    assert _COUNT["n"] <= 7, f"商品列表查询次数异常: {_COUNT['n']}"


def test_cart_list_query_count(admin_headers, normal_user_headers):
    category_id = _create_category(admin_headers)
    products = [_create_product(admin_headers, category_id) for _ in range(3)]
    for product in products:
        response = client.post(
            "/api/cart/items",
            json={"sku_id": product["skus"][0]["id"], "quantity": 1},
            headers=normal_user_headers,
        )
        assert response.status_code == 201
    _reset()
    response = client.get("/api/cart/items", headers=normal_user_headers)
    assert response.status_code == 200
    assert _COUNT["n"] <= 12, f"购物车列表查询次数异常: {_COUNT['n']}"


def test_orders_list_query_count(admin_headers, normal_user_headers):
    category_id = _create_category(admin_headers)
    product = _create_product(admin_headers, category_id)
    client.post(
        "/api/cart/items",
        json={"sku_id": product["skus"][0]["id"], "quantity": 1},
        headers=normal_user_headers,
    )
    _create_order(normal_user_headers)
    _reset()
    response = client.get("/api/orders", headers=normal_user_headers)
    assert response.status_code == 200
    assert _COUNT["n"] <= 6, f"订单列表查询次数异常: {_COUNT['n']}"


def test_order_detail_query_count(admin_headers, normal_user_headers):
    category_id = _create_category(admin_headers)
    product = _create_product(admin_headers, category_id)
    client.post(
        "/api/cart/items",
        json={"sku_id": product["skus"][0]["id"], "quantity": 1},
        headers=normal_user_headers,
    )
    order_id = _create_order(normal_user_headers)
    _reset()
    response = client.get(f"/api/orders/{order_id}", headers=normal_user_headers)
    assert response.status_code == 200
    assert _COUNT["n"] <= 5, f"订单详情查询次数异常: {_COUNT['n']}"


def test_admin_orders_list_query_count(admin_headers, normal_user_headers):
    category_id = _create_category(admin_headers)
    product = _create_product(admin_headers, category_id)
    client.post(
        "/api/cart/items",
        json={"sku_id": product["skus"][0]["id"], "quantity": 1},
        headers=normal_user_headers,
    )
    _create_order(normal_user_headers)
    _reset()
    response = client.get("/api/admin/orders", headers=admin_headers)
    assert response.status_code == 200
    assert _COUNT["n"] <= 6, f"管理端订单列表查询次数异常: {_COUNT['n']}"
