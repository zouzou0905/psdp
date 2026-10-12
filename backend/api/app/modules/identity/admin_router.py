from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.modules.authorization.dependencies import require_access
from app.modules.identity.admin_service import IdentityAdminService
from app.modules.identity.domain import (
    CreateUserRequest,
    ModuleCode,
    Permission,
    Principal,
    UpdateModulesRequest,
    UpdateRolesRequest,
    UpdateStoreScopesRequest,
    UserAccessListResponse,
    UserAccessResponse,
)

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def get_identity_admin_service(request: Request) -> IdentityAdminService:
    return cast(IdentityAdminService, request.app.state.identity_admin_service)


@router.post("", response_model=UserAccessResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.USER_MANAGE)),
    ],
    service: Annotated[IdentityAdminService, Depends(get_identity_admin_service)],
) -> UserAccessResponse:
    return await service.create_user(
        principal,
        payload.username,
        payload.display_name,
        payload.initial_password.get_secret_value(),
        getattr(request.state, "trace_id", None),
    )


@router.get("", response_model=UserAccessListResponse)
async def list_users(
    _principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.USER_MANAGE)),
    ],
    service: Annotated[IdentityAdminService, Depends(get_identity_admin_service)],
) -> UserAccessListResponse:
    return await service.list_users()


@router.get("/{user_id}", response_model=UserAccessResponse)
async def get_user(
    user_id: UUID,
    _principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.USER_MANAGE)),
    ],
    service: Annotated[IdentityAdminService, Depends(get_identity_admin_service)],
) -> UserAccessResponse:
    return await service.get_user(user_id)


@router.post("/{user_id}/enable", response_model=UserAccessResponse)
async def enable_user(
    user_id: UUID,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.USER_MANAGE)),
    ],
    service: Annotated[IdentityAdminService, Depends(get_identity_admin_service)],
) -> UserAccessResponse:
    return await service.set_user_enabled(
        principal,
        user_id,
        enabled=True,
        trace_id=getattr(request.state, "trace_id", None),
    )


@router.post("/{user_id}/disable", response_model=UserAccessResponse)
async def disable_user(
    user_id: UUID,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.USER_MANAGE)),
    ],
    service: Annotated[IdentityAdminService, Depends(get_identity_admin_service)],
) -> UserAccessResponse:
    return await service.set_user_enabled(
        principal,
        user_id,
        enabled=False,
        trace_id=getattr(request.state, "trace_id", None),
    )


@router.put("/{user_id}/roles", response_model=UserAccessResponse)
async def update_roles(
    user_id: UUID,
    payload: UpdateRolesRequest,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.USER_MANAGE)),
    ],
    service: Annotated[IdentityAdminService, Depends(get_identity_admin_service)],
) -> UserAccessResponse:
    return await service.update_roles_permissions(
        principal,
        user_id,
        frozenset(payload.roles),
        frozenset(payload.permissions),
        payload.expected_authorization_revision,
        getattr(request.state, "trace_id", None),
    )


@router.put("/{user_id}/modules", response_model=UserAccessResponse)
async def update_modules(
    user_id: UUID,
    payload: UpdateModulesRequest,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.USER_MANAGE)),
    ],
    service: Annotated[IdentityAdminService, Depends(get_identity_admin_service)],
) -> UserAccessResponse:
    return await service.update_modules(
        principal,
        user_id,
        frozenset(payload.modules),
        payload.expected_authorization_revision,
        getattr(request.state, "trace_id", None),
    )


@router.put("/{user_id}/store-scopes", response_model=UserAccessResponse)
async def update_store_scopes(
    user_id: UUID,
    payload: UpdateStoreScopesRequest,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.USER_MANAGE)),
    ],
    service: Annotated[IdentityAdminService, Depends(get_identity_admin_service)],
) -> UserAccessResponse:
    return await service.update_store_scopes(
        principal,
        user_id,
        frozenset(payload.store_ids),
        payload.expected_authorization_revision,
        getattr(request.state, "trace_id", None),
    )
