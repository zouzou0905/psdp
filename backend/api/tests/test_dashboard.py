import httpx

from app.modules.identity.domain import RoleName


async def test_unauthenticated_business_request_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/dashboard/summary")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


async def test_each_role_receives_its_own_dashboard_shape(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    expected_fields = {
        RoleName.OPERATIONS: "projects",
        RoleName.PROCUREMENT: "purchase_requests",
        RoleName.CREATIVE: "content_tasks",
        RoleName.ADMIN: "readable_modules",
    }
    for role, field in expected_fields.items():
        response = await client.get("/api/v1/dashboard/summary", headers=auth_headers[role])
        assert response.status_code == 200
        body = response.json()
        assert body["workspace"] == role.value
        assert body["data_status"] == "demo"
        assert field in body


async def test_me_returns_roles_permissions_and_scope(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    response = await client.get("/api/v1/me", headers=auth_headers[RoleName.OPERATIONS])

    assert response.status_code == 200
    body = response.json()
    assert body["roles"] == ["operations"]
    assert "project.read_assigned" in body["permissions"]
    assert body["scopes"]["team_ids"] == ["team_operations"]


async def test_system_info(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/system/info")

    assert response.status_code == 200
    assert response.json()["environment"] == "test"
