from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.modules.authorization.dependencies import (
    SESSION_COOKIE_NAME,
    get_authentication_service,
    get_current_user,
)
from app.modules.identity.domain import (
    AccessContextResponse,
    LoginRequest,
    ModuleListResponse,
    Principal,
    default_landing,
    to_access_context,
)
from app.modules.identity.service import AuthenticationService
from app.modules.store.domain import StoreListResponse
from app.modules.store.router import get_store_service
from app.modules.store.service import StoreService

router = APIRouter(tags=["identity"])


@router.post(
    "/auth/login",
    response_model=AccessContextResponse,
    summary="Create an HttpOnly cookie session",
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> AccessContextResponse:
    result = await service.login(
        payload.username,
        payload.password.get_secret_value(),
        getattr(request.state, "trace_id", None),
    )
    settings = request.app.state.settings
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=result.session_token,
        expires=result.expires_at,
        max_age=settings.auth_session_ttl_minutes * 60,
        path="/",
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )
    return result.access_context


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Invalidate tokens")
async def logout(
    request: Request,
    principal: Annotated[Principal, Depends(get_current_user)],
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
) -> Response:
    await service.logout(principal, getattr(request.state, "trace_id", None))
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    settings = request.app.state.settings
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )
    return response


@router.get("/me", response_model=AccessContextResponse, summary="Get the authenticated user")
async def me(
    principal: Annotated[Principal, Depends(get_current_user)],
) -> AccessContextResponse:
    return to_access_context(principal)


@router.get(
    "/me/access-context",
    response_model=AccessContextResponse,
    summary="Get server-resolved authorization context",
)
async def access_context(
    principal: Annotated[Principal, Depends(get_current_user)],
) -> AccessContextResponse:
    return to_access_context(principal)


@router.get("/me/modules", response_model=ModuleListResponse)
async def my_modules(
    principal: Annotated[Principal, Depends(get_current_user)],
) -> ModuleListResponse:
    return ModuleListResponse(
        modules=sorted(principal.modules),
        default_landing=default_landing(principal.modules),
    )


@router.get("/me/stores", response_model=StoreListResponse)
async def my_stores(
    principal: Annotated[Principal, Depends(get_current_user)],
    service: Annotated[StoreService, Depends(get_store_service)],
) -> StoreListResponse:
    return await service.list_for_user(principal)
