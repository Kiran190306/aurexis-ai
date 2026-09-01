# RENDER SERVICE ARCHITECTURE

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 2 - Determine Final Render Service Architecture

---

## Executive Summary

Final Render service architecture defined. The architecture uses Render-native services for PostgreSQL and Redis, Docker-based web services for frontend and backend, and worker services for Celery. Custom monitoring (Prometheus, Grafana, Flower) is deferred in favor of Render-native observability. This approach minimizes cost while preserving all required functionality.

**Status**: ✅ ARCHITECTURE DEFINED

---

## Architecture Overview

### Conceptual Architecture

```
                  INTERNET
                     |
                     v
              Render HTTPS
                     |
              +------+------+
              |             |
              v             v
         Frontend        Backend
         Web Service     Web Service
         (nginx)         (FastAPI)
              |             |
              |        +----+----+
              |        |         |
              |        v         v
              |    PostgreSQL   Redis
              |    (Render)     (Render)
              |        |
              |        |
              |        +----+
              |             |
              |          Celery
              |          Worker
              |          (Render)
              |
              +----------------
                     |
                     v
              Celery Beat
              (Render Worker)
```

---

## Render Services

### 1. Frontend Web Service

**Service Type**: Web Service (Docker)

**Purpose**: Serve React SPA and proxy API requests to backend

**Dockerfile**: `deploy/docker/frontend/Dockerfile`

**Build Context**: `frontend`

**Port**: 80 (internal), 443 (Render HTTPS)

**Environment Variables**:
- VITE_API_URL: Backend public URL (for direct API calls if needed)
- (Other VITE_* variables if required)

**Health Check**: `/health`

**Startup Command**: `nginx -g daemon off;`

**Notes**:
- Uses nginx for SPA routing
- API proxy to backend (optional, can call backend directly)
- HTTPS handled by Render
- Static assets served efficiently

**Cost**: Free tier (Standard) or Basic ($7/month)

---

### 2. Backend Web Service

**Service Type**: Web Service (Docker)

**Purpose**: FastAPI backend, authentication, API endpoints, AI functionality

**Dockerfile**: `deploy/docker/backend/Dockerfile`

**Build Context**: `backend`

**Port**: $PORT (Render-provided)

**Environment Variables**:
- APP_ENV: production
- DATABASE_URL: Render PostgreSQL URL
- REDIS_URL: Render Redis URL
- REDIS_PASSWORD: Render Redis password
- CELERY_BROKER_URL: Redis URL with database 1
- CELERY_RESULT_BACKEND: Redis URL with database 2
- SECRET_KEY: (secret)
- ADMIN_PASSWORD: (secret)
- OPENAI_API_KEY: (optional)
- ANTHROPIC_API_KEY: (optional)
- GOOGLE_API_KEY: (optional)
- CORS_ORIGINS: Frontend URL

**Health Check**: `/health/ready`

**Startup Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Notes**:
- Must use $PORT environment variable
- Depends on PostgreSQL and Redis
- Migration must run before backend starts
- Prometheus metrics endpoint available but optional

**Cost**: Standard ($25/month) or Pro ($70/month) depending on load

---

### 3. PostgreSQL Database

**Service Type**: PostgreSQL (Render Managed)

**Purpose**: Primary database with pgvector extension

**Version**: PostgreSQL 15 (with pgvector)

**Configuration**:
- Database name: jarvis
- User: jarvis
- Extensions: pgvector (required)

**Environment Variables**:
- DATABASE_URL: Provided by Render
- POSTGRES_USER: Provided by Render
- POSTGRES_PASSWORD: Provided by Render
- POSTGRES_DB: Provided by Render

**Notes**:
- Render PostgreSQL includes pgvector extension
- Automatic backups provided by Render
- Automatic failover
- Private network connectivity

**Cost**: Free tier (90 days) or Standard ($7/month) or Pro ($50/month)

---

### 4. Redis Cache

**Service Type**: Redis (Render Managed)

**Purpose**: Cache, Celery broker, Celery result backend

**Configuration**:
- Authentication: Enabled
- Databases: 0 (cache), 1 (broker), 2 (result backend)

**Environment Variables**:
- REDIS_URL: Provided by Render
- REDIS_PASSWORD: Provided by Render

**Notes**:
- Private network connectivity
- Authentication required
- Multiple databases supported
- Automatic persistence

