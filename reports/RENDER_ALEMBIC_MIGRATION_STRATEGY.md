# RENDER ALEMBIC MIGRATION STRATEGY

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 10 - Alembic Migration Strategy

---

## Executive Summary

Alembic migration strategy defined. Migrations must run before backend starts. Three options evaluated: pre-deploy command (preferred), one-time job (alternative), manual shell (fallback). Migration command: `alembic upgrade head`. Verification steps included. No create_all in production. Critical for database schema integrity.

**Status**: ✅ MIGRATION STRATEGY DEFINED

---

## Current Migration Setup

### Alembic Configuration

**Location**: `backend/alembic/`
**Config File**: `backend/alembic.ini`
**Migrations**: `backend/alembic/versions/`

**Current URL in alembic.ini**:
```ini
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/jarvis_ai
```

**Note**: This is a placeholder, will be overridden by environment variable

### Migration Behavior

**Development/Testing**:
```python
if settings.APP_ENV in ["development", "testing"]:
    await init_db()
    logger.info("Database initialized via create_all()")
```

**Production**:
```python
else:
    logger.info("Production mode - skipping create_all, relying on Alembic migrations")
```

**Critical**: Production must use Alembic migrations, not create_all

---

## Migration Strategy Options

### Option A: Pre-deploy Command (Preferred)

**Method**: Use Render pre-deploy command for backend service

**Configuration**:
```yaml
services:
  - type: web
    name: jarvis-backend
    preDeployCommand: alembic upgrade head
```

**Pros**:
- Automatic execution
- Runs before backend starts
- No manual intervention
- Integrated with deployment pipeline

**Cons**:
- May not be available in all Render plans
- Limited error handling visibility
- May require specific Render plan tier

**Availability**: Check Render documentation for pre-deploy command support

**Recommendation**: Use if available

---

### Option B: One-time Job (Alternative)

**Method**: Create one-time cron job for migrations

**Configuration**:
```yaml
services:
  - type: cron
    name: jarvis-migrations
    schedule: "0 0 * * *" # Daily (change to one-time)
    startCommand: alembic upgrade head
```

**Pros**:
- Manual control
- Can be retried if fails
- Independent of backend deployment
- Full visibility in Render dashboard

**Cons**:
- Manual intervention required
- Must remember to run
- Not integrated with deployment pipeline

**Execution**:
1. Create migration job in render.yaml
2. Deploy to Render
3. Manually trigger job via Render dashboard
4. Verify migration success
5. Deploy backend service

**Recommendation**: Use if pre-deploy command not available

---

### Option C: Manual Shell (Fallback)

**Method**: Run migrations via Render shell

**Execution**:
1. Access Render shell for backend service
2. Run `alembic upgrade head`
3. Verify migration success
4. Exit shell
5. Deploy backend service

**Pros**:
- Full control
- Can inspect state
- Can run custom commands

**Cons**:
- Manual intervention required
- Not automated
- Prone to human error

**Recommendation**: Use only as fallback

---

## Recommended Strategy

### Primary Strategy: Pre-deploy Command

**If Render supports pre-deploy commands**:
1. Configure pre-deploy command in render.yaml
2. Deploy backend service
3. Pre-deploy command runs automatically
4. Backend starts after migration completes

### Fallback Strategy: One-time Job

**If pre-deploy commands not available**:
1. Create migration job in render.yaml
2. Deploy migration job first
3. Manually trigger migration job
4. Verify migration success
5. Deploy backend service

### Emergency Fallback: Manual Shell

**If automated options fail**:
1. Access Render shell
2. Run migration manually
3. Verify success
4. Deploy backend service

---

## Migration Execution Steps

### Step 1: Prepare Database

**Action**: Create PostgreSQL service in Render

**Verification**:
```sql
SELECT version();
```

**Expected**: PostgreSQL 15 with pgvector extension

---

### Step 2: Configure DATABASE_URL

**Action**: Set DATABASE_URL in Render environment

**Format**: `postgresql+asyncpg://user:pass@host:port/db`

**Verification**: Check environment variable in Render dashboard

---

### Step 3: Run Migration

**Command**: `alembic upgrade head`

