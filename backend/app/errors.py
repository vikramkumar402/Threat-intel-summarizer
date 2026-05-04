"""Typed application errors with consistent JSON shape."""
from __future__ import annotations

from typing import Optional

import structlog
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger()


class AppError(Exception):
    """Base class for application-level errors."""

    code: str = "internal_error"
    status_code: int = 500
    message: str = "An internal error occurred."

    def __init__(self, message: Optional[str] = None, code: Optional[str] = None) -> None:
        super().__init__(message or self.message)
        if message:
            self.message = message
        if code:
            self.code = code


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404
    message = "Resource not found."


class UnauthorizedError(AppError):
    code = "unauthorized"
    status_code = 401
    message = "Authentication required."


class ForbiddenError(AppError):
    code = "forbidden"
    status_code = 403
    message = "You do not have permission to perform this action."


class ConflictError(AppError):
    code = "conflict"
    status_code = 409
    message = "Resource conflict."


class ValidationError(AppError):
    code = "validation_error"
    status_code = 400
    message = "Invalid request."


def _request_id(request: Request) -> Optional[str]:
    return getattr(request.state, "request_id", None)


def _payload(code: str, message: str, request: Request) -> dict:
    return {"code": code, "message": message, "request_id": _request_id(request)}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "app_error",
        code=exc.code,
        status=exc.status_code,
        path=request.url.path,
        request_id=_request_id(request),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_payload(exc.code, exc.message, request),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        429: "rate_limited",
    }.get(exc.status_code, "http_error")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    logger.warning(
        "http_exception",
        code=code,
        status=exc.status_code,
        path=request.url.path,
        request_id=_request_id(request),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_payload(code, message, request),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.info(
        "validation_error",
        path=request.url.path,
        errors=exc.errors(),
        request_id=_request_id(request),
    )
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Request payload failed validation.",
            "request_id": _request_id(request),
            "details": exc.errors(),
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        exc_info=True,
        path=request.url.path,
        request_id=_request_id(request),
    )
    return JSONResponse(
        status_code=500,
        content=_payload("internal_error", "An internal error occurred.", request),
    )
