# PERFORMANCE SMOKE TEST RUNBOOK

**Date**: 2026-08-25
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: FINAL GO-LIVE DEPLOYMENT & PRODUCTION HANDOVER
**Phase**: Phase 18 - Performance

---

## Executive Summary

Performance smoke test runbook created. This document outlines the performance testing procedure to validate that the production deployment meets or exceeds baseline performance metrics established in EPIC-026. Performance tests cover API response times, throughput, and resource utilization.

**Status**: ✅ PERFORMANCE TEST RUNBOOK CREATED

---

## Performance Baseline

### Baseline Metrics (EPIC-026)

**API Response Times**:
- p50: < 100ms
- p95: < 500ms
- p99: < 1000ms

**Throughput**:
- Requests per second: > 100 RPS
- Concurrent users: > 50

**Resource Utilization**:
- CPU: < 70%
- Memory: < 80%
- Database connections: < 80% of pool

**Status**: ✅ BASELINE DEFINED

---

## Performance Test Overview

### Purpose

Validate that the production deployment meets or exceeds baseline performance metrics established in EPIC-026.

### Scope

- API endpoint performance
- Database query performance
- Redis cache performance
- Celery task performance
- Resource utilization

### Prerequisites

- Production environment deployed
- All services running and healthy
- Smoke test passed
- Performance testing tools available (Apache Bench, wrk, or similar)

---

## Performance Test Procedures

### Test 1: API Response Time Test

**Purpose**: Measure API endpoint response times

**Tool**: Apache Bench (ab) or wrk

**Test Endpoints**:
- GET /health
- GET /health/ready
- POST /api/v1/auth/login
- GET /api/v1/conversations
- POST /api/v1/conversations

**Procedure**:
1. Test health endpoint:
   ```bash
   ab -n 1000 -c 10 http://localhost:8002/health
   ```

2. Test readiness endpoint:
   ```bash
   ab -n 1000 -c 10 http://localhost:8002/health/ready
   ```

3. Test login endpoint (requires authentication):
   ```bash
   ab -n 100 -c 10 -p login.json -T application/json http://localhost:8002/api/v1/auth/login
   ```

4. Test conversations endpoint (requires authentication):
   ```bash
   ab -n 1000 -c 10 -H "Authorization: Bearer <token>" http://localhost:8002/api/v1/conversations
   ```

**Expected Results**:
- p50: < 100ms
- p95: < 500ms
- p99: < 1000ms

**Pass Criteria**: All percentiles meet baseline

**Fail Criteria**: Any percentile exceeds baseline

---

### Test 2: Throughput Test

**Purpose**: Measure maximum throughput

**Tool**: wrk

**Procedure**:
1. Test health endpoint throughput:
   ```bash
   wrk -t 4 -c 100 -d 30s http://localhost:8002/health
   ```

2. Test readiness endpoint throughput:
   ```bash
   wrk -t 4 -c 100 -d 30s http://localhost:8002/health/ready
   ```

**Expected Results**:
- Requests per second: > 100 RPS
- Concurrent connections: > 50

**Pass Criteria**: Throughput meets baseline

**Fail Criteria**: Throughput below baseline

---

### Test 3: Database Query Performance Test

**Purpose**: Measure database query performance

**Tool**: PostgreSQL EXPLAIN ANALYZE

**Procedure**:
1. Test user query:
   ```bash
   docker-compose -p jarvis-production exec postgres psql -U jarvis -d jarvis -c "EXPLAIN ANALYZE SELECT * FROM users LIMIT 100;"
   ```

2. Test conversation query:
   ```bash
   docker-compose -p jarvis-production exec postgres psql -U jarvis -d jarvis -c "EXPLAIN ANALYZE SELECT * FROM conversations LIMIT 100;"
   ```

3. Test message query:
   ```bash
   docker-compose -p jarvis-production exec postgres psql -U jarvis -d jarvis -c "EXPLAIN ANALYZE SELECT * FROM messages LIMIT 100;"
   ```

**Expected Results**:
- Query execution time: < 100ms
- Index usage: > 90%

**Pass Criteria**: Queries meet baseline

**Fail Criteria**: Queries exceed baseline

---

### Test 4: Redis Cache Performance Test

**Purpose**: Measure Redis cache performance

**Tool**: redis-benchmark

**Procedure**:
1. Test Redis performance:
   ```bash
   docker-compose -p jarvis-production exec redis redis-benchmark -t set,get -n 10000 -q
   ```

**Expected Results**:
- SET operations: > 50000 ops/sec
- GET operations: > 50000 ops/sec

**Pass Criteria**: Redis meets baseline

**Fail Criteria**: Redis below baseline

---

### Test 5: Celery Task Performance Test

**Purpose**: Measure Celery task execution time

**Tool**: Celery task timing

**Procedure**:
1. Queue test task:
   ```bash
   docker-compose -p jarvis-production exec backend python -c "
   from app.worker import celery_app
  result = celery_app.send_task('app.tasks.document_tasks.cleanup_old_documents')
  print(f'Task ID: {result.id}')
   "
   ```

2. Monitor task execution:
   ```bash
   docker-compose -p jarvis-production logs celery-worker -f
   ```

**Expected Results**:
- Task execution time: < 5 seconds
- Task success rate: 100%

**Pass Criteria**: Tasks meet baseline

**Fail Criteria**: Tasks exceed baseline

---

### Test 6: Resource Utilization Test

