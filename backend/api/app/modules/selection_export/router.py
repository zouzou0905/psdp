from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse

from app.modules.authorization.dependencies import require_any_access
from app.modules.identity.domain import ModuleCode, Permission, Principal
from app.modules.selection_export.domain import (
    SelectionExportCreateRequest,
    SelectionExportResponse,
)
from app.modules.selection_export.service import SelectionExportService

router = APIRouter(prefix="/selection-exports", tags=["selection-exports"])

EXPORT_SELECTION = require_any_access(
    (ModuleCode.OPERATIONS, Permission.SELECTION_EXPORT),
    (ModuleCode.PROCUREMENT, Permission.SELECTION_EXPORT),
    (ModuleCode.PROCUREMENT, Permission.QUOTATION_EXPORT),
    (ModuleCode.ADMIN, Permission.SELECTION_EXPORT),
    (ModuleCode.ADMIN, Permission.QUOTATION_EXPORT),
)


def get_selection_export_service(request: Request) -> SelectionExportService:
    return cast(SelectionExportService, request.app.state.selection_export_service)


@router.post("", response_model=SelectionExportResponse, status_code=status.HTTP_201_CREATED)
async def create_selection_export(
    payload: SelectionExportCreateRequest,
    request: Request,
    principal: Annotated[Principal, Depends(EXPORT_SELECTION)],
    service: Annotated[SelectionExportService, Depends(get_selection_export_service)],
) -> SelectionExportResponse:
    return await service.create(
        principal, payload, getattr(request.state, "trace_id", None)
    )


@router.get("/{export_id}", response_model=SelectionExportResponse)
async def get_selection_export(
    export_id: UUID,
    principal: Annotated[Principal, Depends(EXPORT_SELECTION)],
    service: Annotated[SelectionExportService, Depends(get_selection_export_service)],
) -> SelectionExportResponse:
    return await service.get(principal, export_id)


@router.get("/{export_id}/download", response_class=FileResponse)
async def download_selection_export(
    export_id: UUID,
    principal: Annotated[Principal, Depends(EXPORT_SELECTION)],
    service: Annotated[SelectionExportService, Depends(get_selection_export_service)],
) -> FileResponse:
    downloadable = await service.download(principal, export_id)
    return FileResponse(
        downloadable.path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=downloadable.file_name,
        headers={"ETag": f'"sha256-{downloadable.checksum}"'},
    )
