# FINAL PRODUCTION SMOKE TEST

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: POST-GO-LIVE SECURITY HARDENING
**Phase**: Phase 12 - Final Production Smoke Test

---

## Executive Summary

Final production smoke test documented. This test validates all functionality after security hardening changes. The test covers infrastructure, database, backend, frontend, Celery, Redis, monitoring, and security. All previously certified functionality must remain functional after security hardening.

**Status**: ✅ SMOKE TEST PROCEDURES DOCUMENTED

---

## Smoke Test Overview

### Purpose

Validate that all previously certified functionality remains functional after security hardening changes:
- Redis authentication
- PostgreSQL port removal
- Redis port removal
- HTTPS/TLS configuration (ready)

### Scope

- Infrastructure (Docker Compose, networks, volumes)
- Database (PostgreSQL, migrations, pgvector)
- Backend (health, authentication, API)
- Frontend (health, serving, API proxy)
- Celery (worker, beat, tasks)
- Redis (authentication, connectivity)
- Monitoring (Prometheus, Grafana)
- Security (port exposures, authentication)

### Prerequisites

- Docker Compose installed
- Environment variables configured (.env)
- REDIS_PASSWORD set (NEW REQUIREMENT)
- All required secrets set
- Sufficient disk space
- Sufficient memory

---

## Smoke Test Procedure

### Step 1: Infrastructure Validation

**Purpose**: Validate Docker Compose infrastructure

**Procedure**:
1. Verify Docker Compose availability
2. Verify Docker daemon running
3. Verify sufficient disk space
4. Verify sufficient memory
5. Verify required ports available

**Commands**:
```bash
# Verify Docker Compose
docker-compose --version

# Verify Docker daemon
docker ps

# Verify disk space
Get-PSDrive C

# Verify memory
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory

# Verify ports available
Get-NetTCPConnection -State Listen | Select-Object LocalPort
```

**Expected Result**: All infrastructure checks pass

**Pass Criteria**: Docker available, sufficient resources, ports available

**Fail Criteria**: Any infrastructure check fails

---

### Step 2: Database Validation

**Purpose**: Validate PostgreSQL database with new internal-only configuration

**Procedure**:
1. Start PostgreSQL container
2. Verify PostgreSQL health check
3. Verify PostgreSQL internal connectivity
4. Verify pgvector extension
5. Verify database schema
6. Verify no host port exposure

**Commands**:
```bash
# Start PostgreSQL
docker-compose -p jarvis-production up -d postgres

# Verify PostgreSQL health
docker-compose -p jarvis-production ps postgres

# Verify PostgreSQL internal connectivity
docker-compose -p jarvis-production exec postgres pg_isready -U jarvis -d jarvis

# Verify pgvector extension
docker-compose -p jarvis-production exec postgres psql -U jarvis -d jarvis -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Verify database schema
docker-compose -p jarvis-production exec postgres psql -U jarvis -d jarvis -c "\dt"

# Verify no host port exposure
docker-compose -p jarvis-production config | grep postgres
```

**Expected Result**: PostgreSQL healthy, pgvector present, schema valid, no host port

**Pass Criteria**: PostgreSQL healthy, pgvector extension present, no port 5434 exposed

**Fail Criteria**: PostgreSQL unhealthy, pgvector missing, port exposed

---

### Step 3: Redis Validation

**Purpose**: Validate Redis with new authentication configuration

**Procedure**:
1. Set REDIS_PASSWORD in .env
2. Start Redis container
3. Verify Redis health check with authentication
4. Verify Redis internal connectivity
5. Verify Redis authentication works
6. Verify no host port exposure

