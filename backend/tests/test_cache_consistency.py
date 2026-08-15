"""V2.0-6.3 缓存失效与一致性测试。

验证原则：数据库修改成功后必须先清除相关 Redis 缓存，下一次查询重新读取 MySQL
并重建缓存；失效操作不得影响 auth:* 认证键（Refresh Token 必须继续可用）。
"""

from uuid import uuid4

from app.core.security import hash_refresh_token
from app.services import cache
from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME, client


def _unique(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:6]}"


def _make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": _unique("test一致分类"), "sort_order": 0},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _make_product(
    admin_headers: dict, category_id: int, *, is_on_sale: bool = True, stock: int = 10
) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": _unique("test一致商品"),
            "category_id": category_id,
            "price": 88.8,
            "stock": stock,
            "description": "一致性测试商品",
            "is_on_sale": is_on_sale,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def _populate_product_caches(product_id: int) -> None:
    """查询详情与公开列表，让两者都命中缓存。"""
    assert client.get(f"/api/products/{product_id}").status_code == 200
    assert client.get("/api/products", params={"page": 1, "page_size": 12}).status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True
    assert (
        cache.exists(cache.product_list_key(None, None, 1, 12, False)) is True
    )


def _assert_no_product_cache() -> None:
    """商品列表/详情缓存必须被全部清除。"""
    leftovers = list(
        cache.redis_client.scan_iter(match=f"{cache.KEY_PRODUCTS_PREFIX}:*")
    ) + list(cache.redis_client.scan_iter(match=f"{cache.KEY_PRODUCT_PREFIX}:*"))
    assert leftovers == [], f"存在未清除的商品缓存键: {leftovers}"


