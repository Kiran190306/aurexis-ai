# RENDER BACKEND PRODUCTION CONFIGURATION

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 9 - Backend Production Configuration

---

## Executive Summary

Backend production configuration documented. Backend uses FastAPI with Uvicorn, Python 3.12. Must use Render's $PORT environment variable. Database and Redis URLs from Render services. Health checks at /health/ready. CORS configured for frontend domain. Authentication via JWT. Logging configured for JSON format. Prometheus metrics at /metrics (optional). No create_all in production (Alembic migrations required).

**Status**: ✅ BACKEND CONFIGURATION DOCUMENTED

---

## Backend Technology Stack

### Framework and Runtime

**Framework**: FastAPI 0.109.1
**Runtime**: Python 3.12
**Server**: Uvicorn 0.24.0
**Database**: PostgreSQL 15 with pgvector
**Cache**: Redis 7
**Async Framework**: SQLAlchemy 2.0 with asyncpg
**Migration Tool**: Alembic 1.13.0
**Task Queue**: Celery 5.3.4

### Production Server

**Server**: Uvicorn
**Workers**: 4 (configurable)
**Host**: 0.0.0.0
**Port**: $PORT (Render-provided)

---

## PORT Configuration

### Current Configuration

**Hardcoded Port**: 8000
```python
HOST: str = "0.0.0.0"
PORT: int = 8000
```

**Startup Command**:
```python
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Render Configuration

**Required Change**: Use $PORT environment variable

**Updated Startup Command**:
```python
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Render Configuration**:
```yaml
envVars:
  - key: PORT
    sync: false
    # Render provides PORT automatically
```

**Action Required**: Update startup command to use $PORT

---

## Startup Command

### Current Command

```python
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Render Command

```python
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Render Configuration**:
```yaml
startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Database Configuration

### Database URL

**Current Format**:
```python
DATABASE_URL = postgresql+asyncpg://user:pass@host:port/db
```

**Render Format**:
```python
DATABASE_URL = postgres://user:pass@host:port/db
```

**Conversion Required**: YES

### Render Configuration

**Option A**: Use Render DATABASE_URL directly
- SQLAlchemy may accept postgres:// format
- Test in development first

**Option B**: Convert to asyncpg format
- Replace `postgres://` with `postgresql+asyncpg://`
- Add to environment variables

**Option C**: Set custom DATABASE_URL
- Set DATABASE_URL in Render with asyncpg format
- Override Render-provided DATABASE_URL

**Recommendation**: Option C - Set custom DATABASE_URL with asyncpg format

**Render Configuration**:
```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: jarvis-postgres
      property: connectionString
    # Then manually convert to postgresql+asyncpg:// format
```

---

## Redis Configuration

### Redis URL

**Current Format**:
```python
REDIS_URL = redis://:${REDIS_PASSWORD}@redis:6379/0
```

**Render Format**:
```python
REDIS_URL = rediss://default:password@host:port
```

**Conversion Required**: YES

### Render Configuration

**Base URL** (from Render):
```python
REDIS_URL = rediss://default:password@host:port
```

**Application URLs**:
```python
# Database 0 (cache)
REDIS_URL = rediss://:password@host:port/0

# Database 1 (broker)
CELERY_BROKER_URL = rediss://:password@host:port/1

# Database 2 (result backend)
CELERY_RESULT_BACKEND = rediss://:password@host:port/2
```

**Render Configuration**:
```yaml
envVars:
  - key: REDIS_URL
    fromService:
      type: redis
      name: jarvis-redis
      property: connectionString
  - key: REDIS_PASSWORD
    fromService:
      type: redis
      name: jarvis-redis
      property: password
  - key: CELERY_BROKER_URL
    generateValue: true
    # Manually set to REDIS_URL with /1
  - key: CELERY_RESULT_BACKEND
    generateValue: true
    # Manually set to REDIS_URL with /2
```

---

## Health Checks

### Health Endpoints

**Liveness**: `/health/live`
```python
async def liveness_check() -> dict[str, str]:
    return {"status": "alive"}
```

**Readiness**: `/health/ready`
```python
async def readiness_check() -> JSONResponse:
    checks = {"database": "failed", "redis": "failed", "ai_engine": "failed"}
    # Check database, redis, ai_engine
    is_ready = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={"status": "ready" if is_ready else "not_ready", "checks": checks}
    )
```

**General**: `/health`
```python
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }
```

### Render Configuration

```yaml
healthCheckPath: /health/ready
```

**Notes**:
- Readiness check verifies database, redis, AI engine
- Liveness check verifies process is running
- General health check provides metadata

---

## CORS Configuration

### Current Configuration

