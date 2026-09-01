# RENDER CELERY PRODUCTION SERVICES

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 11 - Celery Production Services

---

## Executive Summary

Celery production services configuration documented. Two Celery services required: Worker (background task processing) and Beat (scheduled task execution). Both configured as Render worker services. Worker uses Redis database 1 for broker, database 2 for result backend. Beat is singleton service (only one instance). Health checks via Celery inspect ping. Task queues: default, documents, knowledge, agents, computer.

**Status**: ✅ CELERY SERVICES CONFIGURED

---

## Celery Architecture

### Current Docker Configuration

**Celery Worker Service**:
```yaml
celery-worker:
  command: celery -A app.worker worker --loglevel=info
  depends_on:
    - postgres
    - redis
    - backend
  healthcheck:
    test: ["CMD", "celery", "-A", "app.worker", "inspect", "ping"]
```

**Celery Beat Service**:
```yaml
celery-beat:
  command: celery -A app.worker beat --loglevel=info
  depends_on:
    - postgres
    - redis
    - backend
  healthcheck:
    test: ["CMD", "celery", "-A", "app.worker", "inspect", "ping"]
```

### Render Configuration

**Celery Worker**: Render worker service
**Celery Beat**: Render worker service (singleton)

---

## Celery Worker Service

### Service Type

**Render Service Type**: Worker Service

**Purpose**: Background task processing

**Dockerfile**: `deploy/docker/backend/Dockerfile`

**Build Context**: `backend`

**Startup Command**: `celery -A app.worker worker --loglevel=info`

### Environment Variables

**Required Variables**:
```yaml
envVars:
  - key: APP_ENV
    value: production
  - key: DATABASE_URL
    fromDatabase:
      name: jarvis-postgres
      property: connectionString
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
    # Manually set to REDIS_URL with /1
  - key: CELERY_RESULT_BACKEND
    # Manually set to REDIS_URL with /2
  - key: SECRET_KEY
    generateValue: true
  - key: ADMIN_PASSWORD
    generateValue: true
  - key: OPENAI_API_KEY
    sync: false
  - key: ANTHROPIC_API_KEY
    sync: false
  - key: GOOGLE_API_KEY
    sync: false
```

### Health Check

**Method**: Celery inspect ping

**Command**: `celery -A app.worker inspect ping`

**Render Configuration**: Render worker health check (if available)

**Alternative**: Monitor worker logs for errors

### Scaling

**Auto-scaling**: Render auto-scales worker based on queue size

**Minimum Instances**: 1

**Maximum Instances**: 10 (configurable)

**Recommendation**: Start with 1 instance, scale based on load

---

## Celery Beat Service

### Service Type

**Render Service Type**: Worker Service

**Purpose**: Scheduled task execution

**Dockerfile**: `deploy/docker/backend/Dockerfile`

**Build Context**: `backend`

**Startup Command**: `celery -A app.worker beat --loglevel=info`

### Singleton Requirement

**Critical**: Only one Beat instance should run

**Reason**: Beat schedules tasks, multiple instances cause duplicate task execution

**Render Configuration**: Set worker instances to 1

### Environment Variables

**Required Variables**: Same as Celery Worker

### Scheduled Tasks

**Current Schedule**:
```python
beat_schedule = {
    'cleanup-old-documents': {
        'task': 'app.tasks.document_tasks.cleanup_old_documents',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'cleanup-old-executions': {
        'task': 'app.tasks.agent_tasks.cleanup_old_executions',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    },
}
```

**Tasks**:
- cleanup-old-documents: Daily at 2 AM UTC
- cleanup-old-executions: Daily at 3 AM UTC

---

## Celery Configuration

### Broker Configuration

**Broker URL**: `redis://:${REDIS_PASSWORD}@host:port/1`

**Purpose**: Task queue

**Database**: Redis database 1

**Render Configuration**:
```yaml
envVars:
  - key: CELERY_BROKER_URL
    # Construct from REDIS_URL with /1
    # Example: rediss://:password@host:port/1
```

### Result Backend Configuration

**Backend URL**: `redis://:${REDIS_PASSWORD}@host:port/2`

**Purpose**: Task results and status

**Database**: Redis database 2

**Render Configuration**:
```yaml
envVars:
  - key: CELERY_RESULT_BACKEND
    # Construct from REDIS_URL with /2
    # Example: rediss://:password@host:port/2
```

### Task Queues

**Current Queues**:
```python
task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'documents': {
        'exchange': 'documents',
        'routing_key': 'documents',
    },
    'knowledge': {
        'exchange': 'knowledge',
        'routing_key': 'knowledge',
    },
    'agents': {
        'exchange': 'agents',
        'routing_key': 'agents',
    },
    'computer': {
        'exchange': 'computer',
        'routing_key': 'computer',
    },
}
```

**Queues**:
- default: General tasks
- documents: Document processing tasks
- knowledge: Knowledge base tasks
- agents: Agent execution tasks
- computer: Computer use tasks

### Task Configuration

**Current Configuration**:
```python
task_track_started = True
task_time_limit = 3600
task_soft_time_limit = 3600 - 60
task_acks_late = True
task_reject_on_worker_lost = True
result_expires = 3600
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000
task_autoretry_for = (Exception,)
task_retry_delay = 60
task_retry_max = 3
task_retry_backoff = True
task_retry_backoff_max = 600
task_retry_jitter = True
```

