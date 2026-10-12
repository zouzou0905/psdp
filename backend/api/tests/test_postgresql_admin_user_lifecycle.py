import os
from secrets import token_urlsafe
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import delete, select

from app.db.models import IdentityUser
from app.db.test_database import build_postgresql_test_settings
from app.main import create_app

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRESQL_INTEGRATION_TESTS") != "1",
    reason="Set RUN_POSTGRESQL_INTEGRATION_TESTS=1 to use the dedicated PostgreSQL test database",
)


async def _login(client: httpx.AsyncClient, username: str, password: str) -> httpx.Response:
    return await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


async def test_postgresql_user_lifecycle_persists_and_invalidates_session() -> None:
    settings = build_postgresql_test_settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.demo_admin_password is not None
    username = f"lifecycle_{uuid4().hex}"
    password = token_urlsafe(24)
    user_id: UUID | None = None
    applications = []

    try:
        first_app = create_app(settings)
        applications.append(first_app)
        first_transport = httpx.ASGITransport(app=first_app)
        async with (
            httpx.AsyncClient(transport=first_transport, base_url="http://test") as admin,
            httpx.AsyncClient(transport=first_transport, base_url="http://test") as user,
        ):
            admin_login = await _login(
                admin, "admin_demo", settings.demo_admin_password.get_secret_value()
            )
            admin_login.raise_for_status()
            created = await admin.post(
                "/api/v1/admin/users",
                json={
                    "username": username,
                    "display_name": "PostgreSQL Lifecycle Test",
                    "initial_password": password,
                },
            )
            created.raise_for_status()
            created_body = created.json()
            user_id = UUID(created_body["user_id"])
            assert created.status_code == 201
            assert created_body["roles"] == []
            assert created_body["modules"] == []
            assert created_body["effective_permissions"] == []
            assert created_body["scopes"]["store_ids"] == []
            assert password not in created.text
            assert "password_hash" not in created.text

            async with first_app.state.session_factory() as session:
                stored_hash = await session.scalar(
                    select(IdentityUser.password_hash).where(
                        IdentityUser.user_id == user_id
                    )
                )
            assert stored_hash is not None
            assert stored_hash != password
            assert stored_hash.startswith("$argon2")

            duplicate = await admin.post(
                "/api/v1/admin/users",
                json={
                    "username": username,
                    "display_name": "Duplicate",
                    "initial_password": password,
                },
            )
            assert duplicate.status_code == 409

            user_login = await _login(user, username, password)
            user_login.raise_for_status()
            session_cookie = user_login.cookies.get("ai_ops_session")
            assert session_cookie is not None
            assert (await user.get("/api/v1/dashboard/summary")).status_code == 403

        await first_app.state.engine.dispose()

        second_app = create_app(settings)
        applications.append(second_app)
        second_transport = httpx.ASGITransport(app=second_app)
        async with httpx.AsyncClient(
            transport=second_transport, base_url="http://test"
        ) as admin:
            admin_login = await _login(
                admin, "admin_demo", settings.demo_admin_password.get_secret_value()
            )
            admin_login.raise_for_status()
            persisted = await admin.get(f"/api/v1/admin/users/{user_id}")
            persisted.raise_for_status()
            assert persisted.json()["username"] == username

            disabled = await admin.post(f"/api/v1/admin/users/{user_id}/disable")
            disabled.raise_for_status()
            assert disabled.json()["is_active"] is False

            stale_client = httpx.AsyncClient(
                transport=second_transport,
                base_url="http://test",
                headers={"Cookie": f"ai_ops_session={session_cookie}"},
            )
            async with stale_client:
                assert (await stale_client.get("/api/v1/me")).status_code == 401

            disabled_login = await _login(admin, username, password)
            assert disabled_login.status_code == 401

            # Re-authenticate the administrator because the failed login did not alter its cookie.
            enabled = await admin.post(f"/api/v1/admin/users/{user_id}/enable")
            enabled.raise_for_status()
            assert enabled.json()["is_active"] is True
            assert enabled.json()["roles"] == []
            assert enabled.json()["modules"] == []

            new_user = httpx.AsyncClient(transport=second_transport, base_url="http://test")
            async with new_user:
                enabled_login = await _login(new_user, username, password)
                enabled_login.raise_for_status()
                assert (await new_user.get("/api/v1/dashboard/summary")).status_code == 403

            last_admin = await admin.post(
                f"/api/v1/admin/users/{admin_login.json()['user']['user_id']}/disable"
            )
            assert last_admin.status_code == 409
            assert last_admin.json()["error"]["code"] == "LAST_ACTIVE_ADMIN"

            audits = await admin.get("/api/v1/admin/audit-logs", params={"limit": 200})
            audits.raise_for_status()
            lifecycle_audits = [
                item
                for item in audits.json()["items"]
                if item["resource_id"] == str(user_id)
            ]
            assert {
                "identity.user.create",
                "identity.user.disable",
                "identity.user.enable",
            }.issubset({item["action"] for item in lifecycle_audits})
            assert password not in str(lifecycle_audits)
            assert "password_hash" not in str(lifecycle_audits)
    finally:
        cleanup_app = create_app(settings)
        try:
            if user_id is not None:
                async with cleanup_app.state.session_factory.begin() as session:
                    await session.execute(
                        delete(IdentityUser).where(IdentityUser.user_id == user_id)
                    )
        finally:
            await cleanup_app.state.engine.dispose()
        for application in applications:
            await application.state.engine.dispose()