```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080"
]
CORS_ALLOW_CREDENTIALS: bool = True
CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "X-Requested-With"]
```

### Render Configuration

```python
CORS_ORIGINS: List[str] = [
    "https://your-frontend.onrender.com"
]
```

**Render Configuration**:
```yaml
envVars:
  - key: CORS_ORIGINS
    sync: false
    value: https://your-frontend.onrender.com
```

**Action Required**: Set CORS_ORIGINS to frontend Render URL

---

## Authentication Configuration

### JWT Configuration

**Current Configuration**:
```python
SECRET_KEY: str = ""
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

### Render Configuration

**Required Secrets**:
```yaml
envVars:
  - key: SECRET_KEY
    generateValue: true
  - key: ALGORITHM
    value: HS256
  - key: ACCESS_TOKEN_EXPIRE_MINUTES
    value: 15
  - key: REFRESH_TOKEN_EXPIRE_DAYS
    value: 7
```

**Action Required**: Set SECRET_KEY in Render (generate strong random string)

---

## Admin Configuration

### Admin Account

**Current Configuration**:
```python
ADMIN_EMAIL: str = "admin@jarvis-ai.com"
ADMIN_PASSWORD: str = ""
```

### Render Configuration

```yaml
envVars:
  - key: ADMIN_EMAIL
    value: admin@jarvis-ai.com
  - key: ADMIN_PASSWORD
    generateValue: true
```

**Action Required**: Set ADMIN_PASSWORD in Render (generate strong password)

---

## Environment Configuration

### Application Environment

**Current Configuration**:
```python
APP_ENV: str = "development"
APP_DEBUG: bool = False
```

### Render Configuration

```yaml
envVars:
  - key: APP_ENV
    value: production
  - key: APP_DEBUG
    value: false
```

**Action Required**: Set APP_ENV to production

---

## Database Initialization

### Current Behavior

**Development/Testing**:
```python
if settings.APP_ENV in ["development", "testing"]:
    await init_db()
    logger.info("Database initialized via create_all()")
else:
    logger.info("Production mode - skipping create_all, relying on Alembic migrations")
```

**Production**:
- Skips create_all()
- Relies on Alembic migrations
- Migrations must run before backend starts

### Render Configuration

**Action Required**: Ensure migrations run before backend starts (Phase 10)

---

## Logging Configuration

### Current Configuration

```python
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "json"
LOG_DIR: str = "./logs"
LOG_ROTATION: str = "500 MB"
LOG_RETENTION: str = "30 days"
```

### Render Configuration

```yaml
envVars:
  - key: LOG_LEVEL
    value: INFO
  - key: LOG_FORMAT
    value: json
  - key: LOG_DIR
    value: ./logs
  - key: LOG_ROTATION
    value: 500 MB
  - key: LOG_RETENTION
    value: 30 days
```

**Notes**:
- JSON format for structured logging
- Render provides log aggregation
- Logs available in Render dashboard

---

## Monitoring Configuration

### Prometheus Metrics

**Current Configuration**:
```python
PROMETHEUS_ENABLED: bool = True
PROMETHEUS_PORT: int = 9090
```

**Metrics Endpoint**: `/metrics`

### Render Configuration

```yaml
envVars:
  - key: PROMETHEUS_ENABLED
    value: true
  - key: PROMETHEUS_PORT
    value: 9090
```

**Notes**:
- Metrics endpoint available but optional
- Render provides native metrics
- Can use external Prometheus if needed

### OpenTelemetry

**Current Configuration**:
```python
OTEL_ENABLED: bool = True
OTEL_SERVICE_NAME: str = "jarvis-backend"
OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
```

### Render Configuration

```yaml
envVars:
  - key: OTEL_ENABLED
    value: true
  - key: OTEL_SERVICE_NAME
    value: jarvis-backend
  - key: OTEL_EXPORTER_OTLP_ENDPOINT
    sync: false
    # Set if using external OTLP endpoint
```

**Notes**:
- Optional external observability
- Render provides native metrics and logs

---

## Trusted Host Middleware

### Current Configuration

```python
if settings.APP_ENV == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
```

### Render Configuration

```yaml
envVars:
  - key: ALLOWED_HOSTS
    sync: false
    value: your-backend.onrender.com
```

**Action Required**: Set ALLOWED_HOSTS to backend Render domain

---

## Rate Limiting Configuration

### Current Configuration

```python
RATE_LIMIT_ENABLED: bool = True
RATE_LIMIT_PER_MINUTE: int = 60
RATE_LIMIT_PER_HOUR: int = 1000
RATE_LIMIT_PER_DAY: int = 10000
```

### Render Configuration

```yaml
envVars:
  - key: RATE_LIMIT_ENABLED
    value: true
  - key: RATE_LIMIT_PER_MINUTE
    value: 60
  - key: RATE_LIMIT_PER_HOUR
    value: 1000
  - key: RATE_LIMIT_PER_DAY
    value: 10000
