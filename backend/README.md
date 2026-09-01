# Jarvis AI Backend

## Production readiness updates

The backend now includes:
- a fixed refresh-token flow that returns valid JWTs instead of a broken reference
- stricter configuration validation for production environments
- baseline security headers for all responses
- model import fixes that prevent startup failures caused by reserved SQLAlchemy attribute names

## Required runtime environment

Set the following before running in production:
- SECRET_KEY
- ADMIN_PASSWORD
- DATABASE_URL
- REDIS_URL
- CORS_ORIGINS
- ALLOWED_HOSTS

## Verification

Run the regression tests with:

```bash
uv run --python 3.11 pytest -q tests/unit/test_auth_refresh.py
```
