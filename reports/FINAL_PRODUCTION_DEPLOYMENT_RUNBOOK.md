# FINAL PRODUCTION DEPLOYMENT RUNBOOK

**Date**: 2026-08-25
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: FINAL GO-LIVE DEPLOYMENT & PRODUCTION HANDOVER
**Phase**: Phase 20 - Final Production Deployment

---

## Executive Summary

Final production deployment runbook created. This document outlines the complete deployment sequence for the Jarvis AI platform to production. The deployment procedure includes pre-deployment checks, deployment steps, post-deployment verification, and rollback procedures.

**Status**: ✅ DEPLOYMENT RUNBOOK CREATED

---

## Deployment Overview

### Purpose

Deploy the Jarvis AI Enterprise Agent Platform to production environment following a controlled, documented procedure with verification and rollback capabilities.

### Scope

- Pre-deployment checks and validation
- Database migration execution
- Docker Compose deployment
- Application configuration
- Health verification
- Smoke test execution
- Performance validation
- Security validation

### Prerequisites

- All previous phases completed (Phases 1-19)
- Production environment prepared
- Database backup available
- Rollback procedures documented
- Deployment window scheduled
- Stakeholders notified

---

## Pre-Deployment Checklist

### Environment Preparation

- [ ] Production server available
- [ ] Docker and Docker Compose installed
- [ ] Required ports available (8002, 8081, 9092, 3003, 5557, 5432, 6381)
- [ ] Sufficient disk space available (> 20GB)
- [ ] Sufficient memory available (> 8GB)
- [ ] Network connectivity verified

### Configuration Preparation

- [ ] Environment variables configured (.env)
- [ ] SECRET_KEY set
- [ ] ADMIN_PASSWORD set
- [ ] POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB set
- [ ] REDIS_PASSWORD set (NEW - required for Redis authentication)
- [ ] REDIS_URL configured
- [ ] CELERY_BROKER_URL configured
- [ ] CELERY_RESULT_BACKEND configured
- [ ] GRAFANA_ADMIN_PASSWORD set
- [ ] LLM provider API keys configured (optional)

### Code Preparation

- [ ] Latest code pulled from repository
- [ ] Git tag for deployment identified
- [ ] Docker images built
- [ ] Frontend build completed
- [ ] Database migration script reviewed

### Backup Preparation

- [ ] Database backup available
- [ ] Backup integrity verified
- [ ] Backup location documented
- [ ] Restore procedure tested

### Team Preparation

- [ ] Deployment team assembled
- [ ] Rollback team on standby
- [ ] Stakeholders notified
- [ ] Communication channels established
- [ ] Deployment window confirmed

---

## Deployment Procedure

### Step 1: Pre-Deployment Validation

**Purpose**: Validate all pre-deployment checks

**Procedure**:
1. Verify environment:
   ```bash
   docker --version
   docker-compose --version
   ```

2. Verify disk space:
   ```bash
   df -h
   ```

3. Verify memory:
   ```bash
   free -h
   ```

4. Verify ports available:
   ```bash
   netstat -tuln | grep -E '8002|8081|9092|3003|5557|5432|6381'
   ```

**Expected Result**: All checks pass

**Pass Criteria**: Docker installed, sufficient resources, ports available

**Fail Criteria**: Any check fails - resolve before proceeding

---

### Step 2: Code Deployment

**Purpose**: Deploy code to production server

**Procedure**:
1. Navigate to project directory:
   ```bash
   cd E:\jarvis-ai
   ```

2. Pull latest code:
   ```bash
   git pull origin main
   ```

3. Checkout deployment tag:
   ```bash
   git checkout <deployment-tag>
   ```

4. Verify git status:
   ```bash
   git status
   ```

**Expected Result**: Code deployed at correct tag

**Pass Criteria**: Git shows clean state at deployment tag

**Fail Criteria**: Git shows uncommitted changes or wrong tag

---

### Step 3: Database Backup

**Purpose**: Create pre-deployment database backup

**Procedure**:
1. Create backup:
   ```powershell
   cd scripts
   .\production_backup.ps1 -ProjectName "jarvis-production"
   ```

2. Verify backup created:
   ```bash
   ls -lh ../backups/
   ```

3. Verify backup integrity:
   ```powershell
   .\production_restore.ps1 -BackupFile "../backups/jarvis_backup_YYYYMMDD_HHMMSS.sql.gz" -ProjectName "jarvis-production-validation" -DryRun
   ```

**Expected Result**: Backup created and verified

**Pass Criteria**: Backup file exists, integrity check passes

**Fail Criteria**: Backup fails or integrity check fails

**Rollback Trigger**: Backup failure - abort deployment

---

### Step 4: Docker Images Build

