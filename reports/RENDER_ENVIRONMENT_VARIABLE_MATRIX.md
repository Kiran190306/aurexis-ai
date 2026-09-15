# RENDER ENVIRONMENT VARIABLE MATRIX

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 6 - Environment Variable Matrix

---

## Executive Summary

Environment variable matrix completed. All required environment variables documented and categorized. Critical secrets identified (SECRET_KEY, ADMIN_PASSWORD, REDIS_PASSWORD, LLM API keys). Database and Redis URLs will be provided by Render. All secrets must be configured in Render environment, never in code.

**Status**: ✅ ENVIRONMENT VARIABLE MATRIX COMPLETE

---

## Environment Variable Categories

### REQUIRED
Variables that must be set for the application to function in production.

### OPTIONAL
Variables that are optional but may be needed for specific features.

### SECRET
Variables that contain sensitive information and must never be committed to code.

### PUBLIC
Variables that can be safely exposed (e.g., in frontend builds).

### INTERNAL
Variables used for internal configuration.

### LLM
Variables related to LLM provider configuration.

### DATABASE
Variables related to database configuration.

### REDIS
Variables related to Redis configuration.

### CELERY
Variables related to Celery configuration.

### FRONTEND
Variables related to frontend configuration.

### AUTH
Variables related to authentication.

### MONITORING
Variables related to monitoring and observability.

---

## Environment Variable Matrix

### Application Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| APP_ENV | YES | NO | INTERNAL | Backend | All Services | NO | Must be "production" |
| APP_NAME | NO | NO | INTERNAL | Backend | Backend | YES | "Jarvis AI" |
| APP_VERSION | NO | NO | INTERNAL | Backend | Backend | YES | "1.0.0" |
| APP_URL | NO | NO | INTERNAL | Backend | Backend | YES | Backend URL |
| API_V1_PREFIX | NO | NO | INTERNAL | Backend | Backend | YES | "/api/v1" |
| ALLOWED_HOSTS | NO | NO | INTERNAL | Backend | Backend | NO | Set to production domain |
| HOST | NO | NO | INTERNAL | Backend | Backend | NO | "0.0.0.0" |
| PORT | YES | NO | INTERNAL | Backend | Backend | NO | Provided by Render ($PORT) |
| WORKERS | NO | NO | INTERNAL | Backend | Backend | YES | 4 |
| RELOAD | NO | NO | INTERNAL | Backend | Backend | NO | False in production |

### Database Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| DATABASE_URL | YES | YES | DATABASE | Backend | All Services | NO | Provided by Render PostgreSQL |
| DATABASE_POOL_SIZE | NO | NO | DATABASE | Backend | All Services | YES | 20 |
| DATABASE_MAX_OVERFLOW | NO | NO | DATABASE | Backend | All Services | YES | 10 |
| DATABASE_ECHO | NO | NO | DATABASE | Backend | All Services | NO | False in production |

### Redis Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| REDIS_URL | YES | YES | REDIS | Backend | All Services | NO | Provided by Render Redis, add /0 |
| REDIS_PASSWORD | YES | YES | REDIS | Backend | All Services | NO | Provided by Render Redis |
| REDIS_POOL_SIZE | NO | NO | REDIS | Backend | All Services | YES | 10 |
| REDIS_MAX_CONNECTIONS | NO | NO | REDIS | Backend | All Services | YES | 50 |

### Celery Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| CELERY_BROKER_URL | YES | YES | CELERY | Backend | Worker, Beat | NO | Redis URL with /1 |
| CELERY_RESULT_BACKEND | YES | YES | CELERY | Backend | Worker, Beat | NO | Redis URL with /2 |
| CELERY_BROKER_URL | YES | YES | CELERY | Flower | Flower | NO | Redis URL with /1 |
| CELERY_RESULT_BACKEND | YES | YES | CELERY | Flower | Flower | NO | Redis URL with /2 |
| CELERY_TASK_TRACKED | NO | NO | CELERY | Backend | Worker, Beat | YES | True |
| CELERY_TASK_TIME_LIMIT | NO | NO | CELERY | Backend | Worker, Beat | YES | 3600 |

### Security Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| SECRET_KEY | YES | YES | SECRET | Backend | All Services | NO | JWT signing key |
| ALGORITHM | NO | NO | SECRET | Backend | All Services | YES | "HS256" |
| ACCESS_TOKEN_EXPIRE_MINUTES | NO | NO | SECRET | Backend | Backend | YES | 15 |
| REFRESH_TOKEN_EXPIRE_DAYS | NO | NO | SECRET | Backend | Backend | YES | 7 |
| PASSWORD_MIN_LENGTH | NO | NO | SECRET | Backend | Backend | YES | 8 |
| ADMIN_PASSWORD | YES | YES | SECRET | Backend | All Services | NO | Admin account password |
| ADMIN_EMAIL | NO | NO | SECRET | Backend | Backend | YES | "admin@jarvis-ai.com" |