def _login_refresh_token() -> dict:
    response = client.post(
        "/api/auth/login",
        json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return response.json()


def test_name_update_invalidates_detail_and_list_cache(admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    _populate_product_caches(product_id)

    new_name = _unique("test改名后")
    response = client.put(
        f"/api/products/{product_id}",
        json={"name": new_name},
        headers=admin_headers,
    )
    assert response.status_code == 200

    _assert_no_product_cache()
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == new_name


def test_price_update_invalidates_detail_cache(admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    assert client.get(f"/api/products/{product_id}").status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True

    response = client.put(
        f"/api/products/{product_id}",
        json={"price": 199.9},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["price"] == "199.90"

    _assert_no_product_cache()
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["price"] == "199.90"


def test_on_sale_toggle_invalidates_cache(admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    assert client.get(f"/api/products/{product_id}").status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True

    # 下架：缓存清除，公开详情 404，管理员可见
    off = client.put(
        f"/api/products/{product_id}",
        json={"is_on_sale": False},
        headers=admin_headers,
    )
    assert off.status_code == 200
    _assert_no_product_cache()
    assert client.get(f"/api/products/{product_id}").status_code == 404
    admin_detail = client.get(f"/api/products/{product_id}", headers=admin_headers)
    assert admin_detail.status_code == 200
    assert admin_detail.json()["is_on_sale"] is False

    # 重新上架：缓存重建后返回最新状态
    on = client.put(
        f"/api/products/{product_id}",
        json={"is_on_sale": True},
        headers=admin_headers,
    )
    assert on.status_code == 200
    assert client.get(f"/api/products/{product_id}").status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True


def test_category_change_invalidates_cache(admin_headers):
    category_a = _make_category(admin_headers)
    category_b = _make_category(admin_headers)
    product = _make_product(admin_headers, category_a)
    product_id = product["id"]
    _populate_product_caches(product_id)

    response = client.put(
        f"/api/products/{product_id}",
        json={"category_id": category_b},
        headers=admin_headers,
    )
    assert response.status_code == 200

    _assert_no_product_cache()
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["category_id"] == category_b


def test_category_rename_invalidates_categories_and_products_cache(admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    assert client.get("/api/categories").status_code == 200
    assert cache.exists(cache.KEY_CATEGORIES) is True
    _populate_product_caches(product_id)

    new_name = _unique("test分类改名后")
    response = client.put(
        f"/api/categories/{category_id}",
        json={"name": new_name},
        headers=admin_headers,
    )
    assert response.status_code == 200

    assert cache.exists(cache.KEY_CATEGORIES) is False
    _assert_no_product_cache()
    categories = client.get("/api/categories").json()
    assert any(item["name"] == new_name for item in categories)
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["category_name"] == new_name


def test_sku_replace_invalidates_detail_cache(admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    assert client.get(f"/api/products/{product_id}").status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True

    response = client.put(
        f"/api/products/{product_id}/skus",
        json=[
            {
                "sku_code": "SKU-NEW-001",
                "price": 129.9,
                "stock": 5,
                "is_active": True,
                "specs": [{"name": "规格", "value": "A"}],
            }
        ],
        headers=admin_headers,
    )
    assert response.status_code == 200

    _assert_no_product_cache()
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["skus"][0]["sku_code"] == "SKU-NEW-001"
    assert detail.json()["skus"][0]["price"] == "129.90"


def test_image_upload_invalidates_detail_cache(admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    assert client.get(f"/api/products/{product_id}").status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True

    response = client.post(
        f"/api/products/{product_id}/image",
        files={"file": ("tea.png", b"\x89PNG\r\n\x1a\nfake-image", "image/png")},
        headers=admin_headers,
    )
    assert response.status_code == 200

    _assert_no_product_cache()
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["image_url"].startswith("/uploads/")


def test_delete_product_invalidates_cache(admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    _populate_product_caches(product_id)

    response = client.delete(f"/api/products/{product_id}", headers=admin_headers)
    assert response.status_code == 204

    _assert_no_product_cache()
    assert client.get(f"/api/products/{product_id}").status_code == 404


def test_order_create_invalidates_detail_cache_with_new_stock(
    admin_headers, normal_user_headers
):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id, stock=10)
    product_id = product["id"]
    sku_id = product["skus"][0]["id"]
    assert client.get(f"/api/products/{product_id}").status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True

    assert client.post(
        "/api/cart/items",
        json={"sku_id": sku_id, "quantity": 2},
        headers=normal_user_headers,
    ).status_code == 201
    assert client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=normal_user_headers,
    ).status_code == 201

    _assert_no_product_cache()
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["stock"] == 8


def test_user_cancel_order_invalidates_cache_with_restored_stock(
    admin_headers, normal_user_headers
):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id, stock=10)
    product_id = product["id"]
    sku_id = product["skus"][0]["id"]
    assert client.get(f"/api/products/{product_id}").status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True

    client.post(
        "/api/cart/items",
        json={"sku_id": sku_id, "quantity": 2},
        headers=normal_user_headers,
    )
    order_id = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=normal_user_headers,
    ).json()["id"]
    # 下单扣库存后旧缓存被清除
    assert cache.exists(cache.product_detail_key(product_id)) is False
    # 重新查询：从 MySQL 读取新库存并重建缓存
    assert client.get(f"/api/products/{product_id}").json()["stock"] == 8
    assert cache.exists(cache.product_detail_key(product_id)) is True

    cancel = client.post(f"/api/orders/{order_id}/cancel", headers=normal_user_headers)
    assert cancel.status_code == 200
    # 取消恢复库存后旧缓存再次被清除，重新查询返回恢复后的库存
    assert cache.exists(cache.product_detail_key(product_id)) is False

    _assert_no_product_cache()
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["stock"] == 10


def test_admin_cancel_order_invalidates_cache(admin_headers, normal_user_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id, stock=10)
    product_id = product["id"]
    sku_id = product["skus"][0]["id"]
    assert client.get(f"/api/products/{product_id}").status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True

    client.post(
        "/api/cart/items",
        json={"sku_id": sku_id, "quantity": 2},
        headers=normal_user_headers,
    )
    order_id = client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=normal_user_headers,
    ).json()["id"]
    assert cache.exists(cache.product_detail_key(product_id)) is False
    assert client.get(f"/api/products/{product_id}").json()["stock"] == 8
    assert cache.exists(cache.product_detail_key(product_id)) is True
    assert client.post(f"/api/orders/{order_id}/pay", headers=normal_user_headers).status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True

    cancel = client.patch(
        f"/api/admin/orders/{order_id}/status",
        json={"status": "cancelled"},
        headers=admin_headers,
    )
    assert cancel.status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is False

    _assert_no_product_cache()
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["stock"] == 10


def test_cache_invalidation_does_not_touch_auth_keys(admin_headers):
    """商品变更清除业务缓存后，Refresh Token 等认证键不受影响且仍可换发新令牌。"""
    login = _login_refresh_token()
    refresh_fp_key = f"auth:refresh:{hash_refresh_token(login['refresh_token'])}"
    assert cache.redis_client.exists(refresh_fp_key) == 1

    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    _populate_product_caches(product_id)

    client.put(
        f"/api/products/{product_id}",
        json={"name": _unique("test改名后")},
        headers=admin_headers,
    )
    _assert_no_product_cache()

    # 认证键仍在，Refresh Token 可正常换发
    assert cache.redis_client.exists(refresh_fp_key) == 1
    refresh = client.post(
        "/api/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert refresh.status_code == 200
    assert refresh.json().get("token")
    assert refresh.json().get("refresh_token")
