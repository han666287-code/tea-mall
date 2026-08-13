"""V2.0-1.6 测试数据库隔离回归测试。"""

from app.config import settings
from app.database import engine


def test_settings_in_testing_mode():
    assert settings.testing is True


def test_database_url_points_to_test_db():
    assert "tea_mall_test" in settings.database_url
    assert "tea_mall_test" in str(engine.url)