**Commands**:
```bash
# Set REDIS_PASSWORD
echo "REDIS_PASSWORD=strongpassword123" >> .env

# Start Redis
docker-compose -p jarvis-production up -d redis

# Verify Redis health
docker-compose -p jarvis-production ps redis

# Verify Redis internal connectivity with authentication
docker-compose -p jarvis-production exec redis redis-cli -a $REDIS_PASSWORD ping

# Verify Redis authentication
docker-compose -p jarvis-production exec redis redis-cli -a wrongpassword ping
# Should fail with NOAUTH error

# Verify no host port exposure
docker-compose -p jarvis-production config | grep redis
```

**Expected Result**: Redis healthy, authentication works, no host port

**Pass Criteria**: Redis healthy, authentication required, no port 6381 exposed

**Fail Criteria**: Redis unhealthy, authentication bypass, port exposed

---

### Step 4: Backend Validation

**Purpose**: Validate backend with new Redis authentication

**Procedure**:
1. Start backend container
2. Verify backend health check
3. Verify backend readiness check
4. Verify database connectivity
5. Verify Redis connectivity with authentication
6. Verify API endpoints

**Commands**:
```bash
# Start backend
docker-compose -p jarvis-production up -d backend

# Verify backend health
docker-compose -p jarvis-production ps backend

# Verify backend liveness
curl http://localhost:8002/health/live

# Verify backend readiness
curl http://localhost:8002/health/ready

# Verify database connectivity
docker-compose -p jarvis-production logs backend | grep "PostgreSQL"

# Verify Redis connectivity
docker-compose -p jarvis-production logs backend | grep "Redis"

# Verify API endpoint
curl http://localhost:8002/api/v1/
```

**Expected Result**: Backend healthy, database connected, Redis connected with authentication

**Pass Criteria**: Backend healthy, all readiness checks pass, no Redis authentication errors

**Fail Criteria**: Backend unhealthy, Redis authentication errors

---

### Step 5: Frontend Validation

**Purpose**: Validate frontend with new nginx.conf

**Procedure**:
1. Start frontend container
2. Verify frontend health check
3. Verify frontend serves content
4. Verify API proxy works (if configured)
5. Verify HTTPS configuration ready

**Commands**:
```bash
# Start frontend
docker-compose -p jarvis-production up -d frontend

# Verify frontend health
docker-compose -p jarvis-production ps frontend

# Verify frontend health endpoint
curl http://localhost:8081/health

# Verify frontend serves content
curl -I http://localhost:8081/

# Verify API proxy (if configured)
curl http://localhost:8081/api/v1/
```

**Expected Result**: Frontend healthy, content served, HTTPS configuration ready

**Pass Criteria**: Frontend healthy, content served, nginx.conf updated

**Fail Criteria**: Frontend unhealthy, content not served

---

### Step 6: Celery Validation

**Purpose**: Validate Celery with new Redis authentication

**Procedure**:
1. Start Celery worker
2. Start Celery beat
3. Start Flower
4. Verify Celery worker health
5. Verify Celery beat health
6. Verify Flower health
7. Verify Redis authentication for Celery
8. Queue test task
9. Verify task execution

**Commands**:
```bash
# Start Celery services
docker-compose -p jarvis-production up -d celery-worker celery-beat flower

# Verify Celery worker health
docker-compose -p jarvis-production ps celery-worker

# Verify Celery beat health
docker-compose -p jarvis-production ps celery-beat

# Verify Flower health
docker-compose -p jarvis-production ps flower

# Verify Celery worker ping
docker-compose -p jarvis-production exec celery-worker celery -A app.worker inspect ping

# Verify Celery beat ping
docker-compose -p jarvis-production exec celery-beat celery -A app.worker inspect ping

# Verify Flower accessible
curl http://localhost:5557/

# Queue test task
docker-compose -p jarvis-production exec backend python -c "
from app.worker import celery_app
result = celery_app.send_task('app.tasks.document_tasks.cleanup_old_documents')
print(f'Task ID: {result.id}')
"

# Monitor task execution
docker-compose -p jarvis-production logs celery-worker -f
```

**Expected Result**: All Celery services healthy, tasks execute with Redis authentication