**Purpose**: Build Docker images for production

**Procedure**:
1. Navigate to docker directory:
   ```bash
   cd deploy/docker
   ```

2. Build all images:
   ```bash
   docker-compose -p jarvis-production build
   ```

3. Verify images built:
   ```bash
   docker images | grep jarvis
   ```

**Expected Result**: All images built successfully

**Pass Criteria**: All images present in Docker image list

**Fail Criteria**: Any image build fails

**Rollback Trigger**: Image build failure - abort deployment

---

### Step 5: Database Migration

**Purpose**: Apply database migrations

**Procedure**:
1. Start PostgreSQL only:
   ```bash
   docker-compose -p jarvis-production up -d postgres
   ```

2. Wait for PostgreSQL to be healthy:
   ```bash
   docker-compose -p jarvis-production ps postgres
   ```

3. Run migrations:
   ```bash
   docker-compose -p jarvis-production run --rm backend alembic upgrade head
   ```

4. Verify migration:
   ```bash
   docker-compose -p jarvis-production run --rm backend alembic current
   ```

5. Verify pgvector extension:
   ```bash
   docker-compose -p jarvis-production exec postgres psql -U jarvis -d jarvis -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
   ```

**Expected Result**: Migration applied successfully, pgvector extension present

**Pass Criteria**: Migration version current, pgvector extension present

**Fail Criteria**: Migration fails or pgvector extension missing

**Rollback Trigger**: Migration failure - restore from backup

---

### Step 6: Application Deployment

**Purpose**: Deploy all application services

**Procedure**:
1. Stop PostgreSQL (will be restarted with all services):
   ```bash
   docker-compose -p jarvis-production down
   ```

2. Start all services:
   ```bash
   docker-compose -p jarvis-production up -d
   ```

3. Wait for services to be healthy:
   ```bash
   docker-compose -p jarvis-production ps
   ```

4. Verify all services running:
   ```bash
   docker-compose -p jarvis-production ps
   ```

**Expected Result**: All services running and healthy

**Pass Criteria**: All services show "Up" and "healthy" status

**Fail Criteria**: Any service not running or unhealthy

**Rollback Trigger**: Service startup failure - rollback to previous version

---

### Step 7: Health Verification

**Purpose**: Verify all services are healthy

**Procedure**:
1. Verify PostgreSQL health:
   ```bash
   docker-compose -p jarvis-production exec postgres pg_isready -U jarvis -d jarvis
   ```

2. Verify Redis health:
   ```bash
   docker-compose -p jarvis-production exec redis redis-cli ping
   ```

3. Verify backend health:
   ```bash
   curl http://localhost:8002/health/live
   ```

4. Verify backend readiness:
   ```bash
   curl http://localhost:8002/health/ready
   ```

5. Verify frontend health:
   ```bash
   curl http://localhost:8081/health
   ```

6. Verify Celery worker health:
   ```bash
   docker-compose -p jarvis-production exec celery-worker celery -A app.worker inspect ping
   ```

7. Verify Celery beat health:
   ```bash
   docker-compose -p jarvis-production exec celery-beat celery -A app.worker inspect ping
   ```

8. Verify Flower health:
   ```bash
   docker-compose -p jarvis-production exec flower curl --fail http://localhost:5555/
   ```

**Expected Result**: All health checks pass

**Pass Criteria**: All health checks return success

**Fail Criteria**: Any health check fails

**Rollback Trigger**: Critical health check failure - rollback

---

### Step 8: Smoke Test Execution

**Purpose**: Execute 15-step smoke test

**Procedure**:
1. Navigate to scripts directory:
   ```bash
   cd scripts
   ```

2. Run smoke test:
   ```powershell
   .\validate-production-compose.ps1
   ```

3. Review smoke test results

**Expected Result**: All smoke test steps pass

**Pass Criteria**: All 15 steps pass

**Fail Criteria**: Any step fails

**Rollback Trigger**: Critical step failure - rollback

---

### Step 9: Performance Validation

**Purpose**: Validate performance meets baseline

**Procedure**:
1. Run API response time test:
   ```bash
   ab -n 1000 -c 10 http://localhost:8002/health
   ```

2. Run throughput test:
   ```bash
   wrk -t 4 -c 100 -d 30s http://localhost:8002/health
   ```

3. Monitor resource utilization:
   ```bash
   docker stats --no-stream
   ```

**Expected Result**: Performance meets baseline

**Pass Criteria**: Response times < baseline, throughput > baseline, resources < 80%

**Fail Criteria**: Performance below baseline

**Rollback Trigger**: Critical performance degradation - rollback

---

### Step 10: Security Validation

**Purpose**: Validate security configuration

