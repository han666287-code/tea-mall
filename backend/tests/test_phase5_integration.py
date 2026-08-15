"""V2.0-5.2/5.3 认证与业务整合测试。

5.2 权限矩阵：未登录 401 / 普通用户 403 / Admin 成功，
覆盖商品查询、新增、修改、SKU 替换、库存修改、上下架；
5.3 用户状态联动：DISABLED 用户/Admin 旧 Token 访问受保护业务端点全部被拒，
直接改库禁用（不 bump epoch）同样被 401 拦截。
"""

from uuid import uuid4

from sqlalchemy import select

from app.database import SessionLocal
from app.models.user import User
from tests.conftest import client


def unique_name(prefix: str = "testp5商品") -> str:
    return f"{prefix}{uuid4().hex[:6]}"


def make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": f"testp5分类{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def make_product(
    admin_headers: dict,
    category_id: int,
    name: str,
    is_on_sale: bool = True,
    stock: int = 10,
    price: float = 66.5,
) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": name,
            "category_id": category_id,
            "price": price,
            "stock": stock,
            "description": "5.2 权限矩阵测试商品",
            "is_on_sale": is_on_sale,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_public_list_and_detail_accessible_to_all(admin_headers, normal_user_headers):
    """商品查询：游客、普通用户、Admin 均可浏览上架商品列表与详情。"""
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id, unique_name())

    public_list = client.get("/api/products").json()
    assert any(item["id"] == product["id"] for item in public_list["items"])

    assert client.get("/api/products").status_code == 200
    assert client.get(
        "/api/products", headers=normal_user_headers
    ).status_code == 200
    assert client.get(
        f"/api/products/{product['id']}"
    ).status_code == 200
    assert client.get(
        f"/api/products/{product['id']}", headers=normal_user_headers
    ).status_code == 200


def test_include_off_sale_query_requires_admin(admin_headers, normal_user_headers):
    """查询下架商品列表：游客/普通用户 403，Admin 200。"""
    category_id = make_category(admin_headers)
    make_product(admin_headers, category_id, unique_name(), is_on_sale=False)

    for headers in (None, normal_user_headers):
        response = client.get(
            "/api/products", params={"include_off_sale": True}, headers=headers
        )
        assert response.status_code == 403
        assert response.json()["code"] == "ADMIN_PERMISSION_REQUIRED"

    response = client.get(
        "/api/products",
        params={"include_off_sale": True},
        headers=admin_headers,
    )
    assert response.status_code == 200


def test_off_sale_detail_hidden_for_non_admin(admin_headers, normal_user_headers):
    """下架商品详情：游客/普通用户按 404 隐藏，Admin 可见。"""
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id, unique_name(), is_on_sale=False)

    assert client.get(f"/api/products/{product['id']}").status_code == 404
    assert (
        client.get(
            f"/api/products/{product['id']}", headers=normal_user_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/products/{product['id']}", headers=admin_headers
        ).status_code
        == 200
    )