**Pass Criteria**: All Celery services healthy, no Redis authentication errors, tasks execute

**Fail Criteria**: Celery services unhealthy, Redis authentication errors, tasks fail

---

### Step 7: Monitoring Validation

**Purpose**: Validate monitoring services

**Procedure**:
1. Start Prometheus
2. Start Grafana
3. Verify Prometheus health
4. Verify Grafana health
5. Verify Prometheus targets
6. Verify Grafana datasource
7. Verify Grafana dashboard

**Commands**:
```bash
# Start monitoring services
docker-compose -p jarvis-production up -d prometheus grafana

# Verify Prometheus health
docker-compose -p jarvis-production ps prometheus
curl http://localhost:9092/-/healthy

# Verify Grafana health
docker-compose -p jarvis-production ps grafana
curl -I http://localhost:3003/api/health

# Verify Prometheus targets
curl http://localhost:9092/api/v1/targets

# Verify Grafana datasource (manual)
# Login to Grafana at http://localhost:3003
# Navigate to Configuration > Data Sources
# Verify Prometheus datasource is healthy

# Verify Grafana dashboard (manual)
# Navigate to Dashboards > Jarvis
# Verify Jarvis API Overview dashboard loads
```

**Expected Result**: Monitoring services healthy, targets up, dashboard loads

**Pass Criteria**: Prometheus healthy, Grafana healthy, targets up

**Fail Criteria**: Monitoring services unhealthy, targets down

---

### Step 8: Authentication Validation

**Purpose**: Validate authentication system

**Procedure**:
1. Register test user
2. Login test user
3. Verify JWT token issued
4. Verify protected endpoint accessible with token
5. Verify token refresh works
6. Verify logout works

**Commands**:
```bash
# Register user
curl -X POST http://localhost:8002/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}'

# Login user
curl -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Access protected endpoint with token
curl http://localhost:8002/api/v1/auth/me \
  -H "Authorization: Bearer <token>"

# Refresh token
curl -X POST http://localhost:8002/api/v1/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"

# Logout
curl -X POST http://localhost:8002/api/v1/auth/logout \
  -H "Authorization: Bearer <token>"
```

**Expected Result**: Authentication works correctly

**Pass Criteria**: Registration succeeds, login succeeds, token issued, protected endpoint accessible

**Fail Criteria**: Authentication fails

---

### Step 9: Security Validation

**Purpose**: Validate security hardening changes

**Procedure**:
1. Verify PostgreSQL port not exposed
2. Verify Redis port not exposed
3. Verify Redis authentication required
4. Verify monitoring ports exposed (expected)
5. Verify application ports exposed (expected)

**Commands**:
```bash
# Verify port exposures
docker-compose -p jarvis-production config | grep -E "ports:"

# Verify PostgreSQL not accessible from host
curl telnet://localhost:5434
# Should fail (connection refused)

# Verify Redis not accessible from host
curl telnet://localhost:6381
# Should fail (connection refused)

# Verify Redis requires authentication
docker-compose -p jarvis-production exec redis redis-cli ping
# Should fail with NOAUTH error

# Verify backend accessible
curl http://localhost:8002/health/live

# Verify frontend accessible
curl http://localhost:8081/health
```

**Expected Result**: PostgreSQL and Redis not exposed, Redis authentication required

**Pass Criteria**: PostgreSQL port not exposed, Redis port not exposed, Redis authentication required

**Fail Criteria**: PostgreSQL or Redis exposed, Redis authentication bypass

---

### Step 10: Full Stack Validation

**Purpose**: Validate full stack integration

**Procedure**:
1. Start all services
2. Wait for all health checks
3. Verify all services healthy
4. Run end-to-end test
5. Verify no errors in logs

