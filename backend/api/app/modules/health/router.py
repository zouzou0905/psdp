from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel

from app.modules.health.service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    status: Literal["ok", "unhealthy"]
    checks: dict[str, Literal["up", "down"]]


def get_health_service(request: Request) -> HealthService:
    return cast(HealthService, request.app.state.health_service)


@router.get("/live", response_model=LivenessResponse, summary="Process liveness")
async def liveness() -> LivenessResponse:
    return LivenessResponse()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Dependency readiness",
    responses={503: {"model": ReadinessResponse}},
)
async def readiness(
    response: Response,
    service: Annotated[HealthService, Depends(get_health_service)],
) -> ReadinessResponse:
    check = await service.readiness()
    if not check.healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ok" if check.healthy else "unhealthy",
        checks={"database": check.database},
    )
