"""V2.0-2.4 API 数据契约回归测试：响应字段与前端类型保持一致，无敏感字段。"""

from uuid import uuid4

from tests.conftest import client

# 与 frontend/src/types/*.ts 逐一对应的响应字段集合
EXPECTED_KEYS = {
    "UserResponse": {
        "id",
        "username",
        "email",
        "nickname",
        "role",
        "status",
        "is_root",
        "created_at",
    },
    "CategoryResponse": {"id", "name", "sort_order", "created_at"},
    "ProductResponse": {
        "id",
        "name",
        "category_id",
        "category_name",
        "price",
        "stock",
        "description",
        "image_url",
        "is_on_sale",
        "created_at",
    },
    "CartItemResponse": {"id", "quantity", "product", "created_at"},
    "OrderItemResponse": {"id", "product_id", "product_name", "price", "quantity", "subtotal"},
    "OrderResponse": {
        "id",
        "order_no",
        "status",
        "total_amount",
        "username",
        "receiver_name",
        "receiver_phone",
        "receiver_address",
        "created_at",
        "items",
    },
}

PAGE_KEYS = {"items", "total", "page", "page_size"}
SENSITIVE_KEYS = {"password", "password_hash"}


def _walk(obj, found: set):
    if isinstance(obj, dict):
        found.update(obj.keys())
        for value in obj.values():
            _walk(value, found)
    elif isinstance(obj, list):
        for item in obj:
            _walk(item, found)


def _assert_no_sensitive_keys(payload) -> None:
    found: set = set()
    _walk(payload, found)
    assert not (found & SENSITIVE_KEYS), f"响应泄露敏感字段: {found & SENSITIVE_KEYS}"


def test_auth_responses_match_frontend_types():
    username = f"testcontract{uuid4().hex[:6]}"
    register = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "契约测试"},
    )
    assert register.status_code == 201
    user = register.json()
    assert set(user.keys()) == EXPECTED_KEYS["UserResponse"]
    _assert_no_sensitive_keys(user)

    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login.status_code == 200
    body = login.json()
    assert set(body["user"].keys()) == EXPECTED_KEYS["UserResponse"]
    assert "token" in body
    _assert_no_sensitive_keys(body)

    me = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert me.status_code == 200
    assert set(me.json().keys()) == EXPECTED_KEYS["UserResponse"]
    _assert_no_sensitive_keys(me.json())


def test_category_and_product_responses_match_frontend_types(admin_headers):
    category = client.post(
        "/api/categories",
        json={"name": f"testcontract{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    ).json()
    assert set(category.keys()) == EXPECTED_KEYS["CategoryResponse"]

    product = client.post(
        "/api/products",
        json={
            "name": f"testcontract{uuid4().hex[:6]}",
            "category_id": category["id"],
            "price": 88.5,
            "stock": 10,
        },
        headers=admin_headers,
    ).json()
    assert set(product.keys()) == EXPECTED_KEYS["ProductResponse"]
    _assert_no_sensitive_keys(product)

    listed = client.get("/api/products").json()
    assert set(listed.keys()) == PAGE_KEYS
    assert listed["page_size"] <= 50
    _assert_no_sensitive_keys(listed)


def test_cart_and_order_responses_match_frontend_types(admin_headers, normal_user_headers):
    category = client.post(
        "/api/categories",
        json={"name": f"testcontract{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    ).json()
    product = client.post(
        "/api/products",
        json={
            "name": f"testcontract{uuid4().hex[:6]}",
            "category_id": category["id"],
            "price": 50,
            "stock": 10,
        },
        headers=admin_headers,
    ).json()

    cart = client.post(
        "/api/cart/items",
        json={"product_id": product["id"], "quantity": 2},
        headers=normal_user_headers,
    ).json()
    assert set(cart.keys()) == EXPECTED_KEYS["CartItemResponse"]
    assert set(cart["product"].keys()) == EXPECTED_KEYS["ProductResponse"]
    _assert_no_sensitive_keys(cart)

    cart_list = client.get("/api/cart/items", headers=normal_user_headers).json()
    _assert_no_sensitive_keys(cart_list)

    order = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=normal_user_headers,
    ).json()
    assert set(order.keys()) == EXPECTED_KEYS["OrderResponse"]
    assert all(set(item.keys()) == EXPECTED_KEYS["OrderItemResponse"] for item in order["items"])
    _assert_no_sensitive_keys(order)

    orders = client.get("/api/orders", headers=normal_user_headers).json()
    assert set(orders.keys()) == PAGE_KEYS
    assert orders["page_size"] <= 50
    _assert_no_sensitive_keys(orders)


def test_admin_orders_response_matches_frontend_types(admin_headers, normal_user_headers):
    response = client.get("/api/admin/orders", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == PAGE_KEYS
    assert body["page_size"] <= 50
    _assert_no_sensitive_keys(body)
