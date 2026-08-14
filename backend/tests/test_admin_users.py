"""V2.0-3.4 管理端用户管理（RBAC）测试。"""

from uuid import uuid4

from tests.conftest import client


def unique_username() -> str:
    return f"testadm{uuid4().hex[:8]}"


def register_and_login() -> tuple[str, dict]:
    username = unique_username()
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123", "nickname": "RBAC 测试"},
    )
    assert response.status_code == 201
    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login.status_code == 200
    return username, {"Authorization": f"Bearer {login.json()['token']}"}


def _login_as_admin() -> dict:
    """独立登录获取管理员的 Authorization 头（避免依赖 fixture 参数）。"""
    response = client.post(
        "/api/auth/login", json={"username": "testadmin", "password": "adminpass123"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def admin_id() -> int:
    data = client.get(
        "/api/admin/users?keyword=testadmin", headers=_login_as_admin()
    ).json()
    return data["items"][0]["id"]


def test_admin_users_requires_admin(normal_user_headers):
    assert client.get("/api/admin/users").status_code == 401
    assert client.get("/api/admin/users", headers=normal_user_headers).status_code == 403


def test_admin_list_users_paginated_and_keyword(admin_headers):
    response = client.get("/api/admin/users", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"items", "total", "page", "page_size"}
    assert body["total"] >= 1

    username, _ = register_and_login()
    filtered = client.get(
        f"/api/admin/users?keyword={username}", headers=admin_headers
    ).json()
    assert filtered["total"] == 1
    assert filtered["items"][0]["username"] == username


def test_admin_update_role_and_effective(admin_headers):
    username, _ = register_and_login()
    uid = client.get(
        f"/api/admin/users?keyword={username}", headers=admin_headers
    ).json()["items"][0]["id"]

    promoted = client.patch(
        f"/api/admin/users/{uid}/role", json={"role": "admin"}, headers=admin_headers
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "admin"

    # 重新登录后角色生效，可访问管理接口
    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    ).json()
    assert (
        client.get(
            "/api/admin/orders", headers={"Authorization": f"Bearer {login['token']}"}
        ).status_code
        == 200
    )

    demoted = client.patch(
        f"/api/admin/users/{uid}/role", json={"role": "user"}, headers=admin_headers
    )
    assert demoted.status_code == 200
    assert demoted.json()["role"] == "user"


def test_admin_cannot_operate_self(admin_headers):
    me = admin_id()
    role_resp = client.patch(
        f"/api/admin/users/{me}/role", json={"role": "user"}, headers=admin_headers
    )
    assert role_resp.status_code == 400
    assert role_resp.json()["code"] == "SELF_OPERATION_FORBIDDEN"

    status_resp = client.patch(
        f"/api/admin/users/{me}/status",
        json={"status": "disabled"},
        headers=admin_headers,
    )
    assert status_resp.status_code == 400
    assert status_resp.json()["code"] == "SELF_OPERATION_FORBIDDEN"


def test_admin_disable_invalidates_tokens_and_enable_recovers(admin_headers):
    username, headers = register_and_login()
    uid = client.get(
        f"/api/admin/users?keyword={username}", headers=admin_headers
    ).json()["items"][0]["id"]

    disabled = client.patch(
        f"/api/admin/users/{uid}/status",
        json={"status": "disabled"},
        headers=admin_headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"
    # 旧 token 立即失效
    assert client.get("/api/auth/me", headers=headers).status_code == 401

    enabled = client.patch(
        f"/api/admin/users/{uid}/status",
        json={"status": "active"},
        headers=admin_headers,
    )
    assert enabled.status_code == 200
    assert enabled.json()["status"] == "active"
    # 重新登录正常
    login = client.post(
        "/api/auth/login", json={"username": username, "password": "password123"}
    )
    assert login.status_code == 200


def test_invalid_status_role_values_rejected(admin_headers):
    assert (
        client.patch(
            "/api/admin/users/1/status",
            json={"status": "banned"},
            headers=admin_headers,
        ).status_code
        == 422
    )
    assert (
        client.patch(
            "/api/admin/users/1/role",
            json={"role": "super"},
            headers=admin_headers,
        ).status_code
        == 422
    )


def test_admin_user_not_found(admin_headers):
    response = client.patch(
        "/api/admin/users/999999/status",
        json={"status": "disabled"},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


def test_root_cannot_be_demoted_or_disabled_by_other_admin(admin_headers):
    """主账号（conftest 的 testadmin）不可被其他管理员降级/禁用。"""
    root_id = admin_id()

    other, _ = register_and_login()
    other_id = client.get(
        f"/api/admin/users?keyword={other}", headers=admin_headers
    ).json()["items"][0]["id"]
    client.patch(
        f"/api/admin/users/{other_id}/role",
        json={"role": "admin"},
        headers=admin_headers,
    )
    other_login = client.post(
        "/api/auth/login", json={"username": other, "password": "password123"}
    ).json()
    other_admin_headers = {"Authorization": f"Bearer {other_login['token']}"}

    role_resp = client.patch(
        f"/api/admin/users/{root_id}/role",
        json={"role": "user"},
        headers=other_admin_headers,
    )
    assert role_resp.status_code == 400
    assert role_resp.json()["code"] == "ROOT_PROTECTED"

    status_resp = client.patch(
        f"/api/admin/users/{root_id}/status",
        json={"status": "disabled"},
        headers=other_admin_headers,
    )
    assert status_resp.status_code == 400
    assert status_resp.json()["code"] == "ROOT_PROTECTED"


def test_promoted_admin_can_manage_other_promoted_admin(admin_headers):
    """非主账号管理员之间仍可互相管理角色（主账号保护不误伤）。"""
    user_b, _ = register_and_login()
    user_c, _ = register_and_login()
    bid = client.get(
        f"/api/admin/users?keyword={user_b}", headers=admin_headers
    ).json()["items"][0]["id"]
    cid = client.get(
        f"/api/admin/users?keyword={user_c}", headers=admin_headers
    ).json()["items"][0]["id"]
    client.patch(f"/api/admin/users/{bid}/role", json={"role": "admin"}, headers=admin_headers)
    client.patch(f"/api/admin/users/{cid}/role", json={"role": "admin"}, headers=admin_headers)

    b_login = client.post(
        "/api/auth/login", json={"username": user_b, "password": "password123"}
    ).json()
    b_headers = {"Authorization": f"Bearer {b_login['token']}"}
    resp = client.patch(
        f"/api/admin/users/{cid}/role", json={"role": "user"}, headers=b_headers
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "user"
