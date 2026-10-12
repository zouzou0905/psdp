import httpx

from app.modules.audit.repository import InMemoryAuditRepository
from app.modules.identity.domain import RoleName
from tests.conftest import PASSWORD, RECORD_IDS, USER_IDS


async def _login(client: httpx.AsyncClient, role: RoleName) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": f"{role.value}_demo", "password": PASSWORD},
    )
    assert response.status_code == 200
    session_cookie = response.cookies.get("ai_ops_session")
    assert session_cookie is not None
    return {"Cookie": f"ai_ops_session={session_cookie}"}


async def test_login_rejects_client_selected_role_and_returns_access_context(
    client: httpx.AsyncClient,
) -> None:
    rejected = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "operations_demo",
            "password": PASSWORD,
            "role": "admin",
        },
    )
    assert rejected.status_code == 422

    accepted = await client.post(
        "/api/v1/auth/login",
        json={"username": "operations_demo", "password": PASSWORD},
    )
    context = accepted.json()
    assert context["roles"] == ["operations"]
    assert context["modules"] == ["operations"]
    assert context["scopes"]["store_ids"] == ["store_operations"]
    assert context["default_landing"] == "/operations"
    set_cookie = accepted.headers["set-cookie"]
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "access_token" not in accepted.text


async def test_me_access_context_modules_and_stores_are_server_derived(
    client: httpx.AsyncClient, auth_headers: dict[RoleName, dict[str, str]]
) -> None:
    headers = auth_headers[RoleName.OPERATIONS]
    context = await client.get("/api/v1/me/access-context", headers=headers)
    modules = await client.get("/api/v1/me/modules", headers=headers)
    stores = await client.get("/api/v1/me/stores", headers=headers)

    assert context.status_code == modules.status_code == stores.status_code == 200
    assert modules.json() == {
        "modules": ["operations"],
        "default_landing": "/operations",
    }
    assert [item["store_id"] for item in stores.json()["items"]] == ["store_operations"]
    assert "credential_ref" not in stores.text


async def test_operations_store_scope_cannot_be_bypassed_by_object_id(
    client: httpx.AsyncClient, auth_headers: dict[RoleName, dict[str, str]]
) -> None:
    headers = auth_headers[RoleName.OPERATIONS]
    listed = await client.get("/api/v1/operations/projects", headers=headers)
    denied = await client.get(
        f"/api/v1/operations/projects/{RECORD_IDS['operations_denied']}",
        headers=headers,
    )

    assert [item["store_id"] for item in listed.json()["items"]] == ["store_operations"]
    assert denied.status_code == 404


async def test_ordinary_user_cannot_modify_access(
    client: httpx.AsyncClient, auth_headers: dict[RoleName, dict[str, str]]
) -> None:
    response = await client.put(
        f"/api/v1/admin/users/{USER_IDS[RoleName.OPERATIONS]}/modules",
        headers=auth_headers[RoleName.OPERATIONS],
        json={"modules": ["admin"], "expected_authorization_revision": 1},
    )
    assert response.status_code == 403


async def test_stale_authorization_revision_returns_409(
    client: httpx.AsyncClient, auth_headers: dict[RoleName, dict[str, str]]
) -> None:
    user_id = USER_IDS[RoleName.OPERATIONS]
    payload = {
        "modules": ["operations"],
        "expected_authorization_revision": 1,
    }
    first = await client.put(
        f"/api/v1/admin/users/{user_id}/modules",
        headers=auth_headers[RoleName.ADMIN],
        json=payload,
    )
    stale = await client.put(
        f"/api/v1/admin/users/{user_id}/modules",
        headers=auth_headers[RoleName.ADMIN],
        json=payload,
    )

    assert first.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "AUTHORIZATION_REVISION_CONFLICT"


async def test_admin_assigns_modules_and_stores_and_old_session_expires(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
    audit_repository: InMemoryAuditRepository,
) -> None:
    user_id = USER_IDS[RoleName.OPERATIONS]
    old_headers = auth_headers[RoleName.OPERATIONS]
    admin_headers = auth_headers[RoleName.ADMIN]

    module_update = await client.put(
        f"/api/v1/admin/users/{user_id}/modules",
        headers=admin_headers,
        json={
            "modules": [],
            "expected_authorization_revision": 1,
        },
    )
    assert module_update.status_code == 200
    assert module_update.json()["authorization_revision"] == 2
    assert (
        await client.get("/api/v1/operations/dashboard", headers=old_headers)
    ).status_code == 401

    module_assignment = await client.put(
        f"/api/v1/admin/users/{user_id}/modules",
        headers=admin_headers,
        json={
            "modules": ["operations", "creative"],
            "expected_authorization_revision": 2,
        },
    )
    assert module_assignment.status_code == 200
    assert set(module_assignment.json()["modules"]) == {"operations", "creative"}

    store_update = await client.put(
        f"/api/v1/admin/users/{user_id}/store-scopes",
        headers=admin_headers,
        json={
            "store_ids": ["store_operations", "store_other"],
            "expected_authorization_revision": 3,
        },
    )
    assert store_update.status_code == 200
    assert set(store_update.json()["scopes"]["store_ids"]) == {
        "store_operations",
        "store_other",
    }

    role_update = await client.put(
        f"/api/v1/admin/users/{user_id}/roles",
        headers=admin_headers,
        json={
            "roles": ["operations"],
            "permissions": ["creative.dashboard.read"],
            "expected_authorization_revision": 4,
        },
    )
    assert role_update.status_code == 200
    assert role_update.json()["direct_permissions"] == ["creative.dashboard.read"]

    new_headers = await _login(client, RoleName.OPERATIONS)
    assert (
        await client.get("/api/v1/operations/dashboard", headers=new_headers)
    ).status_code == 200
    assert (await client.get("/api/v1/creative/dashboard", headers=new_headers)).status_code == 200

    events = await audit_repository.list_recent()
    changes = [event for event in events if event.action.startswith("identity.user.")]
    assert {event.action for event in changes} == {
        "identity.user.modules.update",
        "identity.user.roles_permissions.update",
        "identity.user.store_scopes.update",
    }
    assert all("before" in event.metadata_summary for event in changes)
    assert all("after" in event.metadata_summary for event in changes)


async def test_admin_store_management_never_exposes_credentials(
    client: httpx.AsyncClient, auth_headers: dict[RoleName, dict[str, str]]
) -> None:
    headers = auth_headers[RoleName.ADMIN]
    created = await client.post(
        "/api/v1/admin/stores",
        headers=headers,
        json={
            "store_id": "store_new_demo",
            "display_name": "New Demo Store",
            "marketplace": "demo",
            "organization_id": "org_1",
        },
    )
    assert created.status_code == 201
    assert created.json()["credential_configured"] is False
    assert "credential_ref" not in created.text

    updated = await client.patch(
        "/api/v1/admin/stores/store_new_demo",
        headers=headers,
        json={"display_name": "Renamed Demo Store", "expected_revision": 1},
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
