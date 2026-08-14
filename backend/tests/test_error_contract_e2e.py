"""V2.0-2.3 错误契约端到端回归：各业务路径的状态码与稳定 code。"""

from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.conftest import client


def _create_category(admin_headers: dict, name: str) -> dict:
    response = client.post(
        "/api/categories", json={"name": name, "sort_order": 0}, headers=admin_headers
    )
    assert response.status_code == 201
    return response.json()


def _create_product(
    admin_headers: dict, category_id: int, *, stock: int = 5, is_on_sale: bool = True
) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": f"testerr{uuid4().hex[:6]}",
            "category_id": category_id,
            "price": 10,
            "stock": stock,
            "is_on_sale": is_on_sale,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def _add_to_cart(user_headers: dict, product_id: int, quantity: int = 1) -> dict:
    response = client.post(
        "/api/cart/items",
        json={"product_id": product_id, "quantity": quantity},
        headers=user_headers,
    )
    assert response.status_code == 201
    return response.json()


def _create_order(user_headers: dict) -> dict:
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
    return response.json()


def test_auth_error_codes():
    username = f"testdupe2e{uuid4().hex[:6]}"
    payload = {"username": username, "password": "password123", "nickname": ""}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["code"] == "USERNAME_TAKEN"

    response = client.post(
        "/api/auth/login", json={"username": "testadmin", "password": "wrong-password"}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_admin_permission_403_code(normal_user_headers):
    response = client.get("/api/admin/orders", headers=normal_user_headers)
    assert response.status_code == 403
    assert response.json()["code"] == "http_403"


def test_cart_error_codes(admin_headers, normal_user_headers):
    response = client.post(
        "/api/cart/items",
        json={"product_id": 999999, "quantity": 1},
        headers=normal_user_headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "PRODUCT_NOT_FOUND"

    category = _create_category(admin_headers, f"testerr{uuid4().hex[:6]}")
    out_of_stock = _create_product(admin_headers, category["id"], stock=0)
    response = client.post(
        "/api/cart/items",
        json={"product_id": out_of_stock["id"], "quantity": 1},
        headers=normal_user_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "INSUFFICIENT_STOCK"

    off_sale = _create_product(admin_headers, category["id"], is_on_sale=False)
    response = client.post(
        "/api/cart/items",
        json={"product_id": off_sale["id"], "quantity": 1},
        headers=normal_user_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "PRODUCT_OFF_SALE"


def test_order_error_codes(admin_headers, normal_user_headers):
    response = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=normal_user_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "CART_EMPTY"

    response = client.get("/api/orders/999999", headers=normal_user_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "ORDER_NOT_FOUND"

    category = _create_category(admin_headers, f"testerr{uuid4().hex[:6]}")
    product = _create_product(admin_headers, category["id"])
    _add_to_cart(normal_user_headers, product["id"])
    order = _create_order(normal_user_headers)
    assert client.post(
        f"/api/orders/{order['id']}/pay", headers=normal_user_headers
    ).status_code == 200
    response = client.post(
        f"/api/orders/{order['id']}/pay", headers=normal_user_headers
    )
    assert response.status_code == 400
    assert response.json()["code"] == "ORDER_STATUS_INVALID"


def test_admin_order_error_codes(admin_headers, normal_user_headers):
    category = _create_category(admin_headers, f"testerr{uuid4().hex[:6]}")
    product = _create_product(admin_headers, category["id"])
    _add_to_cart(normal_user_headers, product["id"])
    order = _create_order(normal_user_headers)

    response = client.patch(
        f"/api/admin/orders/{order['id']}/status",
        json={"status": "shipped"},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "ORDER_STATUS_INVALID"

    response = client.patch(
        "/api/admin/orders/999999/status",
        json={"status": "paid"},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "ORDER_NOT_FOUND"


def test_category_product_http_error_codes(admin_headers, normal_user_headers):
    name = f"testerr{uuid4().hex[:6]}"
    category = _create_category(admin_headers, name)
    response = client.post(
        "/api/categories", json={"name": name, "sort_order": 0}, headers=admin_headers
    )
    assert response.status_code == 400
    assert response.json()["code"] == "CATEGORY_NAME_TAKEN"

    response = client.put(
        "/api/categories/999999",
        json={"name": "x"},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "CATEGORY_NOT_FOUND"

    response = client.post(
        "/api/products",
        json={"name": "x", "category_id": 999999, "price": 1, "stock": 1},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "PRODUCT_CATEGORY_NOT_FOUND"

    response = client.post(
        "/api/categories", json={"name": f"testerr{uuid4().hex[:6]}", "sort_order": 0},
        headers=normal_user_headers,
    )
    assert response.status_code == 403
    assert response.json()["code"] == "http_403"


def test_validation_error_codes():
    response = client.get("/api/products", params={"page": 0})
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"

    response = client.get("/api/products", params={"page_size": 51})
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"

    response = client.post(
        "/api/auth/register",
        json={"username": "ab", "password": "password123", "nickname": ""},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_integrity_error_409_rolls_back(admin_headers, monkeypatch):
    name = f"testerr{uuid4().hex[:6]}"

    def forced_integrity_error(self):
        raise IntegrityError("INSERT ...", {}, Exception("duplicate key"))

    monkeypatch.setattr(Session, "commit", forced_integrity_error)
    response = client.post(
        "/api/categories",
        json={"name": name, "sort_order": 0},
        headers=admin_headers,
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "数据冲突或违反约束", "code": "integrity_error"}
    monkeypatch.undo()

    categories = client.get("/api/categories").json()
    assert all(category["name"] != name for category in categories)
