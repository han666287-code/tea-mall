"""V2.0-6.2 商品缓存测试：Miss→MySQL→Redis、Hit→Redis、过期重建、不存在/非法 ID、管理员独立键、隐私接口不缓存、命中零 SQL。"""

from uuid import uuid4

from sqlalchemy import event

from app.config import settings
from app.database import engine
from app.schemas.product import ProductResponse
from app.services import cache
from tests.conftest import client

_QUERY_COUNT = {"n": 0}


@event.listens_for(engine, "before_cursor_execute")
def _count_queries(conn, cursor, statement, parameters, context, executemany):
    """统计 SQL 查询次数，用于验证缓存命中时零查询。"""
    _QUERY_COUNT["n"] += 1


def _reset_query_count() -> None:
    _QUERY_COUNT["n"] = 0


def _unique(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:6]}"


def _make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": _unique("test缓存分类"), "sort_order": 0},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _make_product(
    admin_headers: dict, category_id: int, *, is_on_sale: bool = True
) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": _unique("test缓存商品"),
            "category_id": category_id,
            "price": 88.8,
            "stock": 10,
            "description": "缓存测试商品",
            "is_on_sale": is_on_sale,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()


def _detail_keys() -> list[str]:
    return list(cache.redis_client.scan_iter(match=f"{cache.KEY_PRODUCT_PREFIX}:*"))


def _assert_response_matches_cached(payload: dict) -> None:
    """缓存内容必须与 API 返回结构完全一致。"""
    model = ProductResponse.model_validate(payload)
    assert model.model_dump(mode="json") == payload


