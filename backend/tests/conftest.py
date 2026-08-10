"""pytest 公共配置：建表、测试管理员、缓存清理、测试数据清理。"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Category, Product, User  # noqa: F401  注册全部模型
from app.services import cache

client = TestClient(app)

TEST_ADMIN_USERNAME = "testadmin"
TEST_ADMIN_PASSWORD = "adminpass123"


def create_test_admin() -> None:
    with SessionLocal() as db:
        exists = db.scalar(select(User).where(User.username == TEST_ADMIN_USERNAME))
        if exists is None:
            db.add(
                User(
                    username=TEST_ADMIN_USERNAME,
                    password_hash=hash_password(TEST_ADMIN_PASSWORD),
                    nickname="测试管理员",
                    role="admin",
                )
            )
            db.commit()


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    Base.metadata.create_all(bind=engine)
    create_test_admin()
    yield
    with SessionLocal() as db:
        # 只清理测试创建的数据（名称以 test 开头），不影响种子数据
        db.execute(delete(Product).where(Product.name.like("test%")))
        db.execute(delete(Category).where(Category.name.like("test%")))
        db.execute(delete(User).where(User.username.like("test%")))
        db.commit()


@pytest.fixture(autouse=True)
def clear_cache():
    """每个测试前清空 Redis 缓存，保证用例之间互不影响。"""
    cache.clear_all()
    yield


@pytest.fixture()
def admin_headers() -> dict:
    response = client.post(
        "/api/auth/login",
        json={"username": TEST_ADMIN_USERNAME, "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture()
def normal_user_headers() -> dict:
    username = f"testuser{uuid4().hex[:8]}"
    client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "普通用户"},
    )
    response = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    return {"Authorization": f"Bearer {response.json()['token']}"}
