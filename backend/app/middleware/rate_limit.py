from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from loguru import logger
import time
from collections import defaultdict
from typing import Dict, Any
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        # Store rate limit data: {identifier: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next: Any) -> JSONResponse:
        # Get identifier (IP address or user ID if authenticated)
        identifier = self._get_identifier(request)

        # Check rate limit
        if not self._is_allowed(identifier):
            logger.warning(
                f"Rate limit exceeded",
                extra={"identifier": identifier, "path": request.url.path},
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                },
                headers={"Retry-After": "60"},
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(
            self._get_remaining_requests(identifier)
        )
        response.headers["X-RateLimit-Reset"] = str(self._get_reset_time(identifier))

        return response

    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting."""
        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    def _is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit."""
        now = time.time()
        
        # Clean up old entries periodically
        if now - self.last_cleanup > 60:
            self._cleanup_old_entries(now)
            self.last_cleanup = now

        # Get request history for this identifier
        request_history = self.requests[identifier]
        
        # Remove requests older than 1 minute
        request_history[:] = [req for req in request_history if now - req[0] < 60]
        
        # Check if under limit
        if len(request_history) >= settings.RATE_LIMIT_PER_MINUTE:
            return False
        
        # Add this request
        request_history.append((now, 1))
        return True

    def _cleanup_old_entries(self, now: float) -> None:
        """Clean up old entries from all identifiers."""
        for identifier in list(self.requests.keys()):
            self.requests[identifier][:] = [
                req for req in self.requests[identifier]
                if now - req[0] < 3600  # Keep entries for 1 hour
            ]
            # Remove empty identifiers
            if not self.requests[identifier]:
                del self.requests[identifier]

    def _get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for this identifier."""
        now = time.time()
        request_history = self.requests[identifier]
        request_history[:] = [req for req in request_history if now - req[0] < 60]
        return max(0, settings.RATE_LIMIT_PER_MINUTE - len(request_history))

    def _get_reset_time(self, identifier: str) -> int:
        """Get reset time for rate limit window."""
        now = time.time()
        request_history = self.requests[identifier]
        if not request_history:
            return int(now + 60)
        
        # Get oldest request in current window
        oldest_request = min(request_history, key=lambda x: x[0])
        return int(oldest_request[0] + 60)
