import json
from collections.abc import Awaitable
from uuid import UUID

from app.core.errors import ApplicationError
from app.modules.audit.domain import AuditResult
from app.modules.audit.service import AuditService
from app.modules.identity.domain import (
    ModuleCode,
    Permission,
    Principal,
    RoleName,
    UserAccessListResponse,
    UserAccessResponse,
    UserIdentity,
    to_user_access,
)
from app.modules.identity.repository import (
    AuthorizationRevisionConflictError,
    DuplicateUsernameError,
    IdentityRepository,
    LastActiveAdminError,
)
from app.modules.identity.security import PasswordService
from app.modules.store.repository import StoreRepository


class IdentityAdminService:
    def __init__(
        self,
        repository: IdentityRepository,
        store_repository: StoreRepository,
        audit_service: AuditService,
        password_service: PasswordService,
    ) -> None:
        self._repository = repository
        self._store_repository = store_repository
        self._audit_service = audit_service
        self._password_service = password_service

    async def create_user(
        self,
        actor: Principal,
        username: str,
        display_name: str,
        initial_password: str,
        trace_id: str | None,
    ) -> UserAccessResponse:
        try:
            user = await self._repository.create_user(
                username,
                display_name,
                self._password_service.hash(initial_password),
            )
        except DuplicateUsernameError as exc:
            await self._audit_service.record(
                action="identity.user.create",
                resource_type="user_access",
                resource_id=None,
                result=AuditResult.FAILURE,
                trace_id=trace_id,
                principal=actor,
                metadata_summary={"username": username, "reason": "duplicate_username"},
            )
            raise ApplicationError(
                "USERNAME_ALREADY_EXISTS", "Username already exists", 409
            ) from exc
        response = to_user_access(user)
        await self._audit_service.record(
            action="identity.user.create",
            resource_type="user_access",
            resource_id=str(user.user_id),
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=actor,
            metadata_summary={
                "after": json.dumps(
                    response.model_dump(mode="json"), ensure_ascii=False, sort_keys=True
                )
            },
        )
        return response

    async def set_user_enabled(
        self,
        actor: Principal,
        user_id: UUID,
        *,
        enabled: bool,
        trace_id: str | None,
    ) -> UserAccessResponse:
        action = "identity.user.enable" if enabled else "identity.user.disable"
        try:
            result = await self._repository.set_active(user_id, enabled=enabled)
        except LastActiveAdminError as exc:
            await self._audit_service.record(
                action=action,
                resource_type="user_access",
                resource_id=str(user_id),
                result=AuditResult.FAILURE,
                trace_id=trace_id,
                principal=actor,
                metadata_summary={"reason": "last_active_admin"},
            )
            raise ApplicationError(
                "LAST_ACTIVE_ADMIN", "The last active administrator cannot be disabled", 409
            ) from exc
        if result is None:
            await self._audit_service.record(
                action=action,
                resource_type="user_access",
                resource_id=str(user_id),
                result=AuditResult.FAILURE,
                trace_id=trace_id,
                principal=actor,
                metadata_summary={"reason": "user_not_found"},
            )
            raise ApplicationError("USER_NOT_FOUND", "User not found", 404)
        before, after = result
        await self._audit_service.record(
            action=action,
            resource_type="user_access",
            resource_id=str(user_id),
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=actor,
            metadata_summary={
                "before": json.dumps(
                    to_user_access(before).model_dump(mode="json"),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "after": json.dumps(
                    to_user_access(after).model_dump(mode="json"),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            },
        )
        return to_user_access(after)

    async def list_users(self) -> UserAccessListResponse:
        users = await self._repository.list_users()
        return UserAccessListResponse(
            items=[to_user_access(user) for user in users], total=len(users)
        )

    async def get_user(self, user_id: UUID) -> UserAccessResponse:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise ApplicationError("USER_NOT_FOUND", "User not found", 404)
        return to_user_access(user)

    async def update_roles_permissions(
        self,
        actor: Principal,
        user_id: UUID,
        roles: frozenset[RoleName],
        permissions: frozenset[Permission],
        expected_revision: int,
        trace_id: str | None,
    ) -> UserAccessResponse:
        result = await self._apply_change(
            self._repository.update_roles_permissions(
                user_id, roles, permissions, expected_revision
            ),
            actor,
            user_id,
            "identity.user.roles_permissions.update",
            trace_id,
        )
        return to_user_access(result)

    async def update_modules(
        self,
        actor: Principal,
        user_id: UUID,
        modules: frozenset[ModuleCode],
        expected_revision: int,
        trace_id: str | None,
    ) -> UserAccessResponse:
        result = await self._apply_change(
            self._repository.update_modules(user_id, modules, expected_revision),
            actor,
            user_id,
            "identity.user.modules.update",
            trace_id,
        )
        return to_user_access(result)

    async def update_store_scopes(
        self,
        actor: Principal,
        user_id: UUID,
        store_ids: frozenset[str],
        expected_revision: int,
        trace_id: str | None,
    ) -> UserAccessResponse:
        found_stores = await self._store_repository.list_by_ids(store_ids)
        found_ids = {store.store_id for store in found_stores}
        missing = sorted(store_ids.difference(found_ids))
        if missing:
            raise ApplicationError(
                "STORE_NOT_FOUND",
                f"Unknown store IDs: {', '.join(missing)}",
                422,
            )
        result = await self._apply_change(
            self._repository.update_store_scopes(user_id, store_ids, expected_revision),
            actor,
            user_id,
            "identity.user.store_scopes.update",
            trace_id,
        )
        return to_user_access(result)

    async def _apply_change(
        self,
        operation: Awaitable[tuple[UserIdentity, UserIdentity] | None],
        actor: Principal,
        user_id: UUID,
        action: str,
        trace_id: str | None,
    ) -> UserIdentity:
        try:
            result = await operation
        except AuthorizationRevisionConflictError as exc:
            raise ApplicationError(
                "AUTHORIZATION_REVISION_CONFLICT",
                "Authorization changed; reload before updating",
                409,
            ) from exc
        if result is None:
            raise ApplicationError("USER_NOT_FOUND", "User not found", 404)
        before, after = result
        await self._audit_service.record(
            action=action,
            resource_type="user_access",
            resource_id=str(user_id),
            result=AuditResult.SUCCESS,
            trace_id=trace_id,
            principal=actor,
            metadata_summary={
                "before": json.dumps(
                    to_user_access(before).model_dump(mode="json"),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "after": json.dumps(
                    to_user_access(after).model_dump(mode="json"),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            },
        )
        return after
