"""管理端订单接口测试：权限、状态筛选、状态机校验、取消恢复库存。"""

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


def create_order_for_user(user_headers: dict, admin_headers: dict) -> dict:
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id)
    client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": 1}, headers=user_headers
    )
    response = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=user_headers,
    )
    return response.json()


def test_admin_orders_requires_admin(normal_user_headers):
    assert client.get("/api/admin/orders").status_code == 401
    assert client.get("/api/admin/orders", headers=normal_user_headers).status_code == 403


def test_admin_list_and_filter_by_status(admin_headers, normal_user_headers):
    order1 = create_order_for_user(normal_user_headers, admin_headers)
    order2 = create_order_for_user(normal_user_headers, admin_headers)
    client.post(f"/api/orders/{order2['id']}/pay", headers=normal_user_headers)

    all_orders = client.get("/api/admin/orders", headers=admin_headers).json()
    assert all_orders["total"] >= 2
    assert {item["id"] for item in all_orders["items"]} >= {order1["id"], order2["id"]}
    # 管理端能看到下单用户名
    assert all(item["username"] for item in all_orders["items"])

    pending = client.get("/api/admin/orders", params={"status": "pending"}, headers=admin_headers).json()
    paid = client.get("/api/admin/orders", params={"status": "paid"}, headers=admin_headers).json()
    assert all(item["status"] == "pending" for item in pending["items"])
    assert all(item["status"] == "paid" for item in paid["items"])


def test_valid_status_flow(admin_headers, normal_user_headers):
    order = create_order_for_user(normal_user_headers, admin_headers)
    order_id = order["id"]

    paid = client.patch(
        f"/api/admin/orders/{order_id}/status", json={"status": "paid"}, headers=admin_headers
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"

    shipped = client.patch(
        f"/api/admin/orders/{order_id}/status", json={"status": "shipped"}, headers=admin_headers
    )
    assert shipped.status_code == 200
    assert shipped.json()["status"] == "shipped"

    completed = client.patch(
        f"/api/admin/orders/{order_id}/status", json={"status": "completed"}, headers=admin_headers
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"


def test_invalid_transitions_rejected(admin_headers, normal_user_headers):
    order = create_order_for_user(normal_user_headers, admin_headers)
    order_id = order["id"]

    # 未支付直接发货
    response = client.patch(
        f"/api/admin/orders/{order_id}/status", json={"status": "shipped"}, headers=admin_headers
    )
    assert response.status_code == 400

    client.patch(f"/api/admin/orders/{order_id}/status", json={"status": "paid"}, headers=admin_headers)
    client.patch(f"/api/admin/orders/{order_id}/status", json={"status": "shipped"}, headers=admin_headers)
    # 发货后不可取消
    response = client.patch(
        f"/api/admin/orders/{order_id}/status", json={"status": "cancelled"}, headers=admin_headers
    )
    assert response.status_code == 400


def test_admin_cancel_paid_order_restores_stock(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, stock=10)
    client.post(
        "/api/cart/items", json={"product_id": product_id, "quantity": 2}, headers=normal_user_headers
    )
    order = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海",
        },
        headers=normal_user_headers,
    ).json()
    client.post(f"/api/orders/{order['id']}/pay", headers=normal_user_headers)
    assert client.get(f"/api/products/{product_id}").json()["stock"] == 8

    cancelled = client.patch(
        f"/api/admin/orders/{order['id']}/status",
        json={"status": "cancelled"},
        headers=admin_headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert client.get(f"/api/products/{product_id}").json()["stock"] == 10


def test_admin_status_update_requires_admin(normal_user_headers):
    assert (
        client.patch("/api/admin/orders/1/status", json={"status": "paid"}).status_code == 401
    )
    assert (
        client.patch(
            "/api/admin/orders/1/status", json={"status": "paid"}, headers=normal_user_headers
        ).status_code
        == 403
    )


def test_admin_update_nonexistent_order(admin_headers):
    response = client.patch(
        "/api/admin/orders/999999/status", json={"status": "paid"}, headers=admin_headers
    )
    assert response.status_code == 404


def test_admin_update_invalid_status_value(admin_headers):
    response = client.patch(
        "/api/admin/orders/1/status", json={"status": "unknown"}, headers=admin_headers
    )
    assert response.status_code == 422