**Purpose**: Measure resource utilization under load

**Tool**: Docker stats

**Procedure**:
1. Run load test:
   ```bash
   wrk -t 4 -c 100 -d 60s http://localhost:8002/health
   ```

2. Monitor resource utilization:
   ```bash
   docker stats --no-stream
   ```

**Expected Results**:
- CPU: < 70%
- Memory: < 80%
- Database connections: < 80% of pool

**Pass Criteria**: Resources within baseline

**Fail Criteria**: Resources exceed baseline

---

## Performance Test Execution

### Automated Execution

**Script**: Create performance test script (not currently implemented)

**Usage**:
```powershell
./scripts/performance-test.ps1
```

**Note**: Automated performance test script to be implemented

### Manual Execution

Execute each test manually following the procedure above

**Recommended**: Use manual execution for initial deployment validation

---

## Performance Test Results

### Pass Criteria

- All API response times meet baseline
- Throughput meets baseline
- Database queries meet baseline
- Redis performance meets baseline
- Celery tasks meet baseline
- Resource utilization within baseline

### Fail Criteria

- Any API response time exceeds baseline
- Throughput below baseline
- Any database query exceeds baseline
- Redis performance below baseline
- Any Celery task exceeds baseline
- Resource utilization exceeds baseline

### Partial Pass Criteria

- Critical endpoints meet baseline (health, readiness, authentication)
- Non-critical endpoints may exceed baseline
- Resource utilization within acceptable limits

**Note**: Partial pass acceptable for initial deployment

---

## Troubleshooting

### Common Performance Issues

#### Slow API Response Times

**Symptom**: API endpoints exceed baseline response times

**Solutions**:
1. Check backend logs: `docker-compose logs backend`
2. Check database query performance
3. Check Redis cache hit rate
4. Check resource utilization
5. Add database indexes if needed
6. Optimize queries

#### Low Throughput

**Symptom**: Throughput below baseline

**Solutions**:
1. Check resource utilization
2. Check connection pool limits
3. Check Redis performance
4. Scale horizontally if needed
5. Optimize application code

#### High Resource Utilization

**Symptom**: CPU or memory exceeds baseline

**Solutions**:
1. Check for memory leaks
2. Check for CPU-intensive operations
3. Optimize application code
4. Add resource limits
5. Scale horizontally if needed

#### Slow Database Queries

**Symptom**: Database queries exceed baseline

**Solutions**:
1. Run EXPLAIN ANALYZE on slow queries
2. Add missing indexes
3. Optimize queries
4. Increase connection pool size
5. Consider read replicas

#### Slow Redis Performance

**Symptom**: Redis operations below baseline

**Solutions**:
1. Check Redis memory usage
2. Check Redis CPU usage
3. Optimize Redis configuration
4. Consider Redis clustering
5. Add Redis persistence tuning

---

## Performance Monitoring

### Continuous Monitoring

**Tools**:
- Prometheus metrics
- Grafana dashboards
- Application Performance Monitoring (APM)

**Metrics to Monitor**:
- API response times (p50, p95, p99)
- Request rate
- Error rate
- Database query times
- Redis hit rate
- Resource utilization

**Alerting**:
- p95 response time > 500ms
- Error rate > 1%
- CPU > 80%
- Memory > 90%
- Database connections > 90%

---

## Performance Optimization Recommendations

### Immediate (Required for Production)

1. **Database Indexing**: Ensure all frequently queried columns are indexed
2. **Connection Pooling**: Optimize connection pool sizes
3. **Redis Caching**: Implement caching for frequently accessed data
4. **Query Optimization**: Optimize slow database queries

### Short-Term (Recommended)

1. **CDN Integration**: Serve static assets via CDN
2. **Load Balancing**: Implement load balancer for horizontal scaling
3. **Database Read Replicas**: Implement read replicas for read-heavy workloads
4. **Redis Clustering**: Implement Redis clustering for high availability

### Long-Term (Nice to Have)

1. **Edge Computing**: Deploy to edge locations for lower latency
2. **Database Sharding**: Implement database sharding for scale
3. **Caching Layers**: Implement multi-layer caching
4. **Performance Profiling**: Implement continuous performance profiling

---

## Pre-Test Checklist

### Before Testing

- [ ] Production environment deployed
- [ ] All services running and healthy
- [ ] Smoke test passed
- [ ] Performance testing tools available
- [ ] Baseline metrics reviewed
- [ ] Test procedure reviewed

### During Testing

- [ ] Execute tests in order
- [ ] Document results for each test
- [ ] Monitor resource utilization
- [ ] Capture performance metrics
- [ ] Note any anomalies

### After Testing

- [ ] Review all results
- [ ] Compare to baseline
- [ ] Document any failures
- [ ] Document any optimizations
- [ ] Update baseline if needed

---

## Sign-Off

**Performance Test Date**: 2026-08-25
**Performance Test By**: Cascade AI Assistant
**EPIC**: FINAL GO-LIVE DEPLOYMENT & PRODUCTION HANDOVER
**Phase**: Phase 18 - Performance
**Status**: ✅ PERFORMANCE TEST RUNBOOK CREATED

**Overall Assessment**: Performance test runbook created with comprehensive test procedures covering API response times, throughput, database performance, Redis performance, Celery task performance, and resource utilization. Baseline metrics from EPIC-026 referenced. Runbook ready for execution when production environment is deployed.

**Next Steps**:
- Phase 19: Security Final Check
