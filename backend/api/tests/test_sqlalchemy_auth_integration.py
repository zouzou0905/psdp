from pathlib import Path
from typing import Any, cast
from uuid import UUID

import httpx
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.db.base import Base
from app.db.models import (
    IdentityModule,
    IdentityPermission,
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserModule,
    IdentityUserRole,
    IdentityUserStoreScope,
    StoreRecord,
)
from app.db.session import create_session_factory
from app.main import create_app
from app.modules.identity.domain import ROLE_PERMISSIONS, RoleName
from app.modules.identity.security import PasswordService


def _settings(database_path: Path) -> Settings:
    return Settings(
        app_env="test",
        database_url=f"sqlite+aiosqlite:///{database_path.as_posix()}",
        auth_secret_key=SecretStr("stable-test-session-secret-with-at-least-32-characters"),
    )


async def _initialize_database(settings: Settings) -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = create_session_factory(engine)
    user_id = UUID("50000000-0000-0000-0000-000000000005")
    permissions = ROLE_PERMISSIONS[RoleName.OPERATIONS]
    async with session_factory.begin() as session:
        session.add(IdentityRole(role_name="operations", description="Operations"))
        session.add(IdentityModule(module_code="operations", description="Operations"))
        session.add_all(
            [
                IdentityPermission(
                    permission_name=permission.value,
                    description=permission.value,
                )
                for permission in permissions
            ]
        )
        await session.flush()
        session.add_all(
            [
                IdentityRolePermission(
                    role_name="operations",
                    permission_name=permission.value,
                )
                for permission in permissions
            ]
        )
        session.add(
            StoreRecord(
                store_id="store_persisted",
                display_name="Persisted Demo Store",
                marketplace="demo",
                organization_id="org_demo",
                status="active",
                credential_ref=None,
                revision=1,
            )
        )
        session.add(
            IdentityUser(
                user_id=user_id,
                username="operations_persisted",
                display_name="Persisted Operations",
                password_hash=PasswordService().hash("persistent-test-password"),
                is_active=True,
                token_version=1,
                authorization_revision=1,
                organization_ids=["org_demo"],
                team_ids=["team_operations"],
            )
        )
        await session.flush()
        session.add(IdentityUserRole(user_id=user_id, role_name="operations"))
        session.add(IdentityUserModule(user_id=user_id, module_code="operations"))
        session.add(IdentityUserStoreScope(user_id=user_id, store_id="store_persisted"))
    await engine.dispose()


async def _login_and_read_context(settings: Settings) -> tuple[int, dict[str, Any]]:
    application = create_app(settings)
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        readiness = await client.get("/health/ready")
        login = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "operations_persisted",
                "password": "persistent-test-password",
            },
        )
        assert login.status_code == 200
        assert login.cookies.get("ai_ops_session") is not None
        context = await client.get("/api/v1/me/access-context")
        assert context.status_code == 200
        denied = await client.get("/api/v1/admin/users")
        assert denied.status_code == 403
    await application.state.engine.dispose()
    return readiness.status_code, cast(dict[str, Any], context.json())


async def test_sqlalchemy_login_and_restart_persistence(tmp_path: Path) -> None:
    settings = _settings(tmp_path / "auth-integration.sqlite3")
    await _initialize_database(settings)

    first_readiness, first_context = await _login_and_read_context(settings)
    second_readiness, second_context = await _login_and_read_context(settings)

    assert first_readiness == second_readiness == 200
    assert first_context == second_context
    assert first_context["roles"] == ["operations"]
    assert first_context["modules"] == ["operations"]
    assert first_context["scopes"]["store_ids"] == ["store_persisted"]


def test_cookie_secure_policy_is_environment_derived() -> None:
    local = Settings(app_env="local")
    production = Settings(
        app_env="production",
        auth_secret_key=SecretStr("production-secret-with-at-least-32-characters"),
    )

    assert local.auth_cookie_secure is False
    assert production.auth_cookie_secure is True