**Expected Output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> <revision_id>, <message>
...
```

---

### Step 4: Verify Migration

**Check Current Version**:
```bash
alembic current
```

**Expected**: Latest revision ID

**Check Head Version**:
```bash
alembic heads
```

**Expected**: Same as current version

**Verify Tables**:
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

**Expected**: All required tables present

**Verify ENUMs**:
```sql
SELECT enumlabel FROM pg_enum WHERE enumtypid = (
    SELECT oid FROM pg_type WHERE typname = 'userrole'
);
```

**Expected**: All ENUM values present

**Verify pgvector Extension**:
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**Expected**: Extension present

---

### Step 5: Deploy Backend

**Action**: Deploy backend service after migration verified

**Verification**: Backend health check passes

---

## Migration Rollback

### Rollback Procedure

**Command**: `alembic downgrade -1`

**Expected Output**:
```
INFO  [alembic.runtime.migration] Running downgrade -> <revision_id>, <message>
```

**Verification**:
```bash
alembic current
```

**Expected**: Previous revision ID

**Use Cases**:
- Migration failed
- Migration introduced bug
- Need to revert schema change

**Warning**: Rollback may cause data loss if migration includes destructive changes

---

## Migration Best Practices

### Before Migration

1. **Backup Database**: Use Render automated backup or manual backup
2. **Test Migration**: Run migration in staging environment
3. **Review Migration**: Inspect migration file for destructive changes
4. **Plan Rollback**: Know how to rollback if needed

### During Migration

1. **Monitor Logs**: Watch migration logs for errors
2. **Verify Success**: Check migration version after completion
3. **Test Application**: Verify application works after migration
4. **Document Changes**: Record migration ID and changes

### After Migration

1. **Verify Schema**: Check tables, ENUMs, extensions
2. **Test Functionality**: Run smoke tests
3. **Monitor Errors**: Watch for migration-related errors
4. **Update Documentation**: Document migration in changelog

---

## Migration Troubleshooting

### Migration Fails

**Symptoms**:
- Migration command fails
- Error message in logs
- Migration not applied

**Possible Causes**:
1. Database connection error
2. Migration file syntax error
3. Schema conflict
4. Permission error

**Solutions**:
1. Verify DATABASE_URL is correct
2. Check migration file syntax
3. Inspect database schema for conflicts
4. Verify database permissions

### Migration Hangs

**Symptoms**:
- Migration command runs indefinitely
- No output
- No completion

**Possible Causes**:
1. Database lock
2. Long-running transaction
3. Network issue

**Solutions**:
1. Check for database locks
2. Kill long-running transactions
3. Check network connectivity

### Migration Applied but Schema Wrong

**Symptoms**:
- Migration reports success
- Schema not as expected
- Application fails

**Possible Causes**:
1. Migration file incorrect
2. Migration not actually applied
3. Wrong database

**Solutions**:
1. Inspect migration file
2. Verify migration version
3. Verify correct database

---

## Migration Verification Checklist

### Pre-Migration Checklist

- [ ] PostgreSQL service created
- [ ] DATABASE_URL configured
- [ ] DATABASE_URL format correct (postgresql+asyncpg://)
- [ ] pgvector extension available
- [ ] Migration files present
- [ ] Migration files reviewed
- [ ] Backup available (if needed)

### Post-Migration Checklist

- [ ] Migration command executed
- [ ] Migration succeeded (no errors)
- [ ] Current version matches head
- [ ] Tables created/updated
- [ ] ENUMs created/updated
- [ ] pgvector extension enabled
- [ ] Backend health check passes
- [ ] Application functional

---

## render.yaml Configuration

### Pre-deploy Command Configuration

```yaml
services:
  - type: web
    name: jarvis-backend
    preDeployCommand: alembic upgrade head
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: jarvis-postgres
          property: connectionString
```

### One-time Job Configuration

```yaml
services:
  - type: cron
    name: jarvis-migrations
    schedule: "0 0 * * *" # Change to one-time manual trigger
    startCommand: alembic upgrade head
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: jarvis-postgres
          property: connectionString
```

---

## Sign-Off

**Migration Strategy Date**: 2026-09-01
**Migration Strategy By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 10 - Alembic Migration Strategy
**Status**: ✅ MIGRATION STRATEGY DEFINED

**Overall Assessment**: Alembic migration strategy defined with three options: pre-deploy command (preferred), one-time job (alternative), manual shell (fallback). Migration command: `alembic upgrade head`. Verification steps included. No create_all in production. Critical for database schema integrity. DATABASE_URL must be in asyncpg format. Migrations must run before backend starts.

**Recommended Approach**: Use pre-deploy command if available, otherwise use one-time job.

**Next Phase**: Phase 11 - Celery Production Services
