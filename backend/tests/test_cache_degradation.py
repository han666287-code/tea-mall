"""V2.0-6.4 Redis 故障降级测试。

三层语义：
- 商品/分类缓存：fail-open（GET/SET 失败回退 MySQL，业务不中断）；
- 认证链路（token_store）：fail-closed（Redis 故障返回 503，不放行失效令牌）；
- 登录限流：fail-open（Redis 故障放行，不误伤正常用户）。
"""

from uuid import uuid4

from app.services import cache
from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME, client


def _boom(*args, **kwargs):
    raise RuntimeError("redis down simulated")


def _unique(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:6]}"


def _make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": _unique("test降级分类"), "sort_order": 0},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _make_product(admin_headers: dict, category_id: int) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": _unique("test降级商品"),
            "category_id": category_id,
            "price": 66.6,
            "stock": 10,
            "description": "降级测试商品",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def _login() -> dict:
    response = client.post(
        "/api/auth/login",
        json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return response.json()


def test_product_list_get_failure_falls_back_to_mysql(monkeypatch, admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    monkeypatch.setattr(cache.redis_client, "get", _boom)

    response = client.get("/api/products", params={"page": 1, "page_size": 12})
    assert response.status_code == 200
    assert any(item["id"] == product["id"] for item in response.json()["items"])


def test_product_detail_get_failure_falls_back_to_mysql(monkeypatch, admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    monkeypatch.setattr(cache.redis_client, "get", _boom)

    response = client.get(f"/api/products/{product['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == product["id"]
    assert response.json()["name"] == product["name"]


def test_product_list_set_failure_returns_mysql_data(monkeypatch, admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    monkeypatch.setattr(cache.redis_client, "set", _boom)

    response = client.get("/api/products", params={"page": 1, "page_size": 12})
    assert response.status_code == 200
    assert any(item["id"] == product["id"] for item in response.json()["items"])


def test_product_detail_set_failure_returns_mysql_data(monkeypatch, admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    monkeypatch.setattr(cache.redis_client, "set", _boom)

    response = client.get(f"/api/products/{product['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == product["id"]


def test_full_redis_outage_product_queries_still_work(monkeypatch, admin_headers):
    """Redis 全部操作失败时，商品列表/详情必须仍能通过 MySQL 正常返回（无 500）。"""
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    for method in ("get", "set", "exists", "delete", "scan_iter"):
        monkeypatch.setattr(cache.redis_client, method, _boom)

    listing = client.get("/api/products", params={"page": 1, "page_size": 12})
    assert listing.status_code == 200
    assert any(item["id"] == product["id"] for item in listing.json()["items"])

    detail = client.get(f"/api/products/{product['id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == product["id"]


def test_categories_get_failure_falls_back_to_mysql(monkeypatch, admin_headers):
    category_id = _make_category(admin_headers)
    monkeypatch.setattr(cache.redis_client, "get", _boom)

    response = client.get("/api/categories")
    assert response.status_code == 200
    assert any(item["id"] == category_id for item in response.json())


def test_redis_recovery_rebuilds_product_cache(monkeypatch, admin_headers):
    """故障期间不写缓存；恢复后首次查询重新从 MySQL 建立缓存。"""
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    key = cache.product_detail_key(product_id)

    monkeypatch.setattr(cache.redis_client, "get", _boom)
    monkeypatch.setattr(cache.redis_client, "set", _boom)
    during = client.get(f"/api/products/{product_id}")
    assert during.status_code == 200
    assert cache.exists(key) is False

    monkeypatch.undo()
    assert cache.exists(key) is False
    recovered = client.get(f"/api/products/{product_id}")
    assert recovered.status_code == 200
    assert recovered.json()["id"] == product_id
    assert cache.exists(key) is True
    assert cache.get_json(key) == recovered.json()


def test_login_fail_closed_when_redis_down(monkeypatch):
    """Redis 写入失败时登录按 fail-closed 返回 503，不得放行。"""
    monkeypatch.setattr(cache.redis_client, "set", _boom)
    response = client.post(
        "/api/auth/login",
        json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    assert "Traceback" not in response.text


def test_refresh_fail_closed_when_redis_down(monkeypatch):
    """Redis 读取失败时 Refresh Token 换发按 fail-closed 返回 503。"""
    login = _login()
    monkeypatch.setattr(cache.redis_client, "get", _boom)
    response = client.post(
        "/api/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"


def test_auth_recovery_after_redis_down(monkeypatch):
    """Redis 恢复后登录、刷新、登出全部恢复正常。"""
    monkeypatch.setattr(cache.redis_client, "set", _boom)
    assert (
        client.post(
            "/api/auth/login",
            json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
        ).status_code
        == 503
    )

    monkeypatch.undo()
    login = _login()
    headers = {"Authorization": f"Bearer {login['token']}"}
    refresh = client.post(
        "/api/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert refresh.status_code == 200
    assert refresh.json().get("token")
    assert refresh.json().get("refresh_token")

    logout = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh.json()["refresh_token"]},
        headers=headers,
    )
    assert logout.status_code == 200
    # 登出后旧 Access Token 已失效
    assert client.get("/api/auth/me", headers=headers).status_code == 401