---

## Celery Tasks

### Task Modules

**Current Task Modules**:
```python
include = [
    'app.tasks.document_tasks',
    'app.tasks.knowledge_tasks',
    'app.tasks.agent_tasks',
    'app.tasks.computer_tasks',
]
```

**Task Files**:
- `app/tasks/document_tasks.py`
- `app/tasks/knowledge_tasks.py`
- `app/tasks/agent_tasks.py`
- `app/tasks/computer_tasks.py`

### Task Types

**Document Tasks**:
- Document processing
- Document embedding
- Document cleanup

**Knowledge Tasks**:
- Knowledge base operations
- Vector similarity search
- Knowledge cleanup

**Agent Tasks**:
- Agent execution
- Agent monitoring
- Execution cleanup

**Computer Tasks**:
- Computer use operations
- Browser automation
- Computer cleanup

---

## render.yaml Configuration

### Celery Worker

```yaml
services:
  - type: worker
    name: jarvis-celery-worker
    env: python
    plan: standard
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.worker worker --loglevel=info
    dockerContext: backend
    dockerfilePath: deploy/docker/backend/Dockerfile
    envVars:
      - key: APP_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: jarvis-postgres
          property: connectionString
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
      - key: CELERY_RESULT_BACKEND
        generateValue: true
      - key: SECRET_KEY
        generateValue: true
      - key: ADMIN_PASSWORD
        generateValue: true
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: GOOGLE_API_KEY
        sync: false
```

### Celery Beat

```yaml
services:
  - type: worker
    name: jarvis-celery-beat
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.worker beat --loglevel=info
    dockerContext: backend
    dockerfilePath: deploy/docker/backend/Dockerfile
    envVars:
      - key: APP_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: jarvis-postgres
          property: connectionString
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
      - key: CELERY_RESULT_BACKEND
        generateValue: true
      - key: SECRET_KEY
        generateValue: true
      - key: ADMIN_PASSWORD
        generateValue: true
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: GOOGLE_API_KEY
        sync: false
```

---

## URL Construction

### CELERY_BROKER_URL

**Base REDIS_URL**: `rediss://default:password@host:port`

**CELERY_BROKER_URL**: `rediss://:password@host:port/1`

**Construction**:
1. Remove `default:` from URL
2. Add database number `/1`
3. Keep password, host, port

### CELERY_RESULT_BACKEND

**Base REDIS_URL**: `rediss://default:password@host:port`

**CELERY_RESULT_BACKEND**: `rediss://:password@host:port/2`

**Construction**:
1. Remove `default:` from URL
2. Add database number `/2`
3. Keep password, host, port

---

## Health Monitoring

### Worker Health Check

**Method**: Celery inspect ping

**Command**: `celery -A app.worker inspect ping`

**Expected Output**: Worker responds with pong

**Render Configuration**: Use Render worker health check (if available)

**Alternative**: Monitor worker logs for errors

### Beat Health Check

**Method**: Celery inspect ping

**Command**: `celery -A app.worker inspect ping`

**Expected Output**: Beat responds with pong

**Note**: Beat may not respond to inspect ping (normal behavior)

**Alternative**: Monitor beat logs for scheduled task execution

---

## Troubleshooting

### Worker Not Starting

**Symptoms**:
- Worker fails to start
- Error in logs
- Worker crashes immediately

**Possible Causes**:
1. Redis connection error
2. Database connection error
3. Environment variable missing
4. Task import error

**Solutions**:
1. Verify REDIS_URL and REDIS_PASSWORD
2. Verify DATABASE_URL
3. Verify all environment variables set
4. Check task imports

### Worker Not Processing Tasks

**Symptoms**:
- Worker running but not processing tasks
- Tasks stuck in queue
- No task execution

**Possible Causes**:
1. Broker URL incorrect
2. Queue name mismatch
3. Worker not subscribed to queue
4. Task not registered

**Solutions**:
1. Verify CELERY_BROKER_URL
2. Verify queue names match
3. Check worker logs for queue subscription
4. Verify task imports

### Beat Not Scheduling Tasks

**Symptoms**:
- Beat running but no tasks scheduled
- Scheduled tasks not executing
- No beat logs

**Possible Causes**:
1. Beat schedule configuration error
2. Beat not running
3. Task not registered
4. Timezone mismatch

**Solutions**:
1. Verify beat_schedule configuration
2. Check beat logs
3. Verify task imports
4. Verify timezone configuration

---

## Sign-Off

**Celery Services Date**: 2026-09-01
**Celery Services By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 11 - Celery Production Services
**Status**: ✅ CELERY SERVICES CONFIGURED

**Overall Assessment**: Celery production services configured with two Render worker services: Worker (background task processing) and Beat (scheduled task execution). Worker uses Redis database 1 for broker, database 2 for result backend. Beat is singleton service (only one instance). Health checks via Celery inspect ping. Task queues: default, documents, knowledge, agents, computer. URL construction required for CELERY_BROKER_URL and CELERY_RESULT_BACKEND.

**Required Configuration**:
- Construct CELERY_BROKER_URL from REDIS_URL with /1
- Construct CELERY_RESULT_BACKEND from REDIS_URL with /2
- Set Beat worker instances to 1 (singleton)
- Configure all environment variables

**Next Phase**: Phase 12 - LLM Provider Configuration
