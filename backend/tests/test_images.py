"""V2.0-4.3 商品图片接口测试：主图、详情图多图、删除与权限。"""

from uuid import uuid4

from tests.conftest import client


def make_category(admin_headers: dict) -> int:
    response = client.post(
        "/api/categories",
        json={"name": f"test分类{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    )
    return response.json()["id"]


def make_product(admin_headers: dict, category_id: int) -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": f"test图片{uuid4().hex[:6]}",
            "category_id": category_id,
            "price": 10,
            "stock": 5,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_main_image_upload_creates_main_row(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id)
    response = client.post(
        f"/api/products/{product['id']}/image",
        files={"file": ("tea.png", b"fake-image", "image/png")},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"].startswith("/uploads/")
    mains = [img for img in data["images"] if img["kind"] == "main"]
    assert len(mains) == 1
    assert mains[0]["url"] == data["image_url"]


def test_main_image_upload_replaces_row(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id)
    client.post(
        f"/api/products/{product['id']}/image",
        files={"file": ("a.png", b"fake-image", "image/png")},
        headers=admin_headers,
    )
    response = client.post(
        f"/api/products/{product['id']}/image",
        files={"file": ("b.png", b"fake-image-2", "image/png")},
        headers=admin_headers,
    )
    data = response.json()
    mains = [img for img in data["images"] if img["kind"] == "main"]
    assert len(mains) == 1
    assert mains[0]["url"] == data["image_url"]


def test_detail_images_upload_append(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id)
    response = client.post(
        f"/api/products/{product['id']}/images",
        files=[
            ("files", ("d1.png", b"detail-1", "image/png")),
            ("files", ("d2.png", b"detail-2", "image/png")),
        ],
        headers=admin_headers,
    )
    assert response.status_code == 200
    details = [img for img in response.json()["images"] if img["kind"] == "detail"]
    assert len(details) == 2
    assert [img["sort_order"] for img in details] == [1, 2]


def test_remove_detail_image(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id)
    uploaded = client.post(
        f"/api/products/{product['id']}/images",
        files=[
            ("files", ("d1.png", b"detail-1", "image/png")),
            ("files", ("d2.png", b"detail-2", "image/png")),
        ],
        headers=admin_headers,
    ).json()
    target = next(img for img in uploaded["images"] if img["kind"] == "detail")
    response = client.request(
        "DELETE",
        f"/api/products/{product['id']}/images",
        json={"url": target["url"]},
        headers=admin_headers,
    )
    assert response.status_code == 200
    remaining = [img for img in response.json()["images"] if img["kind"] == "detail"]
    assert len(remaining) == 1
    assert target["url"] not in [img["url"] for img in remaining]


def test_remove_nonexistent_image_404(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id)
    response = client.request(
        "DELETE",
        f"/api/products/{product['id']}/images",
        json={"url": "/uploads/not-exist.png"},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "PRODUCT_IMAGE_NOT_FOUND"


def test_image_operations_require_admin(admin_headers, normal_user_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id)
    files = {"file": ("tea.png", b"fake-image", "image/png")}
    assert client.post(
        f"/api/products/{product['id']}/image", files=files
    ).status_code == 401
    assert client.post(
        f"/api/products/{product['id']}/image", files=files, headers=normal_user_headers
    ).status_code == 403
    multi = [("files", ("d1.png", b"x", "image/png"))]
    assert client.post(
        f"/api/products/{product['id']}/images", files=multi, headers=normal_user_headers
    ).status_code == 403
    assert client.request(
        "DELETE",
        f"/api/products/{product['id']}/images",
        json={"url": "/uploads/x.png"},
        headers=normal_user_headers,
    ).status_code == 403


def test_detail_upload_rejects_non_image(admin_headers):
    category_id = make_category(admin_headers)
    product = make_product(admin_headers, category_id)
    response = client.post(
        f"/api/products/{product['id']}/images",
        files=[("files", ("notes.txt", b"hello", "text/plain"))],
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "UNSUPPORTED_IMAGE_TYPE"
