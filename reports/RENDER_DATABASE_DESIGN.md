# RENDER DATABASE DESIGN

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 4 - Database Design for Render

---

## Executive Summary

Render PostgreSQL with pgvector extension is fully supported. The application requires PostgreSQL 15 with pgvector extension for vector embeddings. Render provides managed PostgreSQL with automatic backups, failover, and pgvector support. Database schema is managed via Alembic migrations. No changes to database schema are required.

**Status**: ✅ DATABASE DESIGN COMPLETE

---

## PostgreSQL Configuration

### Render PostgreSQL Service

**Service Type**: PostgreSQL (Render Managed)

**Version**: PostgreSQL 15

**Database Name**: jarvis

**User**: jarvis

**Plan**: Standard (can be upgraded to Pro)

**Extensions**:
- pgvector (required for vector embeddings)
- vector (pgvector alias, required)

**Connection**:
- Private network connectivity
- Automatic SSL/TLS
- Connection pooling available

---

## pgvector Extension

### Extension Details

**Extension Name**: pgvector

**Version**: 0.5.0 (or latest available)

**Purpose**: Vector similarity search for RAG/knowledge base

**Installation**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Render Support**: ✅ SUPPORTED

Render PostgreSQL includes pgvector extension by default. No additional configuration required.

---

## Database Schema

### Schema Management

**Migration Tool**: Alembic

**Migration Location**: `backend/alembic/versions/`

**Current Head**: Latest migration

**Migration Command**: `alembic upgrade head`

**Rollback Command**: `alembic downgrade -1`

### Required Tables

Based on the application, the following tables are expected:

**User Tables**:
- users
- oauth_accounts

**Conversation Tables**:
- conversations
- messages

**Knowledge Base Tables**:
- documents
- document_chunks
- knowledge_bases

**Agent Tables**:
- agents
- agent_executions

**Computer Use Tables**:
- computer_sessions
- computer_commands

**ENUM Types**:
- userrole
- oauthprovider
- conversationstatus
- messagetype
- messagerole

---

## Migration Strategy

### Pre-Deployment Migration

**Method**: Render pre-deploy command or one-time cron job

**Command**: `alembic upgrade head`

**Execution**:
1. PostgreSQL service created first
2. Migration job runs
3. Backend service starts after migration completes

**Verification**:
```bash
alembic current
alembic heads
```

### Migration Verification

**Check Current Version**:
```bash
alembic current
```

**Check Head Version**:
```bash
alembic heads
```

**Verify ENUMs**:
```sql
SELECT enumlabel FROM pg_enum WHERE enumtypid = (
    SELECT oid FROM pg_type WHERE typname = 'userrole'
);
```

**Verify Tables**:
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

**Verify pgvector Extension**:
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

---

## Database URL Configuration

### Render DATABASE_URL Format

**Render Format**: `postgres://user:pass@host:port/db`

**Application Format**: `postgresql+asyncpg://user:pass@host:port/db`

**Conversion Required**: YES

### URL Conversion Options

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

---

## Connection Pooling

### SQLAlchemy Pool Configuration

**Current Configuration**:
```python
DATABASE_POOL_SIZE: int = 20
DATABASE_MAX_OVERFLOW: int = 10
```

**Render Connection Pooling**:
- Render provides PgBouncer for connection pooling
- Can be enabled in Render dashboard
- Recommended for production

**Recommendation**: Enable Render PgBouncer, adjust pool settings if needed

---

## Backup Strategy

### Render Automated Backups

**Backups Included**:
- Daily automated backups
- Point-in-time recovery (PITR)
- 7-day retention (Standard tier)
- 30-day retention (Pro tier)

**Backup Schedule**:
- Daily: 2 AM UTC
- Retention: 7 or 30 days

**Restore Process**:
- Use Render dashboard
- Select point-in-time
- Restore to new database or overwrite

### Custom Backups (Optional)

**Backup Script**: Adapt `scripts/production_backup.ps1`

**Method**:
- Use Render PostgreSQL connection
- Run pg_dump via Render shell or cron job
- Store externally (S3, etc.)

**Recommendation**: Use Render automated backups initially

---

## Database Security

### Security Features

**Authentication**:
- Password authentication
- SSL/TLS required
- Private network only

**Network**:
- Private network connectivity
- No public access
- Internal services only

**Encryption**:
- In transit: SSL/TLS
- At rest: Render disk encryption

**Access Control**:
- Render-managed users
- No direct shell access
- Role-based permissions

---

## Performance Considerations

### Instance Sizing

**Standard Plan**:
- 1 GB RAM
- 1 CPU
- 25 GB storage
- Suitable for initial deployment

**Pro Plan**:
- 8 GB RAM
- 4 CPUs
- 500 GB storage
- Suitable for production load

**Recommendation**: Start with Standard, upgrade to Pro as needed

### Query Optimization

**Indexing**:
- Ensure proper indexes on foreign keys
- Vector indexes on embedding columns
- Indexes on frequently queried columns

**Connection Pooling**:
- Enable Render PgBouncer
- Adjust pool size based on load
- Monitor connection count

---

## Monitoring

### Render Native Monitoring

**Metrics Available**:
- CPU usage
- Memory usage
- Storage usage
- Connection count
- Query performance
- Slow queries

**Logs**:
- Query logs
- Error logs
- Connection logs

**Alerts**:
- High CPU usage
- High memory usage
- Storage full
- Connection errors

### Application Monitoring

**Backend Metrics**: `/metrics` endpoint (Prometheus format)
- Database query time
- Connection pool status
- Error rate

**Recommendation**: Use Render native monitoring initially

---

## Sign-Off

**Database Design Date**: 2026-09-01
**Database Design By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 4 - Database Design for Render
**Status**: ✅ DATABASE DESIGN COMPLETE

**Overall Assessment**: Render PostgreSQL with pgvector extension is fully supported. Database schema managed via Alembic migrations. Migration strategy: pre-deploy command or one-time job. URL format conversion required (postgres:// to postgresql+asyncpg://). Render automated backups provide sufficient backup coverage. Security features include SSL/TLS, private network, and encryption.

**Next Phase**: Phase 5 - Redis Design
