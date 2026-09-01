# PRODUCTION SMOKE TEST RUNBOOK

**Date**: 2026-08-25
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: FINAL GO-LIVE DEPLOYMENT & PRODUCTION HANDOVER
**Phase**: Phase 15 - Production Smoke Test

---

## Executive Summary

Production smoke test runbook created. This document outlines the 15-step smoke test procedure to validate the production deployment. The smoke test covers infrastructure, database, backend, frontend, Celery, Redis, and monitoring components.

**Status**: ✅ SMOKE TEST RUNBOOK CREATED

---

## Smoke Test Overview

### Purpose

Validate that all production components are functioning correctly after deployment by executing a comprehensive 15-step smoke test.

### Scope

- Infrastructure services (PostgreSQL, Redis)
- Backend API (health, authentication, CRUD operations)
- Frontend (health, accessibility)
- Celery (worker, beat, flower)
- Monitoring (Prometheus, Grafana)
- Integration tests (end-to-end workflows)

### Prerequisites

- Production environment deployed
- All containers running and healthy
- Environment variables configured
- Database migrations applied
- LLM provider configured (optional for degraded features)

---

## 15-Step Smoke Test Procedure

### Step 1: Verify Docker Compose Environment

**Purpose**: Verify Docker Compose is available and configured

**Command**:
```bash
cd deploy/docker
docker-compose -p jarvis-production ps
```

**Expected Result**: All services listed with status "Up"

**Pass Criteria**: All services running

**Fail Criteria**: Any service not running or Docker Compose error

---

### Step 2: Verify PostgreSQL Health

**Purpose**: Verify PostgreSQL container is healthy

**Command**:
```bash
docker-compose -p jarvis-production exec postgres pg_isready -U jarvis -d jarvis
```

**Expected Result**: "jarvis:5432 - accepting connections"

**Pass Criteria**: PostgreSQL accepting connections

**Fail Criteria**: PostgreSQL not ready or connection error

---

### Step 3: Verify Redis Health

**Purpose**: Verify Redis container is healthy

**Command**:
```bash
docker-compose -p jarvis-production exec redis redis-cli ping
```

**Expected Result**: "PONG"

**Pass Criteria**: Redis responding to ping

**Fail Criteria**: Redis not responding or connection error

---

### Step 4: Verify Alembic Migration Completion

**Purpose**: Verify database migrations are applied

**Command**:
```bash
docker-compose -p jarvis-production exec backend alembic current
```

**Expected Result**: "Current revision(s): 001"

**Pass Criteria**: Migration version 001 applied

**Fail Criteria**: Migration not applied or version mismatch

---

### Step 5: Verify Backend Health Status

**Purpose**: Verify backend container is healthy

**Command**:
```bash
curl http://localhost:8002/health/live
```

**Expected Result**: {"status": "alive"}

**Pass Criteria**: HTTP 200 with status "alive"

**Fail Criteria**: Non-200 status or error response

---

### Step 6: Verify Backend Readiness Status

**Purpose**: Verify backend is ready to accept requests

**Command**:
```bash
curl http://localhost:8002/health/ready
```

**Expected Result**: {"status": "ready", "checks": {"database": "ok", "redis": "ok", "ai_engine": "ok"}}

**Pass Criteria**: HTTP 200 with all checks "ok"

**Fail Criteria**: Non-200 status or any check "failed"

**Note**: ai_engine may be "failed" if no LLM provider configured (acceptable)

---

### Step 7: Verify Frontend Health Status

**Purpose**: Verify frontend container is healthy

**Command**:
```bash
curl http://localhost:8081/health
```

**Expected Result**: "healthy"

**Pass Criteria**: HTTP 200 with "healthy"

**Fail Criteria**: Non-200 status or error response

---

### Step 8: Verify User Registration

**Purpose**: Verify user registration endpoint works

**Command**:
```bash
curl -X POST http://localhost:8002/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "smoke-test@example.com",
    "username": "smoketest",
    "password": "SmokeTest123!",
    "full_name": "Smoke Test User"
  }'
```

**Expected Result**: HTTP 201 with user object

**Pass Criteria**: HTTP 201 with user data

**Fail Criteria**: Non-201 status or error response

---

### Step 9: Verify User Login

**Purpose**: Verify user login endpoint works

**Command**:
```bash
curl -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "smoke-test@example.com",
    "password": "SmokeTest123!"
  }'
```

**Expected Result**: HTTP 200 with access_token and refresh_token

**Pass Criteria**: HTTP 200 with tokens

**Fail Criteria**: Non-200 status or error response

**Note**: Save access_token for subsequent tests

---

### Step 10: Verify Conversation Creation

**Purpose**: Verify conversation creation endpoint works

**Command**:
```bash
curl -X POST http://localhost:8002/api/v1/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "title": "Smoke Test Conversation",
    "description": "Conversation for smoke testing"
  }'
```

**Expected Result**: HTTP 201 with conversation object

**Pass Criteria**: HTTP 201 with conversation data

**Fail Criteria**: Non-201 status or error response

**Note**: Save conversation_id for subsequent tests

---

### Step 11: Verify Tool Creation

**Purpose**: Verify tool creation endpoint works

**Command**:
```bash
curl -X POST http://localhost:8002/api/v1/tools \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "name": "smoke-test-tool",
    "description": "Tool for smoke testing",
    "type": "function",
    "config": {"command": "echo test"}
  }'
```

**Expected Result**: HTTP 201 with tool object

**Pass Criteria**: HTTP 201 with tool data

**Fail Criteria**: Non-201 status or error response

---

### Step 12: Verify Memory Service

**Purpose**: Verify memory service endpoint works

