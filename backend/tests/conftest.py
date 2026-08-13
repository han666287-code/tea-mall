"""pytest 公共配置：测试环境隔离、建表、测试管理员、缓存与数据清理。"""

import os

# 必须在导入 app 模块之前设置测试环境标识与连接目标，
# 避免任何路径误连开发数据库 / 开发 Redis。
os.environ["TESTING"] = "1"
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = os.environ.get(
        "TEST_DATABASE_URL",
        "mysql+pymysql://tea_mall:tea_mall_dev@localhost:3306/tea_mall_test?charset=utf8mb4",
    )
if "REDIS_URL" not in os.environ:
    os.environ["REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.config import ensure_testing_environment
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine, get_db
from app.main import app
from app.models import (  # noqa: F401  注册全部模型
    CartItem,
    Category,
    Order,
    OrderItem,
    Product,
    User,
)
from app.services import cache


def _override_get_db():
    """显式将 FastAPI 的 DB 依赖覆盖为测试库会话（双保险防误连开发库）。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

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
    # 环境保护：非测试库 / 非测试 Redis 时拒绝建表与清理
    ensure_testing_environment()
    Base.metadata.create_all(bind=engine)
    create_test_admin()
    yield
    with SessionLocal() as db:
        # 只清理测试库中由测试创建的数据，不影响任何非测试数据
        db.execute(delete(OrderItem))
        db.execute(delete(Order))
        db.execute(delete(CartItem))
        db.execute(delete(Product).where(Product.name.like("test%")))
        db.execute(delete(Category).where(Category.name.like("test%")))
        db.execute(delete(User).where(User.username.like("test%")))
        db.commit()


@pytest.fixture(autouse=True)
def clear_cache():
    """每个测试前清空测试 Redis 缓存，保证用例之间互不影响。"""
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
