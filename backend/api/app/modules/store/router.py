from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status

from app.modules.authorization.dependencies import require_access
from app.modules.identity.domain import ModuleCode, Permission, Principal
from app.modules.store.domain import (
    CreateStoreRequest,
    StoreListResponse,
    StoreResponse,
    UpdateStoreRequest,
)
from app.modules.store.service import StoreService

router = APIRouter(prefix="/admin/stores", tags=["admin-stores"])


def get_store_service(request: Request) -> StoreService:
    return cast(StoreService, request.app.state.store_service)


@router.get("", response_model=StoreListResponse)
async def list_stores(
    _principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.STORE_READ)),
    ],
    service: Annotated[StoreService, Depends(get_store_service)],
) -> StoreListResponse:
    return await service.list_all()


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    payload: CreateStoreRequest,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.STORE_MANAGE)),
    ],
    service: Annotated[StoreService, Depends(get_store_service)],
) -> StoreResponse:
    return await service.create(principal, payload, getattr(request.state, "trace_id", None))


@router.patch("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: str,
    payload: UpdateStoreRequest,
    request: Request,
    principal: Annotated[
        Principal,
        Depends(require_access(ModuleCode.ADMIN, Permission.STORE_MANAGE)),
    ],
    service: Annotated[StoreService, Depends(get_store_service)],
) -> StoreResponse:
    return await service.update(
        principal, store_id, payload, getattr(request.state, "trace_id", None)
    )
