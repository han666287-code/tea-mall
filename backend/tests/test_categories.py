"""分类接口测试：公开查询、权限、增删改、缓存失效。"""

from uuid import uuid4

from tests.conftest import client


def unique_category_name() -> str:
    return f"test分类{uuid4().hex[:6]}"


def create_category(admin_headers: dict, name: str, sort_order: int = 0):
    return client.post(
        "/api/categories",
        json={"name": name, "sort_order": sort_order},
        headers=admin_headers,
    )


def test_public_list_categories():
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_category_requires_login():
    response = client.post(
        "/api/categories", json={"name": unique_category_name(), "sort_order": 0}
    )
    assert response.status_code == 401


def test_create_category_forbidden_for_normal_user(normal_user_headers):
    response = create_category(normal_user_headers, unique_category_name())
    assert response.status_code == 403


def test_create_and_update_category(admin_headers):
    name = unique_category_name()
    response = create_category(admin_headers, name)
    assert response.status_code == 201
    category_id = response.json()["id"]

    duplicate = create_category(admin_headers, name)
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "分类名称已存在"

    updated = client.put(
        f"/api/categories/{category_id}",
        json={"name": f"{name}改"},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == f"{name}改"


def test_delete_category_with_products_rejected(admin_headers):
    category_name = unique_category_name()
    category_id = create_category(admin_headers, category_name).json()["id"]
    client.post(
        "/api/products",
        json={
            "name": f"test商品{uuid4().hex[:6]}",
            "category_id": category_id,
            "price": 10,
            "stock": 5,
        },
        headers=admin_headers,
    )
    response = client.delete(f"/api/categories/{category_id}", headers=admin_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "该分类下存在商品，无法删除"


def test_delete_category_without_products(admin_headers):
    category_id = create_category(admin_headers, unique_category_name()).json()["id"]
    response = client.delete(f"/api/categories/{category_id}", headers=admin_headers)
    assert response.status_code == 204
    assert client.get(f"/api/categories").json() is not None


def test_category_cache_invalidated_after_create(admin_headers):
    before = client.get("/api/categories").json()
    create_category(admin_headers, unique_category_name())
    after = client.get("/api/categories").json()
    assert len(after) == len(before) + 1
