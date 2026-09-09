from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Any

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline security headers for all responses."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        
        # Route-specific CSP for docs endpoint to allow Swagger UI CDN resources
        if request.url.path in ["/docs", "/redoc"]:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "frame-ancestors 'none'"
            )
        else:
            csp = "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        
        response.headers.setdefault("Content-Security-Policy", csp)
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=()",
        )
        response.headers.setdefault("Cache-Control", "no-store, no-cache, must-revalidate")

        if settings.APP_ENV == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response
