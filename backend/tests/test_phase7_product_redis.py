"""V2.0-7.3 商品与 Redis 测试：缺口补充。

覆盖：
- 商品 → SKU → 价格 → 库存 关系显式校验（不同 SKU 各自价格/库存、汇总正确）；
- Redis 故障时商品查询 fail-open（仍 200），Logout 与认证链一致 fail-closed（503），
  恢复后 Logout 正常，且故障期间的 503 未产生半完成状态。
"""

from uuid import uuid4

from app.services import cache
from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME, client


def _unique(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:6]}"


def _boom(*args, **kwargs):
    raise RuntimeError("redis down simulated")


def _make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": _unique("test阶段七分类"), "sort_order": 0},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _make_product_with_skus(
    admin_headers: dict, category_id: int, skus: list[dict]
) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": _unique("test阶段七商品"),
            "category_id": category_id,
            "price": 0,
            "stock": 0,
            "description": "阶段七商品与 Redis 测试",
            "skus": skus,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_multi_sku_price_stock_relationship(admin_headers):
    """不同 SKU 各自的价格/库存正确返回，商品汇总=最低价/库存之和。"""
    category_id = _make_category(admin_headers)
    product = _make_product_with_skus(
        admin_headers,
        category_id,
        [
            {
                "sku_code": "P7A",
                "price": 66,
                "stock": 3,
                "is_active": True,
                "specs": [{"name": "净含量", "value": "100g"}],
            },
            {
                "sku_code": "P7B",
                "price": 77,
                "stock": 4,
                "is_active": True,
                "specs": [{"name": "净含量", "value": "200g"}],
            },
        ],
    )

    detail = client.get(f"/api/products/{product['id']}").json()
    by_code = {sku["sku_code"]: sku for sku in detail["skus"]}
    assert set(by_code) == {"P7A", "P7B"}
    assert by_code["P7A"]["price"] == "66.00"
    assert by_code["P7A"]["stock"] == 3
    assert by_code["P7B"]["price"] == "77.00"
    assert by_code["P7B"]["stock"] == 4
    assert detail["price"] == "66.00"
    assert detail["stock"] == 7


def test_logout_fail_closed_and_product_fail_open_under_redis_outage(monkeypatch):
    """Redis 全挂：商品查询仍 200；Logout 与认证链一致 503；恢复后无半完成状态。"""
    login = client.post(
        "/api/auth/login",
        json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
    )
    assert login.status_code == 200
    access = login.json()["token"]
    refresh = login.json()["refresh_token"]
    headers = {"Authorization": f"Bearer {access}"}

    for method in ("get", "set", "exists", "delete", "scan_iter"):
        monkeypatch.setattr(cache.redis_client, method, _boom)

    # 商品/分类缓存 fail-open：查询不中断
    listing = client.get("/api/products", params={"page": 1, "page_size": 12})
    assert listing.status_code == 200

    # 认证链路 fail-closed：Logout 返回 503，不泄露内部细节
    logout = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh},
        headers=headers,
    )
    assert logout.status_code == 503
    assert logout.json()["code"] == "SERVICE_UNAVAILABLE"
    assert "Traceback" not in logout.text

    # 恢复后：故障期间的 503 未产生半完成状态，Logout 仍可正常完成
    monkeypatch.undo()
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200

    done = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh},
        headers=headers,
    )
    assert done.status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