def test_detail_first_query_miss_writes_redis_then_hit(admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    key = cache.product_detail_key(product_id)

    assert cache.exists(key) is False
    first = client.get(f"/api/products/{product_id}")
    assert first.status_code == 200

    # 第一次查询：Miss → MySQL → 写 Redis（带 TTL）
    assert cache.exists(key) is True
    ttl = cache.redis_client.ttl(key)
    assert 0 < ttl <= settings.product_cache_ttl_seconds
    cached = cache.get_json(key)
    _assert_response_matches_cached(cached)
    assert cached == first.json()

    # 第二次查询：Hit → Redis，响应结构与第一次完全一致
    second = client.get(f"/api/products/{product_id}")
    assert second.status_code == 200
    assert second.json() == first.json()
def test_detail_cache_hit_zero_queries(admin_headers):
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    first = client.get(f"/api/products/{product_id}")
    assert first.status_code == 200
    assert cache.exists(cache.product_detail_key(product_id)) is True

    _reset_query_count()
    second = client.get(f"/api/products/{product_id}")
    assert second.status_code == 200
    assert second.json() == first.json()
    assert _QUERY_COUNT["n"] == 0, f"详情命中缓存仍产生 SQL: {_QUERY_COUNT['n']}"


def test_list_first_query_miss_writes_redis_then_hit(admin_headers):
    category_id = _make_category(admin_headers)
    _make_product(admin_headers, category_id)
    key = cache.product_list_key(None, None, 1, 12, False)

    assert cache.exists(key) is False
    first = client.get("/api/products", params={"page": 1, "page_size": 12})
    assert first.status_code == 200

    assert cache.exists(key) is True
    assert 0 < cache.redis_client.ttl(key) <= settings.product_cache_ttl_seconds
    assert cache.get_json(key) == first.json()

    second = client.get("/api/products", params={"page": 1, "page_size": 12})
    assert second.status_code == 200
    assert second.json() == first.json()


def test_list_cache_hit_zero_queries(admin_headers):
    category_id = _make_category(admin_headers)
    _make_product(admin_headers, category_id)
    params = {"page": 1, "page_size": 12}
    first = client.get("/api/products", params=params)
    assert first.status_code == 200

    _reset_query_count()
    second = client.get("/api/products", params=params)
    assert second.status_code == 200
    assert second.json() == first.json()
    assert _QUERY_COUNT["n"] == 0, f"列表命中缓存仍产生 SQL: {_QUERY_COUNT['n']}"


def test_cache_expiry_rebuilds_from_mysql(admin_headers):
    """删除键模拟缓存过期：下次查询重新走 MySQL 并重建缓存。"""
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    product_id = product["id"]
    key = cache.product_detail_key(product_id)

    original = client.get(f"/api/products/{product_id}").json()
    assert cache.exists(key) is True
    cache.delete(key)
    assert cache.exists(key) is False

    _reset_query_count()
    refreshed = client.get(f"/api/products/{product_id}")
    assert refreshed.status_code == 200
    assert _QUERY_COUNT["n"] > 0
    assert cache.exists(key) is True
    assert refreshed.json() == original


def test_non_existent_product_404_no_cache_key(admin_headers):
    category_id = _make_category(admin_headers)
    _make_product(admin_headers, category_id)

    response = client.get("/api/products/99999999")
    assert response.status_code == 404
    assert response.json()["code"] == "PRODUCT_NOT_FOUND"
    assert _detail_keys() == []


def test_invalid_product_id_no_cache_key(admin_headers):
    category_id = _make_category(admin_headers)
    _make_product(admin_headers, category_id)

    assert client.get("/api/products/0").status_code == 404
    assert client.get("/api/products/-1").status_code == 404
    assert client.get("/api/products/abc").status_code == 422
    assert _detail_keys() == []


def test_admin_off_sale_list_uses_independent_cache_key(admin_headers):
    category_id = _make_category(admin_headers)
    on_sale = _make_product(admin_headers, category_id, is_on_sale=True)
    off_sale = _make_product(admin_headers, category_id, is_on_sale=False)

    public = client.get("/api/products", params={"page": 1, "page_size": 12})
    assert public.status_code == 200
    public_key = cache.product_list_key(None, None, 1, 12, False)
    assert cache.exists(public_key) is True
    public_ids = {item["id"] for item in public.json()["items"]}
    assert on_sale["id"] in public_ids
    assert off_sale["id"] not in public_ids

    admin_list = client.get(
        "/api/products",
        params={"page": 1, "page_size": 12, "include_off_sale": True},
        headers=admin_headers,
    )
    assert admin_list.status_code == 200
    admin_key = cache.product_list_key(None, None, 1, 12, True)
    assert cache.exists(admin_key) is True
    assert admin_key != public_key
    admin_ids = {item["id"] for item in admin_list.json()["items"]}
    assert on_sale["id"] in admin_ids
    assert off_sale["id"] in admin_ids

    # 两个独立缓存键互不影响
    cached_public_ids = {item["id"] for item in cache.get_json(public_key)["items"]}
    cached_admin_ids = {item["id"] for item in cache.get_json(admin_key)["items"]}
    assert off_sale["id"] not in cached_public_ids
    assert off_sale["id"] in cached_admin_ids


def test_off_sale_detail_not_cached_for_admin(admin_headers):
    category_id = _make_category(admin_headers)
    off_sale = _make_product(admin_headers, category_id, is_on_sale=False)
    on_sale = _make_product(admin_headers, category_id, is_on_sale=True)

    # 公开访问下架商品详情：404，且不产生缓存键
    assert client.get(f"/api/products/{off_sale['id']}").status_code == 404
    assert cache.exists(cache.product_detail_key(off_sale["id"])) is False

    # 管理员可见下架商品详情，但仍保持直查 MySQL、不缓存
    admin_detail = client.get(
        f"/api/products/{off_sale['id']}", headers=admin_headers
    )
    assert admin_detail.status_code == 200
    assert cache.exists(cache.product_detail_key(off_sale["id"])) is False

    # 对照组：上架商品详情正常缓存
    assert client.get(f"/api/products/{on_sale['id']}").status_code == 200
    assert cache.exists(cache.product_detail_key(on_sale["id"])) is True


def test_cart_order_user_endpoints_create_no_cache_keys(
    admin_headers, normal_user_headers
):
    """购物车/订单/用户接口不得产生 cache:* 键（隐私与实时数据不缓存）。"""
    category_id = _make_category(admin_headers)
    product = _make_product(admin_headers, category_id)
    sku_id = product["skus"][0]["id"]

    assert client.get("/api/auth/me", headers=normal_user_headers).status_code == 200
    assert client.post(
        "/api/cart/items",
        json={"sku_id": sku_id, "quantity": 1},
        headers=normal_user_headers,
    ).status_code == 201
    assert client.get("/api/cart/items", headers=normal_user_headers).status_code == 200
    assert client.post(
        "/api/orders",
        json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "receiver_address": "上海市浦东新区",
        },
        headers=normal_user_headers,
    ).status_code == 201
    assert client.get("/api/orders", headers=normal_user_headers).status_code == 200

    cache_keys = list(cache.redis_client.scan_iter(match="cache:*"))
    assert cache_keys == []