### CORS Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| CORS_ORIGINS | YES | NO | INTERNAL | Backend | Backend | NO | Frontend URL(s) |
| CORS_ALLOW_CREDENTIALS | NO | NO | INTERNAL | Backend | Backend | YES | True |
| CORS_ALLOW_METHODS | NO | NO | INTERNAL | Backend | Backend | YES | GET, POST, PUT, PATCH, DELETE, OPTIONS |
| CORS_ALLOW_HEADERS | NO | NO | INTERNAL | Backend | Backend | YES | Authorization, Content-Type, X-Requested-With |

### Rate Limiting Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| RATE_LIMIT_ENABLED | NO | NO | INTERNAL | Backend | Backend | YES | True |
| RATE_LIMIT_PER_MINUTE | NO | NO | INTERNAL | Backend | Backend | YES | 60 |
| RATE_LIMIT_PER_HOUR | NO | NO | INTERNAL | Backend | Backend | YES | 1000 |
| RATE_LIMIT_PER_DAY | NO | NO | INTERNAL | Backend | Backend | YES | 10000 |

### LLM Configuration - OpenAI

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| OPENAI_API_KEY | OPTIONAL | YES | LLM | Backend | All Services | NO | OpenAI API key |
| OPENAI_ORGANIZATION | NO | YES | LLM | Backend | All Services | NO | OpenAI organization ID |
| OPENAI_MODEL | NO | NO | LLM | Backend | All Services | YES | "gpt-4o-mini" |
| OPENAI_TEMPERATURE | NO | NO | LLM | Backend | All Services | YES | 0.7 |
| OPENAI_MAX_TOKENS | NO | NO | LLM | Backend | All Services | YES | 4096 |
| OPENAI_TIMEOUT | NO | NO | LLM | Backend | All Services | YES | 60 |

### LLM Configuration - Anthropic

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| ANTHROPIC_API_KEY | OPTIONAL | YES | LLM | Backend | All Services | NO | Anthropic API key |
| ANTHROPIC_MODEL | NO | NO | LLM | Backend | All Services | YES | "claude-3-opus-20240229" |
| ANTHROPIC_TEMPERATURE | NO | NO | LLM | Backend | All Services | YES | 0.7 |
| ANTHROPIC_MAX_TOKENS | NO | NO | LLM | Backend | All Services | YES | 4096 |
| ANTHROPIC_TIMEOUT | NO | NO | LLM | Backend | All Services | YES | 60 |

### LLM Configuration - Google

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| GOOGLE_API_KEY | OPTIONAL | YES | LLM | Backend | All Services | NO | Google API key |
| GOOGLE_MODEL | NO | NO | LLM | Backend | All Services | YES | "gemini-pro" |
| GOOGLE_TEMPERATURE | NO | NO | LLM | Backend | All Services | YES | 0.7 |
| GOOGLE_MAX_TOKENS | NO | NO | LLM | Backend | All Services | YES | 4096 |
| GOOGLE_TIMEOUT | NO | NO | LLM | Backend | All Services | YES | 60 |

### Default LLM Provider

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| DEFAULT_LLM_PROVIDER | NO | NO | LLM | Backend | All Services | YES | "openai" or "anthropic" |

### ChromaDB Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| CHROMA_PERSIST_DIRECTORY | NO | NO | INTERNAL | Backend | All Services | YES | "./data/chroma" |
| CHROMA_COLLECTION_NAME | NO | NO | INTERNAL | Backend | All Services | YES | "jarvis_memory" |
| CHROMA_EMBEDDING_MODEL | NO | NO | INTERNAL | Backend | All Services | YES | "all-MiniLM-L6-v2" |

### File Storage Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| UPLOAD_DIR | NO | NO | INTERNAL | Backend | All Services | YES | "./data/uploads" |
| MAX_UPLOAD_SIZE | NO | NO | INTERNAL | Backend | All Services | YES | 104857600 (100MB) |
| ALLOWED_FILE_TYPES | NO | NO | INTERNAL | Backend | All Services | YES | pdf, doc, docx, txt, md, json, csv, xlsx, pptx, png, jpg, jpeg, gif, bmp, webp |

### Logging Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| LOG_LEVEL | NO | NO | INTERNAL | Backend | All Services | YES | "INFO" |
| LOG_FORMAT | NO | NO | INTERNAL | Backend | All Services | YES | "json" |
| LOG_DIR | NO | NO | INTERNAL | Backend | All Services | YES | "./logs" |
| LOG_ROTATION | NO | NO | INTERNAL | Backend | All Services | YES | "500 MB" |
| LOG_RETENTION | NO | NO | INTERNAL | Backend | All Services | YES | "30 days" |

