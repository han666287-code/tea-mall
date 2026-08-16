"""V2.0-4.1 SKU/规格体系接口测试。"""

from uuid import uuid4

from tests.conftest import client


def unique_name(prefix: str = "testSKU") -> str:
    return f"{prefix}{uuid4().hex[:6]}"


def make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": f"test分类{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    )
    return response.json()["id"]


def sku_payload(
    sku_code: str,
    price: float,
    stock: int,
    value: str,
    is_active: bool = True,
    spec_name: str = "净含量",
):
    return {
        "sku_code": sku_code,
        "price": price,
        "stock": stock,
        "is_active": is_active,
        "specs": [{"name": spec_name, "value": value}],
    }


def make_product_with_skus(
    admin_headers: dict, category_id: int, skus: list[dict], is_on_sale: bool = True
) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": unique_name(),
            "category_id": category_id,
            "price": 0,
            "stock": 0,
            "description": "SKU 测试商品",
            "is_on_sale": is_on_sale,
            "skus": skus,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_product_with_skus(admin_headers):
    category_id = make_category(admin_headers)
    skus = [
        sku_payload("T100", 88.00, 10, "100g"),
        sku_payload("T200", 158.00, 20, "200g"),
    ]
    product = make_product_with_skus(admin_headers, category_id, skus)
    assert len(product["skus"]) == 2
    prices = {s["price"] for s in product["skus"]}
    assert prices == {"88.00", "158.00"}
    # 商品级为汇总：最低价 + 启用 SKU 库存之和
    assert product["price"] == "88.00"
    assert product["stock"] == 30
    assert all(s["specs"] == [{"name": "净含量", "value": v}] for s, v in zip(product["skus"], ["100g", "200g"]))


