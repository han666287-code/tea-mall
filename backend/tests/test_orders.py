"""订单接口测试：下单事务、库存、支付、取消、越权。"""

from uuid import uuid4

from tests.conftest import client


def make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": f"test分类{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    )
    return response.json()["id"]


def make_product(admin_headers: dict, category_id: int, stock: int = 10) -> int:
    response = client.post(
        "/api/products",
        json={
            "name": f"test商品{uuid4().hex[:6]}",
            "category_id": category_id,
            "price": 50,
            "stock": stock,
        },
        headers=admin_headers,
    )
    return response.json()["id"]


def add_to_cart(user_headers: dict, product_id: int, quantity: int = 1) -> None:
    client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": quantity}, headers=user_headers
    )


def create_order(user_headers: dict) -> dict:
    response = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=user_headers,
    )
    return response


def test_create_order_requires_login():
    response = client.post(
        "/api/orders",
        json={"receiver_name": "张三", "receiver_phone": "138", "receiver_address": "上海"},
    )
    assert response.status_code == 401


def test_create_order_empty_cart(admin_headers, normal_user_headers):
    response = create_order(normal_user_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "购物车为空"


def test_create_order_success_deducts_stock_and_clears_cart(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, stock=10)
    add_to_cart(normal_user_headers, product_id, 2)

    response = create_order(normal_user_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["total_amount"] == "100.00"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_name"].startswith("test商品")
    assert data["items"][0]["subtotal"] == "100.00"

    # 购物车已清空
    assert client.get("/api/cart/items", headers=normal_user_headers).json() == []
    # 库存已扣减（商品上架，公开详情可见库存）
    detail = client.get(f"/api/products/{product_id}").json()
    assert detail["stock"] == 8


def test_create_order_insufficient_stock_fails(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, stock=5)
    add_to_cart(normal_user_headers, product_id, 3)
    # 加购后管理员把库存降到 2，模拟下单时库存不足
    client.put(f"/api/products/{product_id}", json={"stock": 2}, headers=admin_headers)

    response = create_order(normal_user_headers)
    assert response.status_code == 400
    assert "库存不足" in response.json()["detail"]
    # 订单未创建，购物车未清空，库存未被扣减
    assert client.get("/api/cart/items", headers=normal_user_headers).json() != []
    assert client.get(f"/api/products/{product_id}").json()["stock"] == 2


def test_create_order_off_sale_fails(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id)
    add_to_cart(normal_user_headers, product_id, 1)
    client.put(f"/api/products/{product_id}", json={"is_on_sale": False}, headers=admin_headers)

    response = create_order(normal_user_headers)
    assert response.status_code == 400
    assert "已下架" in response.json()["detail"]


def test_order_list_pagination_and_detail(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    for _ in range(2):
        product_id = make_product(admin_headers, category_id)
        add_to_cart(normal_user_headers, product_id, 1)
        assert create_order(normal_user_headers).status_code == 201

    page1 = client.get("/api/orders", params={"page": 1, "page_size": 1}, headers=normal_user_headers).json()
    page2 = client.get("/api/orders", params={"page": 2, "page_size": 1}, headers=normal_user_headers).json()
    assert page1["total"] == 2
    assert len(page1["items"]) == 1
    assert len(page2["items"]) == 1
    assert page1["items"][0]["id"] != page2["items"][0]["id"]

    order_id = page1["items"][0]["id"]
    detail = client.get(f"/api/orders/{order_id}", headers=normal_user_headers)
    assert detail.status_code == 200
    assert detail.json()["items"]


def test_cannot_view_other_users_order(admin_headers, normal_user_headers):
    username = f"testuser{uuid4().hex[:8]}"
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "另一个用户"},
    )
    other_headers = {
        "Authorization": f"Bearer {client.post('/api/auth/login', json={'username': username, 'password': 'password123'}).json()['token']}"
    }

    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id)
    add_to_cart(normal_user_headers, product_id, 1)
    order_id = create_order(normal_user_headers).json()["id"]

    assert client.get(f"/api/orders/{order_id}", headers=other_headers).status_code == 404
    assert client.post(f"/api/orders/{order_id}/pay", headers=other_headers).status_code == 404
    assert client.post(f"/api/orders/{order_id}/cancel", headers=other_headers).status_code == 404


def test_pay_order_and_reject_duplicate(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id)
    add_to_cart(normal_user_headers, product_id, 1)
    order_id = create_order(normal_user_headers).json()["id"]

    paid = client.post(f"/api/orders/{order_id}/pay", headers=normal_user_headers)
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"

    duplicate = client.post(f"/api/orders/{order_id}/pay", headers=normal_user_headers)
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "当前状态不可支付"


def test_cancel_order_restores_stock(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, stock=10)
    add_to_cart(normal_user_headers, product_id, 3)
    order_id = create_order(normal_user_headers).json()["id"]
    assert client.get(f"/api/products/{product_id}").json()["stock"] == 7

    cancelled = client.post(f"/api/orders/{order_id}/cancel", headers=normal_user_headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert client.get(f"/api/products/{product_id}").json()["stock"] == 10


def test_cancel_paid_order_rejected(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id)
    add_to_cart(normal_user_headers, product_id, 1)
    order_id = create_order(normal_user_headers).json()["id"]
    client.post(f"/api/orders/{order_id}/pay", headers=normal_user_headers)

    response = client.post(f"/api/orders/{order_id}/cancel", headers=normal_user_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "当前状态不可取消"


def test_create_order_validation(normal_user_headers):
    response = client.post(
        "/api/orders",
        json={"receiver_name": "", "receiver_phone": "", "receiver_address": ""},
        headers=normal_user_headers,
    )
    assert response.status_code == 422
