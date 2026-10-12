from typing import Any, Protocol, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str | None = None
    trace_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ErrorRecorder(Protocol):
    async def record_unexpected(self, exc: Exception, trace_id: str | None, path: str) -> None: ...


class ApplicationError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.headers = headers


def _context(request: Request) -> tuple[str | None, str | None]:
    return getattr(request.state, "request_id", None), getattr(request.state, "trace_id", None)


def _safe_validation_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Never echo request input or validator context, which may contain credentials."""

    return [
        {
            "loc": [str(part) for part in error["loc"]],
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id, trace_id = _context(request)
        body = ErrorResponse(
            error=ErrorDetail(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                request_id=request_id,
                trace_id=trace_id,
            )
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=body.model_dump(),
            headers=exc.headers,
        )

    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        request_id, trace_id = _context(request)
        body = ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                request_id=request_id,
                trace_id=trace_id,
            )
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id, trace_id = _context(request)
        body = ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_FAILED",
                message="Request validation failed",
                details=_safe_validation_errors(exc),
                request_id=request_id,
                trace_id=trace_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=body.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id, trace_id = _context(request)
        recorder = getattr(request.app.state, "error_recorder", None)
        if recorder is not None:
            try:
                await cast(ErrorRecorder, recorder).record_unexpected(
                    exc, trace_id, request.url.path
                )
            except Exception:
                pass
        body = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                request_id=request_id,
                trace_id=trace_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body.model_dump(),
        )