def test_create_product_default_sku(admin_headers):
    category_id = make_category(admin_headers)
    response = client.post(
        "/api/products",
        json={
            "name": unique_name(),
            "category_id": category_id,
            "price": 66.5,
            "stock": 7,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["skus"]) == 1
    sku = data["skus"][0]
    assert sku["sku_code"].startswith("DEFAULT-")
    assert sku["price"] == "66.50"
    assert sku["stock"] == 7
    assert sku["is_active"] is True
    assert data["price"] == "66.50"
    assert data["stock"] == 7


def test_skus_in_list_and_detail(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product_with_skus(
        admin_headers, category_id, [sku_payload("A1", 10, 1, "100g"), sku_payload("A2", 20, 2, "200g")]
    )
    listed = client.get("/api/products", params={"keyword": product["name"]}).json()
    item = next(p for p in listed["items"] if p["id"] == product["id"])
    assert len(item["skus"]) == 2
    detail = client.get(f"/api/products/{product['id']}").json()
    assert len(detail["skus"]) == 2
    assert {s["sku_code"] for s in detail["skus"]} == {"A1", "A2"}


def test_duplicate_spec_combo_rejected(admin_headers):
    category_id = make_category(admin_headers)
    skus = [sku_payload("B1", 10, 1, "100g"), sku_payload("B2", 20, 1, "100g")]
    response = client.post(
        "/api/products",
        json={
            "name": unique_name(),
            "category_id": category_id,
            "price": 0,
            "stock": 0,
            "skus": skus,
        },
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "SKU_DUPLICATE_SPECS"


def test_inconsistent_spec_names_rejected(admin_headers):
    category_id = make_category(admin_headers)
    skus = [
        sku_payload("C1", 10, 1, "100g", spec_name="净含量"),
        sku_payload("C2", 20, 1, "礼盒装", spec_name="包装"),
    ]
    response = client.post(
        "/api/products",
        json={
            "name": unique_name(),
            "category_id": category_id,
            "price": 0,
            "stock": 0,
            "skus": skus,
        },
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "SKU_INVALID_SPECS"


def test_duplicate_spec_name_in_sku_rejected(admin_headers):
    category_id = make_category(admin_headers)
    skus = [
        {
            "sku_code": "D1",
            "price": 10,
            "stock": 1,
            "is_active": True,
            "specs": [
                {"name": "净含量", "value": "100g"},
                {"name": "净含量", "value": "200g"},
            ],
        }
    ]
    response = client.post(
        "/api/products",
        json={
            "name": unique_name(),
            "category_id": category_id,
            "price": 0,
            "stock": 0,
            "skus": skus,
        },
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "SKU_INVALID_SPECS"


def test_duplicate_sku_code_rejected(admin_headers):
    category_id = make_category(admin_headers)
    skus = [sku_payload("E1", 10, 1, "100g"), sku_payload("E1", 20, 1, "200g")]
    response = client.post(
        "/api/products",
        json={
            "name": unique_name(),
            "category_id": category_id,
            "price": 0,
            "stock": 0,
            "skus": skus,
        },
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "SKU_CODE_TAKEN"


def test_replace_skus_updates_summary(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product_with_skus(
        admin_headers, category_id, [sku_payload("F1", 10, 5, "100g"), sku_payload("F2", 20, 5, "200g")]
    )
    response = client.put(
        f"/api/products/{product['id']}/skus",
        json=[
            sku_payload("F3", 30, 3, "500g"),
            sku_payload("F4", 40, 7, "1000g"),
        ],
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert {s["sku_code"] for s in data["skus"]} == {"F3", "F4"}
    assert data["price"] == "30.00"
    assert data["stock"] == 10


def test_replace_skus_empty_rejected(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product_with_skus(admin_headers, category_id, [sku_payload("G1", 10, 1, "100g")])
    response = client.put(
        f"/api/products/{product['id']}/skus", json=[], headers=admin_headers
    )
    assert response.status_code == 400
    assert response.json()["code"] == "PRODUCT_NEEDS_SKU"


def test_replace_skus_with_cart_ref_rejected(admin_headers, normal_user_headers):
    """商品存在购物车引用时禁止整体替换 SKU，避免级联删除清空用户购物车。"""
    category_id = make_category(admin_headers)
    product = make_product_with_skus(
        admin_headers, category_id, [sku_payload("R1", 10, 5, "100g")]
    )
    sku_id = product["skus"][0]["id"]
    assert (
        client.post(
            "/api/cart/items",
            json={"sku_id": sku_id, "quantity": 1},
            headers=normal_user_headers,
        ).status_code
        == 201
    )
    response = client.put(
        f"/api/products/{product['id']}/skus",
        json=[sku_payload("R2", 20, 8, "200g")],
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "SKU_IN_USE_IN_CART"


def test_replace_skus_requires_admin(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product = make_product_with_skus(admin_headers, category_id, [sku_payload("H1", 10, 1, "100g")])
    payload = [sku_payload("H2", 20, 2, "200g")]
    assert client.put(
        f"/api/products/{product['id']}/skus", json=payload
    ).status_code == 401
    assert client.put(
        f"/api/products/{product['id']}/skus", json=payload, headers=normal_user_headers
    ).status_code == 403


def test_replace_skus_nonexistent_product(admin_headers):
    response = client.put(
        "/api/products/999999/skus",
        json=[sku_payload("I1", 10, 1, "100g")],
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "PRODUCT_NOT_FOUND"


def test_product_update_multi_sku_price_rejected(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product_with_skus(
        admin_headers, category_id, [sku_payload("J1", 10, 1, "100g"), sku_payload("J2", 20, 1, "200g")]
    )
    response = client.put(
        f"/api/products/{product['id']}", json={"price": 99}, headers=admin_headers
    )
    assert response.status_code == 400
    assert response.json()["code"] == "PRODUCT_HAS_SKUS"
    response = client.put(
        f"/api/products/{product['id']}", json={"stock": 99}, headers=admin_headers
    )
    assert response.status_code == 400
    assert response.json()["code"] == "PRODUCT_HAS_SKUS"


def test_product_update_single_sku_price_applies(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product_with_skus(admin_headers, category_id, [sku_payload("K1", 10, 1, "100g")])
    response = client.put(
        f"/api/products/{product['id']}", json={"price": 123.45, "stock": 9}, headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == "123.45"
    assert data["stock"] == 9
    assert data["skus"][0]["price"] == "123.45"
    assert data["skus"][0]["stock"] == 9


def test_update_product_with_skus_replaces(admin_headers):
    """管理页编辑商品并携带 skus 载荷（与前端保存路径一致）应整体替换 SKU。"""
    category_id = make_category(admin_headers)
    product = make_product_with_skus(
        admin_headers, category_id, [sku_payload("P1", 10, 5, "100g")]
    )
    response = client.put(
        f"/api/products/{product['id']}",
        json={
            "name": product["name"],
            "category_id": category_id,
            "description": "更新后的描述",
            "image_url": "",
            "is_on_sale": True,
            "skus": [
                sku_payload("P2", 88, 8, "500g"),
                sku_payload("P3", 128, 3, "1000g"),
            ],
        },
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert {s["sku_code"] for s in data["skus"]} == {"P2", "P3"}
    assert data["price"] == "88.00"
    assert data["stock"] == 11
    detail = client.get(f"/api/products/{product['id']}").json()
    assert len(detail["skus"]) == 2


def test_disable_sku_updates_summary(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product_with_skus(
        admin_headers, category_id, [sku_payload("L1", 10, 5, "100g"), sku_payload("L2", 20, 5, "200g")]
    )
    response = client.put(
        f"/api/products/{product['id']}/skus",
        json=[sku_payload("L1", 10, 5, "100g"), sku_payload("L2", 20, 5, "200g", is_active=False)],
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == "10.00"
    assert data["stock"] == 5


def test_multi_spec_product(admin_headers):
    category_id = make_category(admin_headers)
    skus = [
        {
            "sku_code": "M1",
            "price": 66,
            "stock": 3,
            "is_active": True,
            "specs": [
                {"name": "净含量", "value": "100g"},
                {"name": "包装", "value": "礼盒装"},
            ],
        },
        {
            "sku_code": "M2",
            "price": 77,
            "stock": 4,
            "is_active": True,
            "specs": [
                {"name": "净含量", "value": "200g"},
                {"name": "包装", "value": "罐装"},
            ],
        },
    ]
    product = make_product_with_skus(admin_headers, category_id, skus)
    assert len(product["skus"]) == 2
    for sku in product["skus"]:
        assert [item["name"] for item in sku["specs"]] == ["净含量", "包装"]


def test_cache_invalidated_after_sku_replace(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product_with_skus(admin_headers, category_id, [sku_payload("N1", 10, 1, "100g")])
    client.get(f"/api/products/{product['id']}")  # 预热缓存
    client.put(
        f"/api/products/{product['id']}/skus",
        json=[sku_payload("N2", 88, 8, "500g")],
        headers=admin_headers,
    )
    detail = client.get(f"/api/products/{product['id']}").json()
    assert [s["sku_code"] for s in detail["skus"]] == ["N2"]
    assert detail["price"] == "88.00"


def test_negative_sku_price_rejected(admin_headers):
    category_id = make_category(admin_headers)
    skus = [
        {
            "sku_code": "O1",
            "price": -1,
            "stock": 1,
            "is_active": True,
            "specs": [{"name": "净含量", "value": "100g"}],
        }
    ]
    response = client.post(
        "/api/products",
        json={
            "name": unique_name(),
            "category_id": category_id,
            "price": 0,
            "stock": 0,
            "skus": skus,
        },
        headers=admin_headers,
    )
    assert response.status_code == 422
