"""Phase 0 冒烟测试：应用可启动、根接口可访问。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tea Mall API"}
