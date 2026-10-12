import json

import httpx

from app.modules.audit.repository import InMemoryAuditRepository
from app.modules.identity.domain import RoleName
from app.modules.identity.repository import InMemoryIdentityRepository
from tests.conftest import USER_IDS

NEW_PASSWORD = "new-user-valid-password"


async def test_admin_can_create_disable_and_enable_user(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
    identity_repository: InMemoryIdentityRepository,
    audit_repository: InMemoryAuditRepository,
) -> None:
    response = await client.post(
        "/api/v1/admin/users",
        headers=auth_headers[RoleName.ADMIN],
        json={
            "username": "new_operator",
            "display_name": "New Operator",
            "initial_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["roles"] == []
    assert created["modules"] == []
    assert created["direct_permissions"] == []
    assert created["effective_permissions"] == []
    assert created["scopes"] == {
        "organization_ids": [],
        "team_ids": [],
        "store_ids": [],
    }
    serialized = json.dumps(created)
    assert NEW_PASSWORD not in serialized
    assert "password_hash" not in serialized
    assert "token" not in serialized.lower()

    stored = await identity_repository.get_by_username("new_operator")
    assert stored is not None
    assert stored.password_hash != NEW_PASSWORD
    assert stored.password_hash.startswith("$argon2")

    duplicate = await client.post(
        "/api/v1/admin/users",
        headers=auth_headers[RoleName.ADMIN],
        json={
            "username": "new_operator",
            "display_name": "Duplicate",
            "initial_password": NEW_PASSWORD,
        },
    )
    assert duplicate.status_code == 409

    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "new_operator", "password": NEW_PASSWORD},
    )
    assert login.status_code == 200
    session = login.cookies.get("ai_ops_session")
    assert session is not None
    new_user_headers = {"Cookie": f"ai_ops_session={session}"}
    denied = await client.get("/api/v1/dashboard/summary", headers=new_user_headers)
    assert denied.status_code == 403

    disabled = await client.post(
        f"/api/v1/admin/users/{created['user_id']}/disable",
        headers=auth_headers[RoleName.ADMIN],
    )
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False
    assert (await client.get("/api/v1/me", headers=new_user_headers)).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"username": "new_operator", "password": NEW_PASSWORD},
        )
    ).status_code == 401

    enabled = await client.post(
        f"/api/v1/admin/users/{created['user_id']}/enable",
        headers=auth_headers[RoleName.ADMIN],
    )
    assert enabled.status_code == 200
    assert enabled.json()["is_active"] is True
    assert enabled.json()["roles"] == []
    assert enabled.json()["modules"] == []
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"username": "new_operator", "password": NEW_PASSWORD},
        )
    ).status_code == 200

    lifecycle_events = [
        event
        for event in audit_repository.events
        if event.action
        in {"identity.user.create", "identity.user.disable", "identity.user.enable"}
    ]
    assert {event.action for event in lifecycle_events} == {
        "identity.user.create",
        "identity.user.disable",
        "identity.user.enable",
    }
    audit_text = json.dumps(
        [event.model_dump(mode="json") for event in lifecycle_events]
    )
    assert NEW_PASSWORD not in audit_text
    assert "password_hash" not in audit_text


async def test_non_admin_cannot_manage_users_and_last_admin_cannot_be_disabled(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    denied = await client.post(
        "/api/v1/admin/users",
        headers=auth_headers[RoleName.OPERATIONS],
        json={
            "username": "forbidden_user",
            "display_name": "Forbidden",
            "initial_password": NEW_PASSWORD,
        },
    )
    assert denied.status_code == 403

    last_admin = await client.post(
        f"/api/v1/admin/users/{USER_IDS[RoleName.ADMIN]}/disable",
        headers=auth_headers[RoleName.ADMIN],
    )
    assert last_admin.status_code == 409
    assert last_admin.json()["error"]["code"] == "LAST_ACTIVE_ADMIN"


async def test_created_user_validation_rejects_short_password(
    client: httpx.AsyncClient,
    auth_headers: dict[RoleName, dict[str, str]],
) -> None:
    response = await client.post(
        "/api/v1/admin/users",
        headers=auth_headers[RoleName.ADMIN],
        json={
            "username": "short_password",
            "display_name": "Short Password",
            "initial_password": "too-short",
        },
    )
    assert response.status_code == 422
    assert "too-short" not in response.text