**Cost**: Free tier (90 days) or Standard ($15/month)

---

### 5. Celery Worker

**Service Type**: Worker Service (Docker)

**Purpose**: Background task processing

**Dockerfile**: `deploy/docker/backend/Dockerfile`

**Build Context**: `backend`

**Environment Variables**:
- Same as backend web service
- CELERY_BROKER_URL: Redis URL with database 1
- CELERY_RESULT_BACKEND: Redis URL with database 2

**Health Check**: Celery inspect ping (via Render worker health check)

**Startup Command**: `celery -A app.worker worker --loglevel=info`

**Notes**:
- Processes background tasks
- Depends on backend, PostgreSQL, Redis
- Auto-scales based on queue size
- Separate from web service

**Cost**: Standard ($25/month) or Pro ($70/month) depending on load

---

### 6. Celery Beat

**Service Type**: Worker Service (Docker)

**Purpose**: Scheduled task execution

**Dockerfile**: `deploy/docker/backend/Dockerfile`

**Build Context**: `backend`

**Environment Variables**:
- Same as backend web service
- CELERY_BROKER_URL: Redis URL with database 1
- CELERY_RESULT_BACKEND: Redis URL with database 2

**Startup Command**: `celery -A app.worker beat --loglevel=info`

**Notes**:
- Singleton service (only one instance)
- Runs scheduled tasks (cleanup, etc.)
- Depends on backend, PostgreSQL, Redis

**Cost**: Standard ($25/month) - can use smaller instance

---

### 7. Migration Job

**Service Type**: Cron Job (One-time or Pre-deploy)

**Purpose**: Run Alembic database migrations

**Dockerfile**: `deploy/docker/backend/Dockerfile`

**Build Context**: `backend`

**Environment Variables**:
- DATABASE_URL: Render PostgreSQL URL
- (Other database-related variables)

**Command**: `alembic upgrade head`

**Schedule**: One-time (manual trigger) or pre-deploy hook

**Notes**:
- Must run before backend starts
- Can be triggered manually via Render dashboard
- Alternative: Use Render pre-deploy command

**Cost**: Included in backend build (no additional cost)

---

## Deferred Services

### Monitoring Services (Deferred)

**Reason**: Render provides native observability

**Deferred Services**:
- Prometheus
- Grafana
- Flower

**Alternative**: Use Render native metrics and logs

**Notes**:
- Can be added later if needed
- Would require additional cost
- Would require authentication/protection

---

## Service Dependencies

### Dependency Graph

```
Migration Job
    ↓
PostgreSQL
    ↓
Backend Web Service ←→ Redis
    ↓                    ↓
Celery Worker ←→ Celery Beat
    ↓
Frontend Web Service
```

### Startup Order

1. PostgreSQL (Render managed, always available)
2. Redis (Render managed, always available)
3. Migration Job (manual trigger or pre-deploy)
4. Backend Web Service
5. Celery Worker
6. Celery Beat
7. Frontend Web Service

---

## Network Connectivity

### Private Network

- PostgreSQL: Private (Render internal)
- Redis: Private (Render internal)
- Backend: Public (via Render HTTPS)
- Frontend: Public (via Render HTTPS)
- Celery Worker: Private (Render internal)
- Celery Beat: Private (Render internal)

### Service Communication

- Frontend → Backend: Public HTTPS
- Backend → PostgreSQL: Private network
- Backend → Redis: Private network
- Celery Worker → PostgreSQL: Private network
- Celery Worker → Redis: Private network
- Celery Worker → Backend: Private network (if needed)

---

## Cost Summary

### Monthly Cost Estimate (Standard Tier)

| Service | Cost | Notes |
|---------|------|-------|
| Frontend Web Service | $7 | Basic tier |
| Backend Web Service | $25 | Standard tier |
| PostgreSQL | $7 | Standard tier |
| Redis | $15 | Standard tier |
| Celery Worker | $25 | Standard tier |
| Celery Beat | $7 | Basic tier |
| **Total** | **$86/month** | Standard tier |

### Monthly Cost Estimate (Free Tier - 90 days)

| Service | Cost | Notes |
|---------|------|-------|
| Frontend Web Service | $0 | Free tier |
| Backend Web Service | $0 | Free tier |
| PostgreSQL | $0 | Free tier (90 days) |
| Redis | $0 | Free tier (90 days) |
| Celery Worker | $0 | Free tier |
| Celery Beat | $0 | Free tier |
| **Total** | **$0/month** | Free tier (90 days) |