**Procedure**:
1. Verify security headers:
   ```bash
   curl -I http://localhost:8002/health
   ```

2. Verify CORS configuration
3. Verify authentication works
4. Verify rate limiting works

**Expected Result**: Security configuration valid

**Pass Criteria**: Security headers present, authentication works

**Fail Criteria**: Security configuration invalid

**Rollback Trigger**: Critical security issue - rollback

---

### Step 11: Monitoring Verification

**Purpose**: Verify monitoring is working

**Procedure**:
1. Verify Prometheus health:
   ```bash
   curl http://localhost:9092/-/healthy
   ```

2. Verify Prometheus targets:
   ```bash
   curl http://localhost:9092/api/v1/targets
   ```

3. Verify Grafana health:
   ```bash
   curl -I http://localhost:3003/api/health
   ```

4. Verify Grafana datasource:
   - Login to Grafana (http://localhost:3003)
   - Navigate to Configuration > Data Sources
   - Verify Prometheus datasource is healthy

5. Verify Grafana dashboard:
   - Navigate to Dashboards > Jarvis
   - Verify Jarvis API Overview dashboard loads

**Expected Result**: Monitoring working correctly

**Pass Criteria**: Prometheus and Grafana healthy, dashboard loads

**Fail Criteria**: Monitoring not working

**Rollback Trigger**: Monitoring failure - non-blocking, document issue

---

### Step 12: User Acceptance Testing

**Purpose**: Perform user acceptance testing

**Procedure**:
1. Register test user
2. Login test user
3. Create conversation
4. Send message
5. Verify functionality

**Expected Result**: User acceptance testing passes

**Pass Criteria**: All user flows work correctly

**Fail Criteria**: Critical user flow fails

**Rollback Trigger**: Critical user flow failure - rollback

---

## Post-Deployment Checklist

### Verification

- [ ] All services running and healthy
- [ ] Smoke test passes
- [ ] Performance meets baseline
- [ ] Security configuration valid
- [ ] Monitoring working
- [ ] User acceptance testing passes

### Documentation

- [ ] Deployment timestamp recorded
- [ ] Deployment version recorded
- [ ] Deployment team recorded
- [ ] Deployment issues documented
- [ ] Deployment results documented

### Communication

- [ ] Stakeholders notified of deployment completion
- [ ] Status page updated
- [ ] Release notes published
- [ ] Support team notified

### Monitoring

- [ ] Monitoring dashboards reviewed
- [ ] Alerting rules verified
- [ ] Log aggregation verified
- [ ] Error tracking verified

---

## Rollback Procedure

### Rollback Triggers

- Database migration failure
- Service startup failure
- Critical health check failure
- Smoke test failure
- Critical performance degradation
- Critical security issue
- Critical user flow failure

### Rollback Procedure

1. **Notify Stakeholders**: Communicate rollback initiation
2. **Stop Services**: `docker-compose -p jarvis-production down`
3. **Restore Database**: Use production_restore.ps1
4. **Rollback Code**: `git checkout <previous-tag>`
5. **Rebuild Images**: `docker-compose -p jarvis-production build`
6. **Start Services**: `docker-compose -p jarvis-production up -d`
7. **Verify Health**: Run health checks
8. **Run Smoke Test**: Validate rollback success
9. **Notify Stakeholders**: Communicate rollback completion

**Rollback Time**: 15-30 minutes

---

## Deployment Timeline

### Estimated Duration

| Step | Duration |
|------|----------|
| Pre-Deployment Validation | 5 minutes |
| Code Deployment | 5 minutes |
| Database Backup | 5 minutes |
| Docker Images Build | 10 minutes |
| Database Migration | 5 minutes |
| Application Deployment | 5 minutes |
| Health Verification | 5 minutes |
| Smoke Test Execution | 10 minutes |
| Performance Validation | 10 minutes |
| Security Validation | 5 minutes |
| Monitoring Verification | 5 minutes |
| User Acceptance Testing | 15 minutes |
| **Total** | **85 minutes** |

### Deployment Window

**Recommended**: 2 hours (includes buffer for troubleshooting)

---

## Sign-Off

**Deployment Runbook Date**: 2026-08-25
**Deployment Runbook By**: Cascade AI Assistant
**EPIC**: FINAL GO-LIVE DEPLOYMENT & PRODUCTION HANDOVER
**Phase**: Phase 20 - Final Production Deployment
**Status**: ✅ COMPLETED

**Overall Assessment**: Final production deployment runbook created with comprehensive deployment procedure covering pre-deployment checks, deployment steps, post-deployment verification, and rollback procedures. Runbook ready for execution when deployment window is scheduled.

**Next Steps**:
- Phase 21: Post-Deployment Observation
