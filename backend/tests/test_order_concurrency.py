"""V2.0-1.4 库存并发一致性回归测试（FOR UPDATE 防超卖）。"""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from tests.conftest import client


def make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": f"test并发分类{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    )
    return response.json()["id"]


def make_product(admin_headers: dict, category_id: int, stock: int) -> int:
    response = client.post(
        "/api/products",
        json={
            "name": f"test并发商品{uuid4().hex[:6]}",
            "category_id": category_id,
            "price": 10,
            "stock": stock,
            "is_on_sale": True,
        },
        headers=admin_headers,
    )
    return response.json()["id"]


def register_and_login() -> dict:
    username = f"testuser{uuid4().hex[:8]}"
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "并发用户"},
    )
    response = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    return {"Authorization": f"Bearer {response.json()['token']}"}


def add_to_cart(headers: dict, product_id: int) -> None:
    response = client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": 1}, headers=headers
    )
    assert response.status_code == 201


def create_order(headers: dict) -> int:
    response = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=headers,
    )
    return response.status_code


def test_concurrent_orders_do_not_oversell(admin_headers, normal_user_headers):
    # 两个用户对同一件库存=1 的商品并发下单：恰好一单成功，另一单 400，库存归 0
    for round_index in range(5):
        category_id = make_category(admin_headers)
        product_id = make_product(admin_headers, category_id, stock=1)
        user_b_headers = register_and_login()

        add_to_cart(normal_user_headers, product_id)
        add_to_cart(user_b_headers, product_id)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(create_order, normal_user_headers),
                executor.submit(create_order, user_b_headers),
            ]
            statuses = sorted(f.result() for f in futures)

        assert statuses == [201, 400], f"第 {round_index + 1} 轮出现超卖: {statuses}"
        assert client.get(f"/api/products/{product_id}").json()["stock"] == 0
