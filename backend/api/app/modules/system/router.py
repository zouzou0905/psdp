from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.config import Settings

router = APIRouter(prefix="/system", tags=["system"])


class SystemInfoResponse(BaseModel):
    name: str
    version: str
    environment: str
    api_version: str = "v1"


def get_runtime_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


@router.get("/info", response_model=SystemInfoResponse, summary="Get safe runtime metadata")
async def system_info(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> SystemInfoResponse:
    return SystemInfoResponse(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
