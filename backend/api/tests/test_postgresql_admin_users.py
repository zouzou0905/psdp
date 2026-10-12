import os
from typing import Any, cast
from uuid import UUID

import httpx
import pytest

from app.core.config import Settings
from app.main import create_app
from app.modules.identity.domain import ModuleCode, Permission, RoleName
from app.modules.identity.repository import SqlAlchemyIdentityRepository

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRESQL_INTEGRATION_TESTS") != "1",
    reason="Set RUN_POSTGRESQL_INTEGRATION_TESTS=1 to exercise the local PostgreSQL database",
)


async def _login(client: httpx.AsyncClient, username: str, password: str) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    response.raise_for_status()
    assert response.cookies.get("ai_ops_session") is not None
    return cast(dict[str, Any], response.json())


def _assert_no_credentials(payload: object) -> None:
    serialized = str(payload).lower()
    for forbidden in ("password", "password_hash", "access_token", "refresh_token"):
        assert forbidden not in serialized


async def _fallback_restore(
    settings: Settings,
    user_id: UUID,
    roles: set[RoleName],
    permissions: set[Permission],
    modules: set[ModuleCode],
    store_ids: set[str],
) -> None:
    application = create_app(settings)
    repository = SqlAlchemyIdentityRepository(application.state.session_factory)
    try:
        current = await repository.get_by_id(user_id)
        if current is None:
            return
        if current.roles != frozenset(roles) or current.direct_permissions != frozenset(
            permissions
        ):
            await repository.update_roles_permissions(
                current.user_id,
                frozenset(roles),
                frozenset(permissions),
                current.authorization_revision,
            )
            current = await repository.get_by_id(current.user_id)
            assert current is not None
        if current.modules != frozenset(modules):
            await repository.update_modules(
                current.user_id,
                frozenset(modules),
                current.authorization_revision,
            )
            current = await repository.get_by_id(current.user_id)
            assert current is not None
        if current.scope.store_ids != frozenset(store_ids):
            await repository.update_store_scopes(
                current.user_id,
                frozenset(store_ids),
                current.authorization_revision,
            )
    finally:
        await application.state.engine.dispose()


async def test_postgresql_admin_authorization_persists_across_app_restart() -> None:
    settings = Settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert settings.demo_operations_password is not None
    assert settings.demo_admin_password is not None

    original_roles: set[RoleName] | None = None
    original_permissions: set[Permission] | None = None
    original_modules: set[ModuleCode] | None = None
    original_store_ids: set[str] | None = None
    user_id: UUID | None = None
    restored = False

    try:
        first_app = create_app(settings)
        first_transport = httpx.ASGITransport(app=first_app)
        async with (
            httpx.AsyncClient(transport=first_transport, base_url="http://test") as admin,
            httpx.AsyncClient(transport=first_transport, base_url="http://test") as operations,
        ):
            await _login(
                admin,
                "admin_demo",
                settings.demo_admin_password.get_secret_value(),
            )
            operations_context = await _login(
                operations,
                "operations_demo",
                settings.demo_operations_password.get_secret_value(),
            )
            user_id = UUID(operations_context["user"]["user_id"])
            listed = await admin.get("/api/v1/admin/users")
            detail = await admin.get(f"/api/v1/admin/users/{user_id}")
            assert listed.status_code == detail.status_code == 200
            _assert_no_credentials(listed.json())
            _assert_no_credentials(detail.json())

            original = detail.json()
            original_roles = {RoleName(value) for value in original["roles"]}
            original_permissions = {Permission(value) for value in original["direct_permissions"]}
            original_modules = {ModuleCode(value) for value in original["modules"]}
            original_store_ids = set(original["scopes"]["store_ids"])
            revision = original["authorization_revision"]

            changed_roles = original_roles | {RoleName.CREATIVE}
            changed_modules = original_modules | {ModuleCode.CREATIVE}
            changed_store_ids = original_store_ids | {"store_creative_demo"}
            roles_update = await admin.put(
                f"/api/v1/admin/users/{user_id}/roles",
                json={
                    "roles": sorted(role.value for role in changed_roles),
                    "permissions": sorted(permission.value for permission in original_permissions),
                    "expected_authorization_revision": revision,
                },
            )
            roles_update.raise_for_status()
            revision = roles_update.json()["authorization_revision"]
            modules_update = await admin.put(
                f"/api/v1/admin/users/{user_id}/modules",
                json={
                    "modules": sorted(module.value for module in changed_modules),
                    "expected_authorization_revision": revision,
                },
            )
            modules_update.raise_for_status()
            revision = modules_update.json()["authorization_revision"]
            stores_update = await admin.put(
                f"/api/v1/admin/users/{user_id}/store-scopes",
                json={
                    "store_ids": sorted(changed_store_ids),
                    "expected_authorization_revision": revision,
                },
            )
            stores_update.raise_for_status()
            revision = stores_update.json()["authorization_revision"]

            stale = await operations.get("/api/v1/me/access-context")
            assert stale.status_code == 401
            conflict = await admin.put(
                f"/api/v1/admin/users/{user_id}/modules",
                json={
                    "modules": sorted(module.value for module in changed_modules),
                    "expected_authorization_revision": original["authorization_revision"],
                },
            )
            assert conflict.status_code == 409
        await first_app.state.engine.dispose()

        assert user_id is not None
        assert original_roles is not None
        assert original_permissions is not None
        assert original_modules is not None
        assert original_store_ids is not None

        second_app = create_app(settings)
        second_transport = httpx.ASGITransport(app=second_app)
        async with httpx.AsyncClient(transport=second_transport, base_url="http://test") as admin:
            await _login(
                admin,
                "admin_demo",
                settings.demo_admin_password.get_secret_value(),
            )
            persisted = await admin.get(f"/api/v1/admin/users/{user_id}")
            persisted.raise_for_status()
            persisted_body = persisted.json()
            assert set(persisted_body["roles"]) == {role.value for role in changed_roles}
            assert set(persisted_body["modules"]) == {module.value for module in changed_modules}
            assert set(persisted_body["scopes"]["store_ids"]) == changed_store_ids

            revision = persisted_body["authorization_revision"]
            for suffix, body in (
                (
                    "roles",
                    {
                        "roles": sorted(role.value for role in original_roles),
                        "permissions": sorted(
                            permission.value for permission in original_permissions
                        ),
                    },
                ),
                (
                    "modules",
                    {"modules": sorted(module.value for module in original_modules)},
                ),
                (
                    "store-scopes",
                    {"store_ids": sorted(original_store_ids)},
                ),
            ):
                response = await admin.put(
                    f"/api/v1/admin/users/{user_id}/{suffix}",
                    json={**body, "expected_authorization_revision": revision},
                )
                response.raise_for_status()
                revision = response.json()["authorization_revision"]

            audits = await admin.get("/api/v1/admin/audit-logs")
            audits.raise_for_status()
            actions = {
                item["action"]
                for item in audits.json()["items"]
                if item["resource_id"] == str(user_id)
            }
            assert {
                "identity.user.roles_permissions.update",
                "identity.user.modules.update",
                "identity.user.store_scopes.update",
            }.issubset(actions)
            restored = True
        await second_app.state.engine.dispose()
    finally:
        if (
            not restored
            and user_id is not None
            and original_roles is not None
            and original_permissions is not None
            and original_modules is not None
            and original_store_ids is not None
        ):
            await _fallback_restore(
                settings,
                user_id,
                original_roles,
                original_permissions,
                original_modules,
                original_store_ids,
            )