```

**Notes**:
- Rate limiting middleware enabled
- Configurable limits
- Can be disabled if needed

---

## LLM Configuration

### OpenAI

**Current Configuration**:
```python
OPENAI_API_KEY: Optional[str] = None
OPENAI_MODEL: str = "gpt-4-turbo-preview"
OPENAI_TEMPERATURE: float = 0.7
OPENAI_MAX_TOKENS: int = 4096
OPENAI_TIMEOUT: int = 60
```

### Render Configuration

```yaml
envVars:
  - key: OPENAI_API_KEY
    sync: false
  - key: OPENAI_MODEL
    value: gpt-4-turbo-preview
  - key: OPENAI_TEMPERATURE
    value: 0.7
  - key: OPENAI_MAX_TOKENS
    value: 4096
  - key: OPENAI_TIMEOUT
    value: 60
```

**Action Required**: Set OPENAI_API_KEY if using OpenAI

### Anthropic

**Current Configuration**:
```python
ANTHROPIC_API_KEY: Optional[str] = None
ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
ANTHROPIC_TEMPERATURE: float = 0.7
ANTHROPIC_MAX_TOKENS: int = 4096
ANTHROPIC_TIMEOUT: int = 60
```

### Render Configuration

```yaml
envVars:
  - key: ANTHROPIC_API_KEY
    sync: false
  - key: ANTHROPIC_MODEL
    value: claude-3-opus-20240229
  - key: ANTHROPIC_TEMPERATURE
    value: 0.7
  - key: ANTHROPIC_MAX_TOKENS
    value: 4096
  - key: ANTHROPIC_TIMEOUT
    value: 60
```

**Action Required**: Set ANTHROPIC_API_KEY if using Anthropic

### Default LLM Provider

**Current Configuration**:
```python
DEFAULT_LLM_PROVIDER: Optional[str] = None
```

### Render Configuration

```yaml
envVars:
  - key: DEFAULT_LLM_PROVIDER
    sync: false
    value: openai
```

**Action Required**: Set DEFAULT_LLM_PROVIDER if using LLM features

---

## Required Changes Summary

### Critical Changes

1. **PORT**: Change from hardcoded 8000 to $PORT
2. **DATABASE_URL**: Convert to asyncpg format
3. **REDIS_URL**: Add database numbers (/0, /1, /2)
4. **CORS_ORIGINS**: Set to frontend Render URL
5. **ALLOWED_HOSTS**: Set to backend Render URL
6. **SECRET_KEY**: Set in Render
7. **ADMIN_PASSWORD**: Set in Render
8. **APP_ENV**: Set to production

### Optional Changes

9. **LLM API Keys**: Set if using LLM features
10. **DEFAULT_LLM_PROVIDER**: Set if using LLM features
11. **OTEL_EXPORTER_OTLP_ENDPOINT**: Set if using external observability

---

## Dockerfile Compatibility

### Current Dockerfile

**Base Image**: python:3.12-slim
**Runtime Target**: Non-root user (appuser)
**Exposed Port**: 8000
**Health Check**: curl http://localhost:8000/health/live
**Startup Command**: uvicorn app.main:app --host 0.0.0.0 --port 8000

### Render Compatibility

**Status**: ✅ COMPATIBLE

**Required Changes**:
- Update startup command to use $PORT
- Update health check path to /health/ready
- No other changes required

---

## Sign-Off

**Backend Configuration Date**: 2026-09-01
**Backend Configuration By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 9 - Backend Production Configuration
**Status**: ✅ BACKEND CONFIGURATION DOCUMENTED

**Overall Assessment**: Backend uses FastAPI with Uvicorn, Python 3.12. Must use Render's $PORT environment variable. Database and Redis URLs from Render services with format conversion. Health checks at /health/ready. CORS configured for frontend domain. Authentication via JWT. Logging configured for JSON format. Prometheus metrics at /metrics (optional). No create_all in production (Alembic migrations required).

**Required Changes**:
- Update startup command to use $PORT
- Convert DATABASE_URL to asyncpg format
- Add database numbers to REDIS_URL (/0, /1, /2)
- Set CORS_ORIGINS to frontend Render URL
- Set ALLOWED_HOSTS to backend Render URL
- Set SECRET_KEY in Render
- Set ADMIN_PASSWORD in Render
- Set APP_ENV to production

**Next Phase**: Phase 10 - Alembic Migration Strategy
