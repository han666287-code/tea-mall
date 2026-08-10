"""购物车接口测试：登录、累加、库存边界、越权。"""

from uuid import uuid4

from tests.conftest import client


def make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": f"test分类{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    )
    return response.json()["id"]


def make_product(admin_headers: dict, category_id: int, stock: int = 10, is_on_sale: bool = True) -> int:
    response = client.post(
        "/api/products",
        json={
            "name": f"test商品{uuid4().hex[:6]}",
            "category_id": category_id,
            "price": 99.9,
            "stock": stock,
            "is_on_sale": is_on_sale,
        },
        headers=admin_headers,
    )
    return response.json()["id"]


def test_cart_requires_login():
    assert client.get("/api/cart/items").status_code == 401
    assert client.post("/api/cart/items", json={"product_id": 1}).status_code == 401


def test_add_to_cart(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id)
    response = client.post(
        "/api/cart/items",
        json={"product_id": product_id, "quantity": 1},
        headers=normal_user_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 1
    assert data["product"]["id"] == product_id


def test_add_same_product_accumulates(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, stock=5)
    client.post("/api/cart/items", json={"product_id": product_id, "quantity": 2}, headers=normal_user_headers)
    response = client.post("/api/cart/items", json={"product_id": product_id, "quantity": 3}, headers=normal_user_headers)
    assert response.status_code == 201
    assert response.json()["quantity"] == 5
    items = client.get("/api/cart/items", headers=normal_user_headers).json()
    assert len(items) == 1


def test_add_off_sale_product_rejected(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, is_on_sale=False)
    response = client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": 1}, headers=normal_user_headers
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "商品已下架"


def test_add_exceeds_stock_rejected(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, stock=2)
    response = client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": 3}, headers=normal_user_headers
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "库存不足"


def test_add_accumulate_exceeds_stock_rejected(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, stock=5)
    client.post("/api/cart/items", json={"product_id": product_id, "quantity": 4}, headers=normal_user_headers)
    response = client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": 2}, headers=normal_user_headers
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "库存不足"


def test_update_quantity(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, stock=10)
    item_id = client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": 1}, headers=normal_user_headers
    ).json()["id"]
    response = client.put(f"/api/cart/items/{item_id}", json={"quantity": 7}, headers=normal_user_headers)
    assert response.status_code == 200
    assert response.json()["quantity"] == 7

    over_stock = client.put(f"/api/cart/items/{item_id}", json={"quantity": 11}, headers=normal_user_headers)
    assert over_stock.status_code == 400
    assert over_stock.json()["detail"] == "库存不足"

    zero = client.put(f"/api/cart/items/{item_id}", json={"quantity": 0}, headers=normal_user_headers)
    assert zero.status_code == 422


def test_list_and_delete(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id)
    item_id = client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": 2}, headers=normal_user_headers
    ).json()["id"]

    items = client.get("/api/cart/items", headers=normal_user_headers).json()
    assert len(items) == 1
    assert items[0]["quantity"] == 2
    assert items[0]["product"]["name"].startswith("test商品")

    assert client.delete(f"/api/cart/items/{item_id}", headers=normal_user_headers).status_code == 204
    assert client.get("/api/cart/items", headers=normal_user_headers).json() == []


def test_cannot_touch_other_users_cart(admin_headers, normal_user_headers):
    other_headers = None
    username = f"testuser{uuid4().hex[:8]}"
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "另一个用户"},
    )
    other_headers = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username': username, 'password': 'password123'}).json()['token']}"}

    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id)
    item_id = client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": 1}, headers=normal_user_headers
    ).json()["id"]

    # 另一个用户看不到、也改不了别人的购物车
    assert all(i["id"] != item_id for i in client.get("/api/cart/items", headers=other_headers).json())
    assert client.put(f"/api/cart/items/{item_id}", json={"quantity": 5}, headers=other_headers).status_code == 404
    assert client.delete(f"/api/cart/items/{item_id}", headers=other_headers).status_code == 404
    # 本人仍能正常操作
    assert client.delete(f"/api/cart/items/{item_id}", headers=normal_user_headers).status_code == 204