**Command**:
```bash
curl -X GET http://localhost:8002/api/v1/memory \
  -H "Authorization: Bearer <access_token>"
```

**Expected Result**: HTTP 200 with memory data

**Pass Criteria**: HTTP 200 with memory array

**Fail Criteria**: Non-200 status or error response

---

### Step 13: Verify Celery Worker Health

**Purpose**: Verify Celery worker is healthy

**Command**:
```bash
docker-compose -p jarvis-production exec celery-worker celery -A app.worker inspect ping
```

**Expected Result**: pong response with worker stats

**Pass Criteria**: Worker responds with pong

**Fail Criteria**: Worker not responding or error

---

### Step 14: Verify Prometheus Health

**Purpose**: Verify Prometheus is scraping metrics

**Command**:
```bash
curl http://localhost:9092/api/v1/targets
```

**Expected Result**: JSON with jarvis-backend target UP

**Pass Criteria**: jarvis-backend target health "up"

**Fail Criteria**: jarvis-backend target down or missing

---

### Step 15: Verify Grafana Health

**Purpose**: Verify Grafana is accessible

**Command**:
```bash
curl -I http://localhost:3003/api/health
```

**Expected Result**: HTTP 200

**Pass Criteria**: HTTP 200 response

**Fail Criteria**: Non-200 status or connection error

---

## Smoke Test Execution

### Automated Execution

**Script**: `scripts/validate-production-compose.ps1`

**Usage**:
```powershell
cd deploy/docker
../../scripts/validate-production-compose.ps1
```

**Note**: This script automates the 15-step smoke test procedure

### Manual Execution

Execute each step manually following the procedure above

**Recommended**: Use manual execution for initial deployment validation

---

## Smoke Test Results

### Pass Criteria

- All 15 steps pass
- All services healthy
- All endpoints responding correctly
- No errors in logs

### Fail Criteria

- Any step fails
- Any service unhealthy
- Any endpoint error
- Errors in logs

### Partial Pass Criteria

- Critical steps pass (1-7, 13-15)
- Non-critical steps may fail if LLM provider not configured (8-12)

**Note**: Partial pass acceptable for initial deployment without LLM provider

---

## Troubleshooting

### Common Failures

#### PostgreSQL Not Ready

**Symptom**: Step 2 fails

**Solutions**:
1. Check PostgreSQL logs: `docker-compose logs postgres`
2. Verify PostgreSQL container is running: `docker ps`
3. Check environment variables: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

#### Redis Not Ready

**Symptom**: Step 3 fails

**Solutions**:
1. Check Redis logs: `docker-compose logs redis`
2. Verify Redis container is running: `docker ps`
3. Test Redis connectivity: `docker-compose exec redis redis-cli ping`

#### Migration Not Applied

**Symptom**: Step 4 fails

**Solutions**:
1. Check migration logs: `docker-compose logs migrations`
2. Verify migration service completed: `docker-compose ps migrations`
3. Re-run migrations: `docker-compose up migrations`

#### Backend Not Ready

**Symptom**: Step 6 fails with database or redis check failed

**Solutions**:
1. Check backend logs: `docker-compose logs backend`
2. Verify database connectivity
3. Verify Redis connectivity
4. Check environment variables

#### Authentication Fails

**Symptom**: Step 8 or 9 fails

**Solutions**:
1. Check backend logs: `docker-compose logs backend`
2. Verify database is accessible
3. Verify SECRET_KEY is set
4. Verify ADMIN_PASSWORD is set

#### LLM Features Fail

**Symptom**: Steps 8-12 fail with LLM-related errors

**Solutions**:
1. This is expected if no LLM provider configured
2. Configure OPENAI_API_KEY or ANTHROPIC_API_KEY if LLM features required
3. Accept degraded functionality if LLM provider not configured

#### Celery Worker Not Ready

**Symptom**: Step 13 fails

**Solutions**:
1. Check Celery worker logs: `docker-compose logs celery-worker`
2. Verify Redis is accessible
3. Verify backend is accessible
4. Check health check: `docker-compose ps celery-worker`

#### Prometheus Not Scraping

**Symptom**: Step 14 fails

**Solutions**:
1. Check Prometheus logs: `docker-compose logs prometheus`
2. Check Prometheus targets: http://localhost:9092/targets
3. Verify backend metrics endpoint: curl http://localhost:8002/metrics
4. Verify backend is accessible from Prometheus

#### Grafana Not Accessible

**Symptom**: Step 15 fails

**Solutions**:
1. Check Grafana logs: `docker-compose logs grafana`
2. Verify Grafana container is running: `docker ps`
3. Check Grafana admin credentials
4. Verify Prometheus datasource is configured

---

## Pre-Deployment Checklist

### Before Running Smoke Test

- [ ] Production environment deployed
- [ ] All containers running
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Smoke test script available
- [ ] Access to production environment

### During Smoke Test

- [ ] Execute each step in order
- [ ] Document results for each step
- [ ] Capture logs for failed steps
- [ ] Note any warnings or errors

### After Smoke Test

- [ ] Review all results
- [ ] Document any failures
- [ ] Troubleshoot failures
- [ ] Re-run smoke test after fixes
- [ ] Document final results

---

## Sign-Off

**Smoke Test Date**: 2026-08-25
**Smoke Test By**: Cascade AI Assistant
**EPIC**: FINAL GO-LIVE DEPLOYMENT & PRODUCTION HANDOVER
**Phase**: Phase 15 - Production Smoke Test
**Status**: ✅ SMOKE TEST RUNBOOK CREATED

**Overall Assessment**: Smoke test runbook created with 15-step procedure covering all critical production components. Runbook ready for execution when production environment is deployed.

**Next Steps**:
- Phase 16: Restart/Recovery Test
