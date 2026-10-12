from collections.abc import Iterable
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import (
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserModule,
    IdentityUserPermission,
    IdentityUserRole,
    IdentityUserStoreScope,
)
from app.modules.identity.domain import (
    ROLE_PERMISSIONS,
    DataScope,
    ModuleCode,
    Permission,
    RoleName,
    UserIdentity,
)


class AuthorizationRevisionConflictError(Exception):
    pass


def _known_permissions(names: Iterable[str]) -> frozenset[Permission]:
    permissions: set[Permission] = set()
    for name in names:
        try:
            permissions.add(Permission(name))
        except ValueError:
            # Retired permission names remain inert if an older database row survives.
            continue
    return frozenset(permissions)


class DuplicateUsernameError(Exception):
    pass


class LastActiveAdminError(Exception):
    pass


class IdentityRepository(Protocol):
    async def get_by_username(self, username: str) -> UserIdentity | None: ...

    async def get_by_id(self, user_id: UUID) -> UserIdentity | None: ...

    async def list_users(self) -> list[UserIdentity]: ...

    async def create_user(
        self, username: str, display_name: str, password_hash: str
    ) -> UserIdentity: ...

    async def set_active(
        self, user_id: UUID, *, enabled: bool
    ) -> tuple[UserIdentity, UserIdentity] | None: ...

    async def increment_token_version(self, user_id: UUID) -> None: ...

    async def update_roles_permissions(
        self,
        user_id: UUID,
        roles: frozenset[RoleName],
        permissions: frozenset[Permission],
        expected_revision: int,
    ) -> tuple[UserIdentity, UserIdentity] | None: ...

    async def update_modules(
        self,
        user_id: UUID,
        modules: frozenset[ModuleCode],
        expected_revision: int,
    ) -> tuple[UserIdentity, UserIdentity] | None: ...

    async def update_store_scopes(
        self,
        user_id: UUID,
        store_ids: frozenset[str],
        expected_revision: int,
    ) -> tuple[UserIdentity, UserIdentity] | None: ...


def _effective_permissions(
    roles: frozenset[RoleName], direct_permissions: frozenset[Permission]
) -> frozenset[Permission]:
    inherited = set[Permission]()
    for role in roles:
        inherited.update(ROLE_PERMISSIONS[role])
    return frozenset(inherited.union(direct_permissions))


class InMemoryIdentityRepository:
    def __init__(self, users: list[UserIdentity] | None = None) -> None:
        self._users = {user.user_id: user for user in users or []}

    async def get_by_username(self, username: str) -> UserIdentity | None:
        return next((user for user in self._users.values() if user.username == username), None)

    async def get_by_id(self, user_id: UUID) -> UserIdentity | None:
        return self._users.get(user_id)

    async def list_users(self) -> list[UserIdentity]:
        return sorted(self._users.values(), key=lambda user: user.username)

    async def create_user(
        self, username: str, display_name: str, password_hash: str
    ) -> UserIdentity:
        if any(user.username == username for user in self._users.values()):
            raise DuplicateUsernameError
        user = UserIdentity(
            user_id=uuid4(),
            username=username,
            display_name=display_name,
            password_hash=password_hash,
            is_active=True,
            token_version=1,
            authorization_revision=1,
            roles=frozenset(),
            modules=frozenset(),
            direct_permissions=frozenset(),
            permissions=frozenset(),
            scope=DataScope(),
        )
        self._users[user.user_id] = user
        return user

    async def set_active(
        self, user_id: UUID, *, enabled: bool
    ) -> tuple[UserIdentity, UserIdentity] | None:
        before = self._users.get(user_id)
        if before is None:
            return None
        if not enabled and before.is_active and self._is_valid_admin(before):
            active_admins = sum(
                user.is_active and self._is_valid_admin(user) for user in self._users.values()
            )
            if active_admins <= 1:
                raise LastActiveAdminError
        after = before.model_copy(
            update={
                "is_active": enabled,
                "token_version": before.token_version + (before.is_active != enabled),
            }
        )
        self._users[user_id] = after
        return before, after

    @staticmethod
    def _is_valid_admin(user: UserIdentity) -> bool:
        return RoleName.ADMIN in user.roles and ModuleCode.ADMIN in user.modules

    async def increment_token_version(self, user_id: UUID) -> None:
        user = self._users.get(user_id)
        if user is not None:
            self._users[user_id] = user.model_copy(update={"token_version": user.token_version + 1})

    async def update_roles_permissions(
        self,
        user_id: UUID,
        roles: frozenset[RoleName],
        permissions: frozenset[Permission],
        expected_revision: int,
    ) -> tuple[UserIdentity, UserIdentity] | None:
        return self._replace(
            user_id,
            expected_revision,
            {
                "roles": roles,
                "direct_permissions": permissions,
                "permissions": _effective_permissions(roles, permissions),
            },
        )

    async def update_modules(
        self,
        user_id: UUID,
        modules: frozenset[ModuleCode],
        expected_revision: int,
    ) -> tuple[UserIdentity, UserIdentity] | None:
        return self._replace(user_id, expected_revision, {"modules": modules})

    async def update_store_scopes(
        self,
        user_id: UUID,
        store_ids: frozenset[str],
        expected_revision: int,
    ) -> tuple[UserIdentity, UserIdentity] | None:
        user = self._users.get(user_id)
        if user is None:
            return None
        return self._replace(
            user_id,
            expected_revision,
            {"scope": user.scope.model_copy(update={"store_ids": store_ids})},
        )

    def _replace(
        self, user_id: UUID, expected_revision: int, updates: dict[str, object]
    ) -> tuple[UserIdentity, UserIdentity] | None:
        before = self._users.get(user_id)
        if before is None:
            return None
        if before.authorization_revision != expected_revision:
            raise AuthorizationRevisionConflictError
        after = before.model_copy(
            update={**updates, "authorization_revision": expected_revision + 1}
        )
        self._users[user_id] = after
        return before, after


class SqlAlchemyIdentityRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_username(self, username: str) -> UserIdentity | None:
        async with self._session_factory() as session:
            user = await session.scalar(
                select(IdentityUser).where(IdentityUser.username == username)
            )
            return await self._hydrate(session, user)

    async def get_by_id(self, user_id: UUID) -> UserIdentity | None:
        async with self._session_factory() as session:
            user = await session.get(IdentityUser, user_id)
            return await self._hydrate(session, user)

    async def list_users(self) -> list[UserIdentity]:
        async with self._session_factory() as session:
            users = (
                await session.scalars(select(IdentityUser).order_by(IdentityUser.username))
            ).all()
            result: list[UserIdentity] = []
            for user in users:
                hydrated = await self._hydrate(session, user)
                if hydrated is not None:
                    result.append(hydrated)
            return result

    async def create_user(
        self, username: str, display_name: str, password_hash: str
    ) -> UserIdentity:
        try:
            async with self._session_factory.begin() as session:
                user = IdentityUser(
                    username=username,
                    display_name=display_name,
                    password_hash=password_hash,
                    is_active=True,
                    token_version=1,
                    authorization_revision=1,
                    organization_ids=[],
                    team_ids=[],
                )
                session.add(user)
                await session.flush()
                hydrated = await self._hydrate(session, user)
                if hydrated is None:
                    raise RuntimeError("Created user could not be hydrated")
                return hydrated
        except IntegrityError as exc:
            raise DuplicateUsernameError from exc

    async def set_active(
        self, user_id: UUID, *, enabled: bool
    ) -> tuple[UserIdentity, UserIdentity] | None:
        async with self._session_factory.begin() as session:
            # Serialize account-state changes that could affect the valid-admin invariant.
            await session.scalar(
                select(IdentityRole)
                .where(IdentityRole.role_name == RoleName.ADMIN.value)
                .with_for_update()
            )
            user = await session.scalar(
                select(IdentityUser)
                .where(IdentityUser.user_id == user_id)
                .with_for_update()
            )
            if user is None:
                return None
            before = await self._hydrate(session, user)
            if before is None:
                return None
            if not enabled and before.is_active and self._is_valid_admin(before):
                active_admin_ids = set(
                    (
                        await session.scalars(
                            select(IdentityUser.user_id)
                            .join(IdentityUserRole)
                            .join(IdentityUserModule)
                            .where(
                                IdentityUser.is_active.is_(True),
                                IdentityUserRole.role_name == RoleName.ADMIN.value,
                                IdentityUserModule.module_code == ModuleCode.ADMIN.value,
                            )
                            .with_for_update(of=IdentityUser)
                        )
                    ).all()
                )
                if len(active_admin_ids) <= 1:
                    raise LastActiveAdminError
            if user.is_active != enabled:
                user.is_active = enabled
                user.token_version += 1
                await session.flush()
            after = await self._hydrate(session, user)
            if after is None:
                raise RuntimeError("Updated user could not be hydrated")
            return before, after

    @staticmethod
    def _is_valid_admin(user: UserIdentity) -> bool:
        return RoleName.ADMIN in user.roles and ModuleCode.ADMIN in user.modules

    async def increment_token_version(self, user_id: UUID) -> None:
        async with self._session_factory.begin() as session:
            await session.execute(
                update(IdentityUser)
                .where(IdentityUser.user_id == user_id)
                .values(token_version=IdentityUser.token_version + 1)
            )

    async def update_roles_permissions(
        self,
        user_id: UUID,
        roles: frozenset[RoleName],
        permissions: frozenset[Permission],
        expected_revision: int,
    ) -> tuple[UserIdentity, UserIdentity] | None:
        async with self._session_factory.begin() as session:
            locked = await self._lock_and_snapshot(session, user_id, expected_revision)
            if locked is None:
                return None
            user, before = locked
            await session.execute(
                delete(IdentityUserRole).where(IdentityUserRole.user_id == user_id)
            )
            await session.execute(
                delete(IdentityUserPermission).where(IdentityUserPermission.user_id == user_id)
            )
            session.add_all(
                [IdentityUserRole(user_id=user_id, role_name=role.value) for role in roles]
            )
            session.add_all(
                [
                    IdentityUserPermission(user_id=user_id, permission_name=permission.value)
                    for permission in permissions
                ]
            )
            return before, await self._finish_update(session, user)

    async def update_modules(
        self,
        user_id: UUID,
        modules: frozenset[ModuleCode],
        expected_revision: int,
    ) -> tuple[UserIdentity, UserIdentity] | None:
        async with self._session_factory.begin() as session:
            locked = await self._lock_and_snapshot(session, user_id, expected_revision)
            if locked is None:
                return None
            user, before = locked
            await session.execute(
                delete(IdentityUserModule).where(IdentityUserModule.user_id == user_id)
            )
            session.add_all(
                [
                    IdentityUserModule(user_id=user_id, module_code=module.value)
                    for module in modules
                ]
            )
            return before, await self._finish_update(session, user)

    async def update_store_scopes(
        self,
        user_id: UUID,
        store_ids: frozenset[str],
        expected_revision: int,
    ) -> tuple[UserIdentity, UserIdentity] | None:
        async with self._session_factory.begin() as session:
            locked = await self._lock_and_snapshot(session, user_id, expected_revision)
            if locked is None:
                return None
            user, before = locked
            await session.execute(
                delete(IdentityUserStoreScope).where(IdentityUserStoreScope.user_id == user_id)
            )
            session.add_all(
                [
                    IdentityUserStoreScope(user_id=user_id, store_id=store_id)
                    for store_id in store_ids
                ]
            )
            return before, await self._finish_update(session, user)

    async def _lock_and_snapshot(
        self, session: AsyncSession, user_id: UUID, expected_revision: int
    ) -> tuple[IdentityUser, UserIdentity] | None:
        user = await session.scalar(
            select(IdentityUser).where(IdentityUser.user_id == user_id).with_for_update()
        )
        if user is None:
            return None
        if user.authorization_revision != expected_revision:
            raise AuthorizationRevisionConflictError
        before = await self._hydrate(session, user)
        if before is None:
            return None
        return user, before

    async def _finish_update(self, session: AsyncSession, user: IdentityUser) -> UserIdentity:
        user.authorization_revision += 1
        await session.flush()
        after = await self._hydrate(session, user)
        if after is None:
            raise RuntimeError("Updated user could not be hydrated")
        return after

    async def _hydrate(
        self, session: AsyncSession, user: IdentityUser | None
    ) -> UserIdentity | None:
        if user is None:
            return None
        role_names = frozenset(
            RoleName(value)
            for value in (
                await session.scalars(
                    select(IdentityUserRole.role_name).where(
                        IdentityUserRole.user_id == user.user_id
                    )
                )
            ).all()
        )
        inherited_names = set(
            (
                await session.scalars(
                    select(IdentityRolePermission.permission_name).where(
                        IdentityRolePermission.role_name.in_(role_names)
                    )
                )
            ).all()
        )
        direct_permissions = _known_permissions(
            (
                await session.scalars(
                    select(IdentityUserPermission.permission_name).where(
                        IdentityUserPermission.user_id == user.user_id
                    )
                )
            ).all()
        )
        modules = frozenset(
            ModuleCode(value)
            for value in (
                await session.scalars(
                    select(IdentityUserModule.module_code).where(
                        IdentityUserModule.user_id == user.user_id
                    )
                )
            ).all()
        )
        store_ids = frozenset(
            (
                await session.scalars(
                    select(IdentityUserStoreScope.store_id).where(
                        IdentityUserStoreScope.user_id == user.user_id
                    )
                )
            ).all()
        )
        permissions = frozenset(
            _known_permissions(inherited_names).union(direct_permissions)
        )
        return UserIdentity(
            user_id=user.user_id,
            username=user.username,
            display_name=user.display_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
            token_version=user.token_version,
            authorization_revision=user.authorization_revision,
            roles=role_names,
            modules=modules,
            direct_permissions=direct_permissions,
            permissions=permissions,
            scope=DataScope(
                organization_ids=frozenset(user.organization_ids),
                team_ids=frozenset(user.team_ids),
                store_ids=store_ids,
            ),
        )
