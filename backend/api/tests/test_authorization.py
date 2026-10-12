import httpx

from app.modules.identity.domain import RoleName
from tests.conftest import RECORD_IDS


async def test_operations_cannot_access_procurement_or_admin(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    headers = auth_headers[RoleName.OPERATIONS]
    procurement = await client.get("/api/v1/procurement/purchase-requests", headers=headers)
    errors = await client.get("/api/v1/admin/errors", headers=headers)

    assert procurement.status_code == 403
    assert errors.status_code == 403


async def test_procurement_and_creative_only_receive_scoped_records(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    procurement = await client.get(
        "/api/v1/procurement/purchase-requests",
        headers=auth_headers[RoleName.PROCUREMENT],
    )
    creative = await client.get(
        "/api/v1/creative/content-tasks",
        headers=auth_headers[RoleName.CREATIVE],
    )

    assert procurement.status_code == 200
    assert [item["record_id"] for item in procurement.json()["items"]] == [
        str(RECORD_IDS["procurement_allowed"])
    ]
    assert creative.status_code == 200
    assert [item["record_id"] for item in creative.json()["items"]] == [
        str(RECORD_IDS["creative_allowed"])
    ]


async def test_object_id_change_does_not_bypass_scope(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    response = await client.get(
        f"/api/v1/operations/projects/{RECORD_IDS['operations_denied']}",
        headers=auth_headers[RoleName.OPERATIONS],
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


async def test_admin_can_read_all_role_modules(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    headers = auth_headers[RoleName.ADMIN]
    for path in (
        "/api/v1/operations/projects",
        "/api/v1/procurement/purchase-requests",
        "/api/v1/creative/content-tasks",
    ):
        response = await client.get(path, headers=headers)
        assert response.status_code == 200
        assert response.json()["total"] == 2