def test_create_product_permission_matrix(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    payload = {
        "name": unique_name(),
        "category_id": category_id,
        "price": 66.5,
        "stock": 10,
    }

    assert client.post("/api/products", json=payload).status_code == 401
    assert (
        client.post(
            "/api/products", json=payload, headers=normal_user_headers
        ).status_code
        == 403
    )
    assert (
        client.post("/api/products", json=payload, headers=admin_headers).status_code
        == 201
    )


def test_update_product_permission_matrix(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id, unique_name())
    new_name = unique_name("testp5改名")

    assert client.put(f"/api/products/{product['id']}", json={"name": new_name}).status_code == 401
    assert (
        client.put(
            f"/api/products/{product['id']}",
            json={"name": new_name},
            headers=normal_user_headers,
        ).status_code
        == 403
    )
    response = client.put(
        f"/api/products/{product['id']}",
        json={"name": new_name},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == new_name


def test_replace_skus_permission_matrix(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id, unique_name())
    skus = [
        {
            "sku_code": "P5-SKU-001",
            "price": 88.0,
            "stock": 5,
            "is_active": True,
            "specs": [],
        }
    ]

    assert (
        client.put(f"/api/products/{product['id']}/skus", json=skus).status_code
        == 401
    )
    assert (
        client.put(
            f"/api/products/{product['id']}/skus",
            json=skus,
            headers=normal_user_headers,
        ).status_code
        == 403
    )
    response = client.put(
        f"/api/products/{product['id']}/skus",
        json=skus,
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["skus"][0]["sku_code"] == "P5-SKU-001"


def test_stock_update_permission_matrix(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id, unique_name())

    assert (
        client.put(f"/api/products/{product['id']}", json={"stock": 3}).status_code
        == 401
    )
    assert (
        client.put(
            f"/api/products/{product['id']}",
            json={"stock": 3},
            headers=normal_user_headers,
        ).status_code
        == 403
    )
    response = client.put(
        f"/api/products/{product['id']}",
        json={"stock": 3},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["stock"] == 3


def test_on_off_shelf_permission_matrix(admin_headers, normal_user_headers):
    """上下架：游客/普通用户 401/403，Admin 可下架且下架后对非 Admin 隐藏。"""
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id, unique_name())

    assert (
        client.put(
            f"/api/products/{product['id']}", json={"is_on_sale": False}
        ).status_code
        == 401
    )
    assert (
        client.put(
            f"/api/products/{product['id']}",
            json={"is_on_sale": False},
            headers=normal_user_headers,
        ).status_code
        == 403
    )
    response = client.put(
        f"/api/products/{product['id']}",
        json={"is_on_sale": False},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_on_sale"] is False

    # 下架后：游客/普通用户详情 404，Admin 可见
    assert client.get(f"/api/products/{product['id']}").status_code == 404
    assert (
        client.get(
            f"/api/products/{product['id']}", headers=normal_user_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/products/{product['id']}", headers=admin_headers
        ).status_code
        == 200
    )


# ---------------- V2.0-5.3 用户状态与业务联动 ----------------


def register_and_login(username: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "5.3状态测试"},
    )
    assert response.status_code == 201
    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login.status_code == 200
    return login.json()


def unique_username() -> str:
    return f"testp5status{uuid4().hex[:8]}"


def disable_via_admin(username: str, admin_headers: dict) -> None:
    """通过管理端接口禁用（触发 epoch+1，全部旧 Token 失效）。"""
    users = client.get(
        f"/api/admin/users?keyword={username}", headers=admin_headers
    ).json()["items"]
    assert users, "测试用户应存在"
    response = client.patch(
        f"/api/admin/users/{users[0]['id']}/status",
        json={"status": "disabled"},
        headers=admin_headers,
    )
    assert response.status_code == 200


def set_status_in_db(username: str, status: str) -> None:
    """直接改库状态（绕过管理端 API，不触发 epoch 递增）。"""
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        assert user is not None
        user.status = status
        db.commit()


def test_disabled_user_old_token_blocked_on_cart_orders_and_product_write(
    admin_headers,
):
    """管理端禁用（epoch 失效路径）：购物车/订单/商品写接口旧 Token 全部 401。"""
    username = unique_username()
    body = register_and_login(username)
    headers = {"Authorization": f"Bearer {body['token']}"}

    assert client.get("/api/cart/items", headers=headers).status_code == 200
    assert client.get("/api/orders", headers=headers).status_code == 200

    disable_via_admin(username, admin_headers)

    assert client.get("/api/cart/items", headers=headers).status_code == 401
    assert client.get("/api/orders", headers=headers).status_code == 401
    assert client.post("/api/products", json={}, headers=headers).status_code == 401


def test_direct_db_disable_old_token_blocked_on_business_apis(admin_headers):
    """直改库禁用（Token 纪元未变）：业务端点仍按 ACCOUNT_DISABLED 401 拦截。"""
    username = unique_username()
    body = register_and_login(username)
    headers = {"Authorization": f"Bearer {body['token']}"}

    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id, unique_name())

    assert client.get("/api/cart/items", headers=headers).status_code == 200
    set_status_in_db(username, "disabled")

    cart = client.get("/api/cart/items", headers=headers)
    assert cart.status_code == 401
    assert cart.json()["code"] == "ACCOUNT_DISABLED"

    update = client.put(
        f"/api/products/{product['id']}", json={"stock": 1}, headers=headers
    )
    assert update.status_code == 401
    assert update.json()["code"] == "ACCOUNT_DISABLED"


def promote_to_admin(username: str, admin_headers: dict) -> int:
    users = client.get(
        f"/api/admin/users?keyword={username}", headers=admin_headers
    ).json()["items"]
    assert users, "测试用户应存在"
    user_id = users[0]["id"]
    response = client.patch(
        f"/api/admin/users/{user_id}/role",
        json={"role": "admin"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    return user_id


def test_disabled_admin_old_token_blocked_on_admin_apis(admin_headers):
    """DISABLED Admin（epoch 失效路径）：旧 Token 访问 Admin 接口全部被拒。"""
    username = unique_username()
    body = register_and_login(username)
    promote_to_admin(username, admin_headers)
    headers = {"Authorization": f"Bearer {body['token']}"}

    assert client.get("/api/admin/users", headers=headers).status_code == 200
    assert client.get("/api/admin/orders", headers=headers).status_code == 200

    disable_via_admin(username, admin_headers)

    assert client.get("/api/admin/users", headers=headers).status_code == 401
    assert client.get("/api/admin/orders", headers=headers).status_code == 401
    assert client.post("/api/products", json={}, headers=headers).status_code == 401


def test_direct_db_disable_admin_old_token_blocked_on_admin_apis(admin_headers):
    """直改库禁用 Admin：旧 Token 访问 Admin 接口 401，且可选认证按匿名处理。"""
    username = unique_username()
    body = register_and_login(username)
    promote_to_admin(username, admin_headers)
    headers = {"Authorization": f"Bearer {body['token']}"}

    category_id = make_category(admin_headers)
    off_sale = make_product(admin_headers, category_id, unique_name(), is_on_sale=False)

    assert client.get("/api/admin/users", headers=headers).status_code == 200
    set_status_in_db(username, "disabled")

    admin_users = client.get("/api/admin/users", headers=headers)
    assert admin_users.status_code == 401
    assert admin_users.json()["code"] == "ACCOUNT_DISABLED"

    # 可选认证路径：DISABLED Admin 被视为匿名，下架商品详情按 404 隐藏
    assert client.get(f"/api/products/{off_sale['id']}", headers=headers).status_code == 404
