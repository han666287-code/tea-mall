"""商品接口测试：公开查询、搜索、分页、权限、图片上传、缓存失效。"""

from uuid import uuid4

from app.config import UPLOAD_DIR
from tests.conftest import client


def unique_name(prefix: str = "test商品") -> str:
    return f"{prefix}{uuid4().hex[:6]}"


def make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": f"test分类{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    )
    return response.json()["id"]


def make_product(
    admin_headers: dict,
    category_id: int,
    name: str,
    is_on_sale: bool = True,
    stock: int = 10,
    price: float = 66.5,
):
    return client.post(
        "/api/products",
        json={
            "name": name,
            "category_id": category_id,
            "price": price,
            "stock": stock,
            "description": "测试商品描述",
            "is_on_sale": is_on_sale,
        },
        headers=admin_headers,
    )


def test_create_product_permissions(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    payload = {
        "name": unique_name(),
        "category_id": category_id,
        "price": 66.5,
        "stock": 10,
    }
    assert client.post("/api/products", json=payload).status_code == 401
    assert client.post("/api/products", json=payload, headers=normal_user_headers).status_code == 403
    response = client.post("/api/products", json=payload, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["name"] == payload["name"]
    assert response.json()["category_name"] is not None


def test_create_product_id_is_max_plus_one(admin_headers):
    """新商品 ID = 现存最大商品 ID + 1（删除最大行后复用该 ID，不跳号）。"""
    category_id = make_category(admin_headers)
    first = make_product(admin_headers, category_id, unique_name()).json()
    second = make_product(admin_headers, category_id, unique_name()).json()
    assert second["id"] == first["id"] + 1

    # 删除最大 ID 的商品后，再创建应复用"最大 ID + 1"（即刚删除的 ID）
    assert (
        client.delete(f"/api/products/{second['id']}", headers=admin_headers).status_code
        == 204
    )
    third = make_product(admin_headers, category_id, unique_name()).json()
    assert third["id"] == second["id"]


def test_create_product_with_invalid_category(admin_headers):
    response = client.post(
        "/api/products",
        json={"name": unique_name(), "category_id": 999999, "price": 10, "stock": 1},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "分类不存在"


def test_public_list_only_on_sale(admin_headers):
    category_id = make_category(admin_headers)
    on_name = unique_name()
    off_name = unique_name()
    make_product(admin_headers, category_id, on_name)
    make_product(admin_headers, category_id, off_name, is_on_sale=False)

    public = client.get("/api/products", params={"keyword": "test商品"}).json()
    names = [item["name"] for item in public["items"]]
    assert on_name in names
    assert off_name not in names


def test_include_off_sale_requires_admin(admin_headers, normal_user_headers):
    response = client.get("/api/products", params={"include_off_sale": True}, headers=normal_user_headers)
    assert response.status_code == 403
    response = client.get("/api/products", params={"include_off_sale": True}, headers=admin_headers)
    assert response.status_code == 200


def test_search_keyword(admin_headers):
    category_id = make_category(admin_headers)
    name = unique_name("test龙井")
    make_product(admin_headers, category_id, name)
    matched = client.get("/api/products", params={"keyword": "龙井"}).json()
    assert any(item["name"] == name for item in matched["items"])
    unmatched = client.get("/api/products", params={"keyword": "不存在的关键词"}).json()
    assert all(item["name"] != name for item in unmatched["items"])


def test_filter_by_category(admin_headers):
    category_a = make_category(admin_headers)
    category_b = make_category(admin_headers)
    name_a = unique_name("test分类甲")
    name_b = unique_name("test分类乙")
    make_product(admin_headers, category_a, name_a)
    make_product(admin_headers, category_b, name_b)
    result = client.get("/api/products", params={"category_id": category_a}).json()
    names = [item["name"] for item in result["items"]]
    assert name_a in names
    assert name_b not in names


def test_search_keyword_plus_category(admin_headers):
    """关键词与分类组合过滤：命中词但不在该分类下的商品不应返回。"""
    category_a = make_category(admin_headers)
    category_b = make_category(admin_headers)
    keyword = f"龙井{ uuid4().hex[:4] }"
    name_a = f"test{keyword}甲"
    name_b = f"test{keyword}乙"
    make_product(admin_headers, category_a, name_a)
    make_product(admin_headers, category_b, name_b)
    result = client.get(
        "/api/products", params={"keyword": keyword, "category_id": category_a}
    ).json()
    names = [item["name"] for item in result["items"]]
    assert name_a in names
    assert name_b not in names


def test_search_off_sale_requires_admin(admin_headers):
    """下架商品按关键词搜索：公开不可见，管理员 include_off_sale=true 可见。"""
    category_id = make_category(admin_headers)
    keyword = f"下架茶{ uuid4().hex[:4] }"
    name = f"test{keyword}"
    make_product(admin_headers, category_id, name, is_on_sale=False)

    public = client.get("/api/products", params={"keyword": keyword}).json()
    assert all(item["name"] != name for item in public["items"])
    admin = client.get(
        "/api/products",
        params={"keyword": keyword, "include_off_sale": True},
        headers=admin_headers,
    ).json()
    assert any(item["name"] == name for item in admin["items"])


def test_search_category_plus_off_sale(admin_headers):
    """分类与下架组合：管理员能看到该分类下的下架商品，公开看不到。"""
    category_a = make_category(admin_headers)
    category_b = make_category(admin_headers)
    name_a_off = f"test分类下架{uuid4().hex[:4]}"
    name_b_off = f"test分类下架{uuid4().hex[:4]}"
    make_product(admin_headers, category_a, name_a_off, is_on_sale=False)
    make_product(admin_headers, category_b, name_b_off, is_on_sale=False)

    public = client.get("/api/products", params={"category_id": category_a}).json()
    assert all(item["name"] != name_a_off for item in public["items"])
    admin = client.get(
        "/api/products",
        params={"category_id": category_a, "include_off_sale": True},
        headers=admin_headers,
    ).json()
    assert any(item["name"] == name_a_off for item in admin["items"])
    assert all(item["name"] != name_b_off for item in admin["items"])


def test_pagination(admin_headers):
    category_id = make_category(admin_headers)
    for _ in range(3):
        make_product(admin_headers, category_id, unique_name())
    page1 = client.get("/api/products", params={"page": 1, "page_size": 2}).json()
    page2 = client.get("/api/products", params={"page": 2, "page_size": 2}).json()
    assert page1["total"] >= 3
    assert len(page1["items"]) == 2
    assert len(page2["items"]) >= 1


def test_detail_public_and_not_found(admin_headers):
    category_id = make_category(admin_headers)
    name = unique_name()
    product_id = make_product(admin_headers, category_id, name).json()["id"]
    detail = client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == name
    assert client.get("/api/products/999999").status_code == 404


def test_off_sale_detail_hidden_for_public(admin_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, unique_name(), is_on_sale=False).json()["id"]
    assert client.get(f"/api/products/{product_id}").status_code == 404
    assert client.get(f"/api/products/{product_id}", headers=admin_headers).status_code == 200


def test_update_product(admin_headers):
    category_id = make_category(admin_headers)
    name = unique_name()
    product_id = make_product(admin_headers, category_id, name).json()["id"]
    response = client.put(
        f"/api/products/{product_id}",
        json={"stock": 999},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["stock"] == 999
    # 缓存已失效：重新查询应看到新库存
    listed = client.get("/api/products", params={"keyword": name}).json()
    assert listed["items"][0]["stock"] == 999


def test_delete_product(admin_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, unique_name()).json()["id"]
    response = client.delete(f"/api/products/{product_id}", headers=admin_headers)
    assert response.status_code == 204
    assert client.get(f"/api/products/{product_id}").status_code == 404


def test_upload_image_requires_admin(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, unique_name()).json()["id"]
    files = {"file": ("tea.png", b"fake-image-content", "image/png")}
    assert client.post(f"/api/products/{product_id}/image", files=files).status_code == 401
    response = client.post(
        f"/api/products/{product_id}/image", files=files, headers=normal_user_headers
    )
    assert response.status_code == 403


def test_upload_image_success(admin_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, unique_name()).json()["id"]
    response = client.post(
        f"/api/products/{product_id}/image",
        files={"file": ("tea.png", b"fake-image-content", "image/png")},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["image_url"].startswith("/uploads/")


def test_upload_non_image_rejected(admin_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, unique_name()).json()["id"]
    response = client.post(
        f"/api/products/{product_id}/image",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=admin_headers,
    )
    assert response.status_code == 400


def test_upload_image_too_large_rejected(admin_headers):
    category_id = make_category(admin_headers)
    product_id = make_product(admin_headers, category_id, unique_name()).json()["id"]
    before = {p.name for p in UPLOAD_DIR.glob("*")}
    files = {"file": ("big.png", b"x" * (10 * 1024 * 1024 + 1), "image/png")}
    response = client.post(
        f"/api/products/{product_id}/image",
        files=files,
        headers=admin_headers,
    )
    assert response.status_code == 413
    after = {p.name for p in UPLOAD_DIR.glob("*")}
    assert after - before == set()
