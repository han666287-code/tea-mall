"""V2.0-7.5 基础并发测试。

仅使用 ThreadPoolExecutor（无额外依赖），覆盖：
并发商品列表查询 / 并发商品详情 / 并发缓存 Miss 同一商品 /
并发登录（不同用户，避开同用户名限流互扰）/ 并发 Admin 只读 API。

本阶段不做订单库存锁定、扣减与回滚（留待后续订单阶段）。
"""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from app.services import cache
from tests.conftest import client


def _unique(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:8]}"


def _make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": _unique("test并发分类"), "sort_order": 0},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _make_product(admin_headers: dict, category_id: int) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": _unique("test并发商品"),
            "category_id": category_id,
            "price": 9.9,
            "stock": 50,
            "is_on_sale": True,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def _run_concurrently(fn, workers: int = 8):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda _: fn(), range(workers)))


def test_concurrent_product_list_queries(admin_headers):
    """多个请求同时查询商品列表：全部 200 且包含目标商品。"""
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)

    responses = _run_concurrently(
        lambda: client.get("/api/products", params={"page": 1, "page_size": 12})
    )
    assert all(r.status_code == 200 for r in responses)
    assert all(
        any(p["id"] == product["id"] for p in r.json()["items"])
        for r in responses
    )


def test_concurrent_product_detail_queries(admin_headers):
    """多个请求同时访问商品详情：全部 200 且返回同一商品。"""
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)

    responses = _run_concurrently(
        lambda: client.get(f"/api/products/{product['id']}")
    )
    assert all(r.status_code == 200 for r in responses)
    assert all(r.json()["id"] == product["id"] for r in responses)


def test_concurrent_cache_miss_product_detail(admin_headers):
    """缓存不存在时并发访问同一商品：全部回源 MySQL 成功并重建缓存。"""
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    key = cache.product_detail_key(product["id"])
    assert cache.exists(key) is False

    responses = _run_concurrently(
        lambda: client.get(f"/api/products/{product['id']}")
    )
    assert all(r.status_code == 200 for r in responses)
    assert all(r.json()["id"] == product["id"] for r in responses)
    assert cache.exists(key) is True
    assert cache.get_json(key)["id"] == product["id"]


def test_concurrent_login_distinct_users():
    """多个请求同时执行登录（不同用户）：全部成功。"""

    def do_login():
        username = _unique("test并发登录")
        registered = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": "password123",
                "nickname": "并发用户",
            },
        )
        assert registered.status_code == 201
        return client.post(
            "/api/auth/login", json={"username": username, "password": "password123"}
        )

    responses = _run_concurrently(do_login)
    assert all(r.status_code == 200 for r in responses)
    assert all(r.json().get("token") for r in responses)


def test_concurrent_admin_read_only_apis(admin_headers):
    """多个请求同时访问商品管理类只读 API：全部 200。"""
    users = _run_concurrently(
        lambda: client.get("/api/admin/users", headers=admin_headers)
    )
    assert all(r.status_code == 200 for r in users), [
        (r.status_code, r.text[:120]) for r in users
    ]

    off_sale = _run_concurrently(
        lambda: client.get(
            "/api/products",
            params={"include_off_sale": "true"},
            headers=admin_headers,
        )
    )
    assert all(r.status_code == 200 for r in off_sale), [
        r.status_code for r in off_sale
    ]
