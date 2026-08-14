"""V2.0-2.6 数据库约束强制生效回归测试（绕过应用层，直接验证 MySQL CHECK）。"""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.database import engine
from tests.conftest import client


def test_negative_stock_rejected_by_database(admin_headers):
    category = client.post(
        "/api/categories",
        json={"name": f"testck{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    ).json()
    with engine.begin() as conn:
        with pytest.raises(DBAPIError):
            conn.execute(
                text(
                    "INSERT INTO products "
                    "(name, category_id, price, stock, description, image_url, is_on_sale, created_at, updated_at) "
                    "VALUES (:name, :cid, 1, -1, '', '', 1, NOW(), NOW())"
                ),
                {"name": "testck_neg", "cid": category["id"]},
            )


def test_zero_cart_quantity_rejected_by_database(admin_headers, normal_user_headers):
    category = client.post(
        "/api/categories",
        json={"name": f"testck{uuid4().hex[:6]}", "sort_order": 0},
        headers=admin_headers,
    ).json()
    product = client.post(
        "/api/products",
        json={
            "name": f"testckprod{uuid4().hex[:6]}",
            "category_id": category["id"],
            "price": 10,
            "stock": 5,
        },
        headers=admin_headers,
    ).json()
    user_id = client.get("/api/auth/me", headers=normal_user_headers).json()["id"]
    sku_id = product["skus"][0]["id"]
    with engine.begin() as conn:
        with pytest.raises(DBAPIError):
            conn.execute(
                text(
                    "INSERT INTO cart_items (user_id, product_id, sku_id, quantity, created_at, updated_at) "
                    "VALUES (:uid, :pid, :sku_id, 0, NOW(), NOW())"
                ),
                {"uid": user_id, "pid": product["id"], "sku_id": sku_id},
            )