**Commands**:
```bash
# Start all services
docker-compose -p jarvis-production up -d

# Wait for health checks
docker-compose -p jarvis-production ps

# Verify all services healthy
docker-compose -p jarvis-production ps

# Check logs for errors
docker-compose -p jarvis-production logs --tail=100

# Run end-to-end test
# 1. Register user
# 2. Login user
# 3. Create conversation
# 4. Send message
# 5. Verify response
```

**Expected Result**: All services healthy, end-to-end test passes

**Pass Criteria**: All services healthy, no critical errors, end-to-end test passes

**Fail Criteria**: Any service unhealthy, critical errors, end-to-end test fails

---

## Smoke Test Checklist

### Infrastructure
- [ ] Docker Compose available
- [ ] Docker daemon running
- [ ] Sufficient disk space
- [ ] Sufficient memory
- [ ] Required ports available

### Database
- [ ] PostgreSQL healthy
- [ ] PostgreSQL internal connectivity
- [ ] pgvector extension present
- [ ] Database schema valid
- [ ] No host port exposure

### Redis
- [ ] Redis healthy
- [ ] Redis authentication required
- [ ] Redis internal connectivity
- [ ] No host port exposure

### Backend
- [ ] Backend healthy
- [ ] Database connected
- [ ] Redis connected with authentication
- [ ] API endpoints accessible
- [ ] Health endpoints working

### Frontend
- [ ] Frontend healthy
- [ ] Content served
- [ ] API proxy working (if configured)
- [ ] HTTPS configuration ready

### Celery
- [ ] Celery worker healthy
- [ ] Celery beat healthy
- [ ] Flower healthy
- [ ] Redis authentication for Celery
- [ ] Tasks execute

### Monitoring
- [ ] Prometheus healthy
- [ ] Grafana healthy
- [ ] Prometheus targets up
- [ ] Grafana datasource healthy
- [ ] Grafana dashboard loads

### Authentication
- [ ] Registration works
- [ ] Login works
- [ ] Token issued
- [ ] Protected endpoint accessible
- [ ] Token refresh works
- [ ] Logout works

### Security
- [ ] PostgreSQL not exposed
- [ ] Redis not exposed
- [ ] Redis authentication required
- [ ] Monitoring ports exposed (expected)
- [ ] Application ports exposed (expected)

### Full Stack
- [ ] All services healthy
- [ ] No critical errors
- [ ] End-to-end test passes

---

## Troubleshooting

### Redis Authentication Errors

**Symptom**: Backend cannot connect to Redis

**Possible Causes**:
1. REDIS_PASSWORD not set in .env
2. REDIS_PASSWORD mismatch
3. Redis not started with password

**Solutions**:
1. Set REDIS_PASSWORD in .env
2. Restart Redis container
3. Verify Redis password in docker-compose.yml

---

### PostgreSQL Connection Errors

**Symptom**: Backend cannot connect to PostgreSQL

**Possible Causes**:
1. PostgreSQL not started
2. PostgreSQL not healthy
3. Network issues

**Solutions**:
1. Verify PostgreSQL container running
2. Verify PostgreSQL health check
3. Verify network connectivity

---

### Celery Task Failures

**Symptom**: Celery tasks failing

**Possible Causes**:
1. Redis authentication errors
2. Backend not healthy
3. Task configuration issues

**Solutions**:
1. Verify Redis authentication
2. Verify backend health
3. Check Celery logs

---

## Sign-Off

**Smoke Test Date**: 2026-09-01
**Smoke Test By**: Cascade AI Assistant
**EPIC**: POST-GO-LIVE SECURITY HARDENING
**Phase**: Phase 12 - Final Production Smoke Test
**Status**: ✅ SMOKE TEST PROCEDURES DOCUMENTED

**Overall Assessment**: Final production smoke test procedures documented. The test validates all functionality after security hardening changes. New requirements include REDIS_PASSWORD environment variable and verification of port exposure removal. All previously certified functionality must remain functional.

**Next Steps**:
- Phase 13: Security Performance Check
