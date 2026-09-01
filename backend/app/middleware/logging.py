from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import time
import uuid
from typing import Any
from app.observability import record_http_request


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    @staticmethod
    def _metric_path(request: Request) -> str:
        """Use the matched route template; never create a time series per ID."""
        route = request.scope.get("route")
        return getattr(route, "path", None) or "unmatched"

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Preserve caller-provided IDs so logs, traces, and downstream services
        # can be correlated. Never trust an empty or excessively large value.
        request_id = request.headers.get("X-Request-ID", "").strip()[:128] or str(uuid.uuid4())
        correlation_id = (
            request.headers.get("X-Correlation-ID", "").strip()[:128] or request_id
        )
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        # Log request
        start_time = time.time()
        logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
            correlation_id=correlation_id,
        ).info("Request started")

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.bind(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                correlation_id=correlation_id,
            ).error("Request failed")
            record_http_request(
                request.method, self._metric_path(request), 500, time.time() - start_time
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            correlation_id=correlation_id,
        ).info("Request completed")

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        record_http_request(
            request.method, self._metric_path(request), response.status_code, duration
        )

        return response  # type: ignore[no-any-return]