### Monitoring Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| PROMETHEUS_ENABLED | NO | NO | MONITORING | Backend | Backend | YES | True |
| PROMETHEUS_PORT | NO | NO | MONITORING | Backend | Backend | YES | 9090 |
| SENTRY_DSN | OPTIONAL | YES | MONITORING | Backend | All Services | NO | Sentry DSN |
| SENTRY_ENVIRONMENT | NO | NO | MONITORING | Backend | All Services | YES | "production" |
| SENTRY_TRACES_SAMPLE_RATE | NO | NO | MONITORING | Backend | All Services | YES | 1.0 |
| OTEL_ENABLED | NO | NO | MONITORING | Backend | All Services | YES | True |
| OTEL_SERVICE_NAME | NO | NO | MONITORING | Backend | All Services | YES | "jarvis-backend" |
| OTEL_EXPORTER_OTLP_ENDPOINT | OPTIONAL | YES | MONITORING | Backend | All Services | NO | OTLP endpoint |

### Email Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| SMTP_HOST | NO | NO | INTERNAL | Backend | All Services | YES | "smtp.gmail.com" |
| SMTP_PORT | NO | NO | INTERNAL | Backend | All Services | YES | 587 |
| SMTP_USER | OPTIONAL | YES | SECRET | Backend | All Services | NO | SMTP username |
| SMTP_PASSWORD | OPTIONAL | YES | SECRET | Backend | All Services | NO | SMTP password |
| SMTP_FROM | NO | NO | INTERNAL | Backend | All Services | YES | "noreply@jarvis-ai.com" |
| SMTP_TLS | NO | NO | INTERNAL | Backend | All Services | YES | True |

### OAuth2 Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| GOOGLE_OAUTH_CLIENT_ID | OPTIONAL | YES | SECRET | Backend | Backend | NO | Google OAuth client ID |
| GOOGLE_OAUTH_CLIENT_SECRET | OPTIONAL | YES | SECRET | Backend | Backend | NO | Google OAuth client secret |
| GOOGLE_OAUTH_REDIRECT_URI | NO | NO | SECRET | Backend | Backend | NO | OAuth redirect URI |
| GITHUB_OAUTH_CLIENT_ID | OPTIONAL | YES | SECRET | Backend | Backend | NO | GitHub OAuth client ID |
| GITHUB_OAUTH_CLIENT_SECRET | OPTIONAL | YES | SECRET | Backend | Backend | NO | GitHub OAuth client secret |
| GITHUB_OAUTH_REDIRECT_URI | NO | NO | SECRET | Backend | Backend | NO | OAuth redirect URI |

### Frontend Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| VITE_API_URL | YES | NO | PUBLIC | Frontend | Frontend | NO | Backend public URL |
| PORT | NO | NO | INTERNAL | Frontend | Frontend | NO | 80 (internal) |

### Grafana Configuration

| Name | Required? | Secret? | Category | Used By | Render Service | Default Allowed? | Notes |
|------|-----------|---------|----------|---------|----------------|-----------------|-------|
| GRAFANA_ADMIN_USER | NO | NO | SECRET | Grafana | Grafana | YES | "admin" |
| GRAFANA_ADMIN_PASSWORD | YES | YES | SECRET | Grafana | Grafana | NO | Grafana admin password |

---

## Critical Secrets

### Must Be Configured in Render

1. **SECRET_KEY** - JWT signing key
2. **ADMIN_PASSWORD** - Admin account password
3. **REDIS_PASSWORD** - Redis authentication
4. **DATABASE_URL** - PostgreSQL connection (provided by Render)
5. **REDIS_URL** - Redis connection (provided by Render)
6. **CELERY_BROKER_URL** - Celery broker
7. **CELERY_RESULT_BACKEND** - Celery result backend

### Optional LLM Secrets

1. **OPENAI_API_KEY** - OpenAI API key (if using OpenAI)
2. **ANTHROPIC_API_KEY** - Anthropic API key (if using Anthropic)
3. **GOOGLE_API_KEY** - Google API key (if using Google)

---

## Render-Specific Variables

### Provided by Render

- **PORT** - Web service port
- **DATABASE_URL** - PostgreSQL connection string
- **REDIS_URL** - Redis connection string
- **REDIS_PASSWORD** - Redis password

### Must Be Set Manually

- **SECRET_KEY**
- **ADMIN_PASSWORD**
- **CORS_ORIGINS** (frontend URL)
- **VITE_API_URL** (backend URL)
- **LLM API keys** (if using LLM features)

---

## Sign-Off

**Environment Variable Matrix Date**: 2026-09-01
**Environment Variable Matrix By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 6 - Environment Variable Matrix
**Status**: ✅ ENVIRONMENT VARIABLE MATRIX COMPLETE

**Overall Assessment**: All environment variables documented and categorized. Critical secrets identified (SECRET_KEY, ADMIN_PASSWORD, REDIS_PASSWORD, LLM API keys). Database and Redis URLs provided by Render. All secrets must be configured in Render environment, never in code. Frontend requires VITE_API_URL for backend communication.

**Next Phase**: Phase 7 - Production Secrets Configuration
