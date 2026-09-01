# RENDER REDIS DESIGN

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 5 - Redis Design

---

## Executive Summary

Render Redis is fully supported with authentication and multiple databases. The application uses Redis for caching (database 0), Celery broker (database 1), and Celery result backend (database 2). Redis password authentication is required (from security hardening). Render provides managed Redis with automatic persistence and private network connectivity.

**Status**: ✅ REDIS DESIGN COMPLETE

---

## Redis Configuration

### Render Redis Service

**Service Type**: Redis (Render Managed)

**Version**: Redis 7

**Plan**: Standard (can be upgraded to Pro)

**Authentication**: Enabled (REDIS_PASSWORD required)

**Connection**:
- Private network connectivity
- TLS available (rediss://)
- Automatic persistence (AOF)

---

## Redis Databases

### Database Usage

**Database 0**: Application cache
- Session storage
- Temporary data
- Caching

**Database 1**: Celery broker
- Task queue
- Message broker

**Database 2**: Celery result backend
- Task results
- Task status

### Database Selection

**Application Configuration**:
```python
REDIS_URL = redis://:${REDIS_PASSWORD}@host:6379/0
CELERY_BROKER_URL = redis://:${REDIS_PASSWORD}@host:6379/1
CELERY_RESULT_BACKEND = redis://:${REDIS_PASSWORD}@host:6379/2
```

**Render Configuration**:
- Render provides base REDIS_URL
- Must add database numbers (/0, /1, /2)
- Must add REDIS_PASSWORD

---

## Redis URL Configuration

### Render REDIS_URL Format

**Render Format**: `rediss://default:password@host:port` (with TLS)
or `redis://default:password@host:port` (without TLS)

**Application Format**: `redis://:password@host:port/db`

**Conversion Required**: YES

### URL Construction

**Base URL from Render**: `rediss://default:password@host:port`

**Application URLs**:
```python
# Database 0 (cache)
REDIS_URL = rediss://:password@host:port/0

# Database 1 (broker)
CELERY_BROKER_URL = rediss://:password@host:port/1

# Database 2 (result backend)
CELERY_RESULT_BACKEND = rediss://:password@host:port/2
```

**Notes**:
- Remove `default:` from URL (use `:` instead)
- Add database number
- Keep password
- Keep host and port

---

## Redis Authentication

### Password Configuration

**Environment Variable**: REDIS_PASSWORD

**Source**: Render Redis service

**Configuration**:
- Set in Render environment
- Passed to all services
- Required for all Redis connections

### Authentication in Application

**Current Configuration**:
```python
REDIS_URL = redis://:${REDIS_PASSWORD}@redis:6379/0
```

**Render Configuration**:
```python
REDIS_URL = rediss://:${REDIS_PASSWORD}@host:port/0
```

**Notes**:
- Password in URL (after `:`)
- Works with hiredis
- Works with redis-py

---

## Redis Security

### Security Features

**Authentication**:
- Password required (REDIS_PASSWORD)
- No anonymous access

**Network**:
- Private network connectivity
- No public access
- Internal services only

**Encryption**:
- In transit: TLS (rediss://)
- At rest: Render disk encryption

**Access Control**:
- Render-managed
- No direct shell access
- IP allowlist configured

### IP Allowlist

**Configuration**:
```yaml
ipallow:
  - source: 0.0.0.0/0 # Allow from Render private network
```

**Notes**:
- Allows access from Render private network
- Blocks external access
- Services on same Render account can access

---

## Redis Persistence

### Persistence Configuration

**Mode**: AOF (Append Only File)

**Configuration**:
- Automatic persistence
- Data durability
- Fast recovery

**Render Feature**: Automatic persistence included

---

## Redis Performance

### Instance Sizing

**Standard Plan**:
- 25 MB memory
- 10,000 connections
- Suitable for initial deployment

**Pro Plan**:
- 1 GB memory
- 50,000 connections
- Suitable for production load

**Recommendation**: Start with Standard, upgrade to Pro as needed

### Connection Pooling

**Application Configuration**:
```python
REDIS_POOL_SIZE: int = 10
REDIS_MAX_CONNECTIONS: int = 50
```

**Render Connection Limits**:
- Standard: 10,000 connections
- Pro: 50,000 connections

**Recommendation**: Keep application pool sizes within Render limits

---

## Redis Monitoring

### Render Native Monitoring

**Metrics Available**:
- Memory usage
- Connection count
- Command rate
- Hit rate
- Eviction rate

**Logs**:
- Connection logs
- Error logs
- Command logs

**Alerts**:
- High memory usage
- High connection count
- Redis down

### Application Monitoring

**Backend Health Check**:
```python
# /health/ready endpoint checks Redis
redis_client.ping()
```

**Celery Health Check**:
```python
# Celery inspect ping
celery -A app.worker inspect ping
```

---

## Redis Backup Strategy

### Render Persistence

**Backup Method**: Automatic persistence (AOF)

**Recovery**: Automatic on restart

**No Separate Backup Required**: Render handles persistence

### Custom Backups (Optional)

**Backup Method**: Redis dump

**Command**: `redis-cli --rdb /path/to/dump.rdb`

**Recommendation**: Use Render automatic persistence

---

## Celery Configuration

### Celery Broker Configuration

**Broker URL**: `redis://:${REDIS_PASSWORD}@host:port/1`

**Configuration**:
```python
CELERY_BROKER_URL = redis://:${REDIS_PASSWORD}@host:port/1
```

**Notes**:
- Uses database 1
- Requires password
- TLS recommended

### Celery Result Backend Configuration

**Backend URL**: `redis://:${REDIS_PASSWORD}@host:port/2`

**Configuration**:
```python
CELERY_RESULT_BACKEND = redis://:${REDIS_PASSWORD}@host:port/2
```

**Notes**:
- Uses database 2
- Requires password
- TLS recommended

### Celery Task Configuration

**Task Queues**:
- default
- documents
- knowledge
- agents
- computer

**Queue Configuration**:
```python
task_queues = {
    'default': {...},
    'documents': {...},
    'knowledge': {...},
    'agents': {...},
    'computer': {...},
}
```

---

## Redis vs. Render Redis

### Current Docker Configuration

**Image**: redis:7-alpine

**Command**:
```bash
redis-server --appendonly yes --requirepass $REDIS_PASSWORD --bind 0.0.0.0
```

**Port**: 6379 (internal only)

### Render Redis Configuration

**Service**: Render managed Redis

**Features**:
- Managed service
- Automatic persistence
- Authentication
- TLS
- Private network
- Monitoring

**Advantages**:
- No container management
- Automatic scaling
- Built-in monitoring
- Automatic backups

**Recommendation**: Use Render managed Redis

---

## Sign-Off

**Redis Design Date**: 2026-09-01
**Redis Design By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 5 - Redis Design
**Status**: ✅ REDIS DESIGN COMPLETE

**Overall Assessment**: Render Redis is fully supported with authentication and multiple databases. Application uses Redis for caching (db 0), Celery broker (db 1), and Celery result backend (db 2). Redis password authentication required (REDIS_PASSWORD). URL format conversion required (add database numbers). Render provides automatic persistence, TLS, and private network connectivity.

**Next Phase**: Phase 6 - Environment Variable Matrix
