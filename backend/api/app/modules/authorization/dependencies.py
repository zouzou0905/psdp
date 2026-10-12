from collections.abc import Callable, Coroutine
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import APIKeyCookie

from app.core.errors import ApplicationError
from app.modules.audit.domain import AuditResult
from app.modules.audit.service import AuditService
from app.modules.identity.domain import (
    DataScope,
    ModuleCode,
    Permission,
    Principal,
    RoleName,
)
from app.modules.identity.service import AuthenticationService

SESSION_COOKIE_NAME = "ai_ops_session"
session_cookie_scheme = APIKeyCookie(name=SESSION_COOKIE_NAME, auto_error=False)


def get_authentication_service(request: Request) -> AuthenticationService:
    return cast(AuthenticationService, request.app.state.authentication_service)


def get_audit_service(request: Request) -> AuditService:
    return cast(AuditService, request.app.state.audit_service)


async def get_current_user(
    session_token: Annotated[str | None, Depends(session_cookie_scheme)],
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> Principal:
    if session_token is None:
        raise ApplicationError(
            "AUTHENTICATION_REQUIRED",
            "Authentication is required",
            401,
        )
    return await service.authenticate(session_token)


AuthorizationDependency = Callable[..., Coroutine[Any, Any, Principal]]


async def _deny(
    request: Request,
    principal: Principal,
    audit_service: AuditService,
    requirement: str,
) -> None:
    await audit_service.record(
        action="authorization.denied",
        resource_type="permission",
        resource_id=requirement,
        result=AuditResult.DENIED,
        trace_id=getattr(request.state, "trace_id", None),
        principal=principal,
        metadata_summary={"path": request.url.path, "method": request.method},
    )
    raise ApplicationError("PERMISSION_DENIED", "Permission denied", 403)


def require_permission(permission: Permission) -> AuthorizationDependency:
    async def dependency(
        request: Request,
        principal: Annotated[Principal, Depends(get_current_user)],
        audit_service: Annotated[AuditService, Depends(get_audit_service)],
    ) -> Principal:
        if permission not in principal.permissions:
            await _deny(request, principal, audit_service, permission.value)
        return principal

    return dependency


def require_any_permission(*permissions: Permission) -> AuthorizationDependency:
    async def dependency(
        request: Request,
        principal: Annotated[Principal, Depends(get_current_user)],
        audit_service: Annotated[AuditService, Depends(get_audit_service)],
    ) -> Principal:
        if principal.permissions.isdisjoint(permissions):
            await _deny(
                request,
                principal,
                audit_service,
                "|".join(permission.value for permission in permissions),
            )
        return principal

    return dependency


def require_role(role: RoleName) -> AuthorizationDependency:
    async def dependency(
        request: Request,
        principal: Annotated[Principal, Depends(get_current_user)],
        audit_service: Annotated[AuditService, Depends(get_audit_service)],
    ) -> Principal:
        if role not in principal.roles:
            await _deny(request, principal, audit_service, f"role:{role.value}")
        return principal

    return dependency


def require_module(module: ModuleCode) -> AuthorizationDependency:
    async def dependency(
        request: Request,
        principal: Annotated[Principal, Depends(get_current_user)],
        audit_service: Annotated[AuditService, Depends(get_audit_service)],
    ) -> Principal:
        if module not in principal.modules:
            await _deny(request, principal, audit_service, f"module:{module.value}")
        return principal

    return dependency


def require_access(module: ModuleCode, permission: Permission) -> AuthorizationDependency:
    async def dependency(
        request: Request,
        principal: Annotated[Principal, Depends(get_current_user)],
        audit_service: Annotated[AuditService, Depends(get_audit_service)],
    ) -> Principal:
        if module not in principal.modules:
            await _deny(request, principal, audit_service, f"module:{module.value}")
        if permission not in principal.permissions:
            await _deny(request, principal, audit_service, permission.value)
        return principal

    return dependency


def require_any_access(
    *requirements: tuple[ModuleCode, Permission],
) -> AuthorizationDependency:
    async def dependency(
        request: Request,
        principal: Annotated[Principal, Depends(get_current_user)],
        audit_service: Annotated[AuditService, Depends(get_audit_service)],
    ) -> Principal:
        if not any(
            module in principal.modules and permission in principal.permissions
            for module, permission in requirements
        ):
            await _deny(
                request,
                principal,
                audit_service,
                "|".join(
                    f"{module.value}:{permission.value}"
                    for module, permission in requirements
                ),
            )
        return principal

    return dependency


def enforce_scope(
    principal: Principal,
    resource_scope: DataScope,
    *,
    assigned_user_id: UUID | None = None,
) -> None:
    """Application-service guard used after repository-level filtering for key actions."""

    if Permission.ALL_BUSINESS_READ in principal.permissions:
        return
    if assigned_user_id == principal.user_id:
        return
    if principal.scope.organization_ids.intersection(resource_scope.organization_ids):
        return
    if principal.scope.team_ids.intersection(resource_scope.team_ids):
        return
    if principal.scope.store_ids.intersection(resource_scope.store_ids):
        return
    raise ApplicationError("SCOPE_DENIED", "Resource is outside the authorized scope", 403)


def enforce_store_scope(principal: Principal, store_id: str) -> None:
    if Permission.ALL_BUSINESS_READ in principal.permissions:
        return
    if store_id in principal.scope.store_ids:
        return
    raise ApplicationError("STORE_SCOPE_DENIED", "Store is outside the authorized scope", 403)
