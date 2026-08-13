"""V2.0-1.6 破坏性测试操作环境保护回归测试。"""

import pytest

from app.config import ensure_testing_environment, settings
from app.services import cache


def test_clear_all_refused_when_not_testing(monkeypatch):
    monkeypatch.setattr(settings, "testing", False)
    with pytest.raises(RuntimeError):
        cache.clear_all()


def test_ensure_testing_rejects_dev_database(monkeypatch):
    monkeypatch.setattr(settings, "testing", True)
    monkeypatch.setattr(
        settings,
        "database_url",
        "mysql+pymysql://tea_mall:tea_mall_dev@localhost:3306/tea_mall?charset=utf8mb4",
    )
    with pytest.raises(RuntimeError):
        ensure_testing_environment()


def test_ensure_testing_rejects_dev_redis(monkeypatch):
    monkeypatch.setattr(settings, "testing", True)
    monkeypatch.setattr(
        settings,
        "database_url",
        "mysql+pymysql://tea_mall:tea_mall_dev@localhost:3306/tea_mall_test?charset=utf8mb4",
    )
    monkeypatch.setattr(settings, "redis_url", "redis://localhost:6379/0")
    with pytest.raises(RuntimeError):
        ensure_testing_environment()
