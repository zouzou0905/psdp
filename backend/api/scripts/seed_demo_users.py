import asyncio

from sqlalchemy import delete, select

from app.core.config import get_settings
from app.db.models import (
    IdentityUser,
    IdentityUserModule,
    IdentityUserPermission,
    IdentityUserRole,
    IdentityUserStoreScope,
    StoreRecord,
)
from app.db.session import create_engine, create_session_factory
from app.modules.identity.domain import ModuleCode, RoleName
from app.modules.identity.security import PasswordService

DEMO_USERNAMES = {
    RoleName.OPERATIONS: "operations_demo",
    RoleName.PROCUREMENT: "procurement_demo",
    RoleName.CREATIVE: "creative_demo",
    RoleName.ADMIN: "admin_demo",
}


async def seed() -> None:
    settings = get_settings()
    if settings.app_env not in {"local", "test"}:
        raise RuntimeError("Demo users are forbidden outside local/test environments")
    passwords = {
        RoleName.OPERATIONS: settings.demo_operations_password,
        RoleName.PROCUREMENT: settings.demo_procurement_password,
        RoleName.CREATIVE: settings.demo_creative_password,
        RoleName.ADMIN: settings.demo_admin_password,
    }
    if any(password is None for password in passwords.values()):
        raise RuntimeError("All DEMO_*_PASSWORD environment variables are required")

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    hasher = PasswordService()
    async with session_factory.begin() as session:
        for role in (RoleName.OPERATIONS, RoleName.PROCUREMENT, RoleName.CREATIVE):
            store_id = f"store_{role.value}_demo"
            store = await session.get(StoreRecord, store_id)
            if store is None:
                session.add(
                    StoreRecord(
                        store_id=store_id,
                        display_name=f"{role.value.title()} Demo Store (DEMO)",
                        marketplace="demo",
                        organization_id="org_demo",
                        status="active",
                        credential_ref=None,
                        revision=1,
                    )
                )
            else:
                store.display_name = f"{role.value.title()} Demo Store (DEMO)"
                store.marketplace = "demo"
                store.organization_id = "org_demo"
                store.status = "active"
        await session.flush()
        for role, username in DEMO_USERNAMES.items():
            existing = await session.scalar(
                select(IdentityUser).where(IdentityUser.username == username)
            )
            secret = passwords[role]
            if secret is None:
                raise RuntimeError("Demo password configuration changed during seed")
            modules = list(ModuleCode) if role is RoleName.ADMIN else [ModuleCode(role.value)]
            target_modules = {module.value for module in modules}
            target_store_ids = set() if role is RoleName.ADMIN else {f"store_{role.value}_demo"}
            if existing is None:
                user = IdentityUser(
                    username=username,
                    display_name=f"{role.value.title()} Demo (DEMO)",
                    password_hash=hasher.hash(secret.get_secret_value()),
                    is_active=True,
                    token_version=1,
                    authorization_revision=1,
                    organization_ids=["org_demo"],
                    team_ids=[f"team_{role.value}"],
                )
                session.add(user)
                await session.flush()
                access_changed = True
            else:
                user = existing
                user.display_name = f"{role.value.title()} Demo (DEMO)"
                user.is_active = True
                user.organization_ids = ["org_demo"]
                user.team_ids = [f"team_{role.value}"]
                if not hasher.verify(secret.get_secret_value(), user.password_hash):
                    user.password_hash = hasher.hash(secret.get_secret_value())
                    user.token_version += 1
                current_roles = set(
                    (
                        await session.scalars(
                            select(IdentityUserRole.role_name).where(
                                IdentityUserRole.user_id == user.user_id
                            )
                        )
                    ).all()
                )
                current_modules = set(
                    (
                        await session.scalars(
                            select(IdentityUserModule.module_code).where(
                                IdentityUserModule.user_id == user.user_id
                            )
                        )
                    ).all()
                )
                current_store_ids = set(
                    (
                        await session.scalars(
                            select(IdentityUserStoreScope.store_id).where(
                                IdentityUserStoreScope.user_id == user.user_id
                            )
                        )
                    ).all()
                )
                current_direct_permissions = set(
                    (
                        await session.scalars(
                            select(IdentityUserPermission.permission_name).where(
                                IdentityUserPermission.user_id == user.user_id
                            )
                        )
                    ).all()
                )
                access_changed = (
                    current_roles != {role.value}
                    or current_modules != target_modules
                    or current_store_ids != target_store_ids
                    or bool(current_direct_permissions)
                )
            if access_changed:
                if existing is not None:
                    user.authorization_revision += 1
                await session.execute(
                    delete(IdentityUserRole).where(IdentityUserRole.user_id == user.user_id)
                )
                await session.execute(
                    delete(IdentityUserModule).where(IdentityUserModule.user_id == user.user_id)
                )
                await session.execute(
                    delete(IdentityUserPermission).where(
                        IdentityUserPermission.user_id == user.user_id
                    )
                )
                await session.execute(
                    delete(IdentityUserStoreScope).where(
                        IdentityUserStoreScope.user_id == user.user_id
                    )
                )
                session.add(IdentityUserRole(user_id=user.user_id, role_name=role.value))
                session.add_all(
                    [
                        IdentityUserModule(user_id=user.user_id, module_code=module.value)
                        for module in modules
                    ]
                )
                session.add_all(
                    [
                        IdentityUserStoreScope(user_id=user.user_id, store_id=store_id)
                        for store_id in target_store_ids
                    ]
                )
        print("Seeded development accounts: " + ", ".join(DEMO_USERNAMES.values()))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
