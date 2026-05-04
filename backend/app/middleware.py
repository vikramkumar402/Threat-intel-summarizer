"""HTTP middleware (request_id + structured logging context)."""
from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID, bind structlog context, and emit access logs."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.error("request_failed", duration_ms=round(duration_ms, 2), exc_info=True)
            raise

        duration_ms = (time.perf_counter() - started) * 1000
        response.headers["x-request-id"] = request_id

        log = logger.bind(status=response.status_code, duration_ms=round(duration_ms, 2))
        if response.status_code >= 500:
            log.error("request_completed")
        elif response.status_code >= 400:
            log.warning("request_completed")
        else:
            log.info("request_completed")
        return response
