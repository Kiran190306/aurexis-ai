from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
from typing import Any


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors globally."""

    async def dispatch(self, request: Request, call_next: Any) -> JSONResponse:
        try:
            response = await call_next(request)
            return response
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return JSONResponse(
                status_code=422,
                content={
                    "detail": "Validation error",
                    "errors": e.errors(),
                },
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Database error",
                    "message": "A database error occurred. Please try again later.",
                },
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                },
            )