### Cost Optimization

**Options**:
1. Use free tier for initial deployment (90 days)
2. Scale down Celery Beat to Basic tier ($7)
3. Use smaller instance sizes if load permits
4. Consider combining Celery Worker and Beat (not recommended)

**Recommendation**: Start with free tier, scale to Standard as needed

---

## Security Considerations

### Private Services

- PostgreSQL: Private network only
- Redis: Private network only
- Celery Worker: Private network only
- Celery Beat: Private network only

### Public Services

- Frontend: Public HTTPS
- Backend: Public HTTPS (can be restricted via CORS)

### Authentication

- Redis: Password authentication (REDIS_PASSWORD)
- PostgreSQL: Password authentication (Render-managed)
- Backend: JWT authentication
- Frontend: Cookie/token-based authentication

### Secrets

All secrets configured in Render environment:
- SECRET_KEY
- ADMIN_PASSWORD
- REDIS_PASSWORD
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GOOGLE_API_KEY

---

## Migration Strategy

### Option A: Pre-deploy Command (Preferred)

**Method**: Use Render pre-deploy command for backend service

**Command**: `alembic upgrade head`

**Pros**:
- Automatic
- Runs before backend starts
- No manual intervention

**Cons**:
- May not be available in all Render plans

### Option B: One-time Job (Alternative)

**Method**: Create one-time cron job for migrations

**Command**: `alembic upgrade head`

**Pros**:
- Manual control
- Can be retried if fails
- Independent of backend deployment

**Cons**:
- Manual intervention required
- Must remember to run

### Option C: Manual Shell (Fallback)

**Method**: Run migrations via Render shell

**Command**: `alembic upgrade head`

**Pros**:
- Full control
- Can inspect state

**Cons**:
- Manual intervention required
- Not automated

**Recommendation**: Use Option A (pre-deploy) if available, otherwise Option B (one-time job)

---

## Monitoring Strategy

### Render Native Observability

**Metrics**:
- CPU usage
- Memory usage
- Response time
- Error rate
- Request rate

**Logs**:
- Application logs
- Access logs
- Error logs

**Alerts**:
- Service down
- High error rate
- High response time

### Application Metrics (Optional)

**Backend**: `/metrics` endpoint (Prometheus format)
- Can be used with external monitoring
- Optional, not required

### Deferred Monitoring

**Deferred**:
- Prometheus service
- Grafana service
- Flower service

**Reason**: Render provides sufficient observability for initial deployment

---

## Backup Strategy

### Render Automated Backups

**PostgreSQL**:
- Daily automated backups
- Point-in-time recovery
- 7-day retention (Standard tier)
- 30-day retention (Pro tier)

**Redis**:
- Automatic persistence
- No separate backup needed

### Custom Backups (Optional)

**Backup Script**: Adapt `scripts/production_backup.ps1` for Render

**Method**:
- Use Render PostgreSQL connection
- Run pg_dump via Render shell or cron job
- Store backups externally (S3, etc.)

**Recommendation**: Use Render automated backups initially, add custom backups if needed

---

## Scaling Strategy

### Horizontal Scaling

**Backend Web Service**:
- Auto-scale based on request rate
- Minimum: 1 instance
- Maximum: 10 instances

**Celery Worker**:
- Auto-scale based on queue size
- Minimum: 1 instance
- Maximum: 10 instances

### Vertical Scaling

**Instance Sizes**:
- Basic: 512 MB RAM, 0.5 CPU
- Standard: 2 GB RAM, 1 CPU
- Pro: 8 GB RAM, 4 CPU

**Recommendation**: Start with Standard, scale up as needed

---

## Sign-Off

**Architecture Date**: 2026-09-01
**Architecture By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 2 - Determine Final Render Service Architecture
**Status**: ✅ ARCHITECTURE DEFINED

**Overall Assessment**: Render service architecture defined with 7 services: Frontend (web), Backend (web), PostgreSQL (managed), Redis (managed), Celery Worker (worker), Celery Beat (worker), Migration (job). Custom monitoring deferred in favor of Render native observability. Cost estimate: $86/month (Standard tier) or $0/month (Free tier 90 days). Architecture preserves all required functionality while minimizing cost.

**Next Phase**: Phase 3 - Create render.yaml Configuration
