# PRODUCTION BACKUP/RESTORE RUNBOOK

**Date**: 2026-08-25
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: FINAL GO-LIVE DEPLOYMENT & PRODUCTION HANDOVER
**Phase**: Phase 4 - Production Database Backup

---

## Executive Summary

This runbook documents the backup and restore procedures for the Jarvis AI production PostgreSQL database. Automated backup scripts have been created to ensure data safety before migrations and for regular disaster recovery.

**Status**: ✅ BACKUP PROCEDURES IMPLEMENTED

---

## Backup Procedures

### Automated Backup Script

**Location**: `scripts/production_backup.ps1`

**Purpose**: Automated PostgreSQL database backup with compression and integrity verification

**Usage**:
```powershell
# Basic backup
.\scripts\production_backup.ps1

# Custom project name
.\scripts\production_backup.ps1 -ProjectName "jarvis-production"

# Backup without compression
.\scripts\production_backup.ps1 -Compress:$false
```

**Parameters**:
- `ProjectName`: Docker Compose project name (default: jarvis-production)
- `PostgresService`: PostgreSQL service name (default: postgres)
- `PostgresUser`: PostgreSQL user (default: jarvis)
- `PostgresDb`: Database name (default: jarvis)
- `BackupDir`: Backup directory (default: backups)
- `Compress`: Compress backup file (default: true)

**Backup Location**: `backups/` directory in project root

**Backup Filename Format**: `jarvis_backup_YYYYMMDD_HHMMSS.sql` (or .sql.gz if compressed)

**Backup Process**:
1. Verify Docker Compose availability
2. Verify PostgreSQL container is running
3. Create backup directory if not exists
4. Generate timestamped backup filename
5. Execute pg_dump inside PostgreSQL container
6. Verify backup file exists and has content
7. Compress backup file (if enabled)
8. Test backup integrity
9. Generate backup metadata file

**Backup Metadata**: Each backup includes a `.metadata.json` file with:
- timestamp
- filename
- size
- database name
- PostgreSQL version
- project name

---

## Restore Procedures

### Automated Restore Script

**Location**: `scripts/production_restore.ps1`

**Purpose**: Automated PostgreSQL database restore from backup with safety checks

**Usage**:
```powershell
# Interactive restore (requires confirmation)
.\scripts\production_restore.ps1 -BackupFile "backups/jarvis_backup_20260825_120000.sql.gz"

# Force restore (no confirmation)
.\scripts\production_restore.ps1 -BackupFile "backups/jarvis_backup_20260825_120000.sql.gz" -Force

# Dry run (no changes)
.\scripts\production_restore.ps1 -BackupFile "backups/jarvis_backup_20260825_120000.sql.gz" -DryRun
```

**Parameters**:
- `BackupFile`: Path to backup file (required)
- `ProjectName`: Docker Compose project name (default: jarvis-production)
- `PostgresService`: PostgreSQL service name (default: postgres)
- `PostgresUser`: PostgreSQL user (default: jarvis)
- `PostgresDb`: Database name (default: jarvis)
- `Force`: Skip confirmation prompt (default: false)
- `DryRun`: Validate without making changes (default: false)

**Restore Process**:
1. Verify Docker Compose availability
2. Verify PostgreSQL container is running
3. Verify backup file exists and has content
4. Test backup integrity
5. Confirm restore (unless -Force)
6. Create pre-restore backup of current database
7. Drop existing database
8. Create new database
9. Restore from backup file
10. Verify restore success

**Safety Features**:
- Pre-restore backup automatically created
- Confirmation prompt (unless -Force)
- Dry run mode for validation
- Integrity checks before restore
- Verification after restore

---

## Backup Schedule

### Recommended Backup Schedule

**Daily Backups**:
- Time: 2:00 AM UTC (low traffic period)
- Retention: 7 days
- Compression: Enabled
- Location: `backups/daily/`
- **Security**: Note: Backup files not encrypted (see SECURITY section)

**Weekly Backups**:
- Time: Sunday 2:00 AM UTC
- Retention: 4 weeks
- Compression: Enabled
- Location: `backups/weekly/`
- **Security**: Note: Backup files not encrypted (see SECURITY section)

**Monthly Backups**:
- Time: 1st of month 2:00 AM UTC
- Retention: 12 months
- Compression: Enabled
- Location: `backups/monthly/`
- **Security**: Note: Backup files not encrypted (see SECURITY section)

### Pre-Migration Backups

**Before Any Migration**:
- Always create a backup before running `alembic upgrade head`
- Use timestamp format: `pre_migration_YYYYMMDD_HHMMSS.sql`
- Retain until migration is verified successful
- Label with migration version: `pre_migration_001_YYYYMMDD_HHMMSS.sql`

---

## Backup Verification

### Manual Verification Steps

1. **Check Backup File Exists**:
```powershell
Test-Path backups/jarvis_backup_20260825_120000.sql.gz
```

2. **Check Backup File Size**:
```powershell
(Get-Item backups/jarvis_backup_20260825_120000.sql.gz).Length
```

3. **Test Gzip Integrity**:
```powershell
gzip -t backups/jarvis_backup_20260825_120000.sql.gz
```

4. **Verify Backup Metadata**:
```powershell
Get-Content backups/jarvis_backup_20260825_120000.sql.gz.metadata.json
```

5. **Test Restore to Isolated Database** (recommended):
```powershell
# Create isolated test database
docker-compose -p jarvis-test exec -T postgres psql -U jarvis -d postgres -c "CREATE DATABASE test_restore;"

# Restore to test database
.\scripts\production_restore.ps1 -BackupFile "backups/jarvis_backup_20260825_120000.sql.gz" -ProjectName "jarvis-test" -PostgresDb "test_restore"

# Verify tables
docker-compose -p jarvis-test exec -T postgres psql -U jarvis -d test_restore -c "\dt"

# Clean up
docker-compose -p jarvis-test exec -T postgres psql -U jarvis -d postgres -c "DROP DATABASE test_restore;"
```

---

## Disaster Recovery Procedures

### Scenario 1: Database Corruption

**Symptoms**:
- Application errors related to database
- PostgreSQL container crashes
- Data inconsistency

**Recovery Steps**:
1. Stop application services
2. Identify most recent good backup
3. Run restore script with pre-restore backup
4. Verify restore success
5. Restart application services
6. Monitor for errors

**Command**:
```powershell
.\scripts\production_restore.ps1 -BackupFile "backups/jarvis_backup_20260825_120000.sql.gz" -Force
```

### Scenario 2: Migration Failure

**Symptoms**:
- Migration script fails
- Database schema inconsistent
- Application won't start

**Recovery Steps**:
1. Stop application services
2. Identify pre-migration backup
3. Restore from pre-migration backup
4. Investigate migration failure
5. Fix migration script
6. Re-run migration
7. Verify success

**Command**:
```powershell
.\scripts\production_restore.ps1 -BackupFile "backups/pre_migration_001_20260825_120000.sql.gz" -Force
```

### Scenario 3: Accidental Data Deletion

**Symptoms**:
- User reports missing data
- Tables truncated or dropped
- Critical data lost

**Recovery Steps**:
1. Stop application services immediately
2. Identify backup before data loss
3. Restore from that backup
4. Verify data restoration
5. Restart application services
6. Investigate cause of deletion

**Command**:
```powershell
.\scripts\production_restore.ps1 -BackupFile "backups/jarvis_backup_20260825_100000.sql.gz" -Force
```

---

## Rollback Procedures

### Migration Rollback

**Important**: Alembic downgrade may not be safe for all migrations. Always test downgrade in isolated environment first.

**Rollback Steps**:
1. Stop application services
2. Restore from pre-migration backup
3. Verify database state
4. Restart application services
5. Monitor for errors

**Command**:
```powershell
.\scripts\production_restore.ps1 -BackupFile "backups/pre_migration_001_20260825_120000.sql.gz" -Force
```

**Note**: Do not rely on `alembic downgrade` unless it has been tested and designed for that migration. The current migration uses raw SQL and may not have a safe downgrade path.

---

## Backup Storage

### Local Storage

**Location**: `backups/` directory in project root

**Structure**:
```
backups/
├── daily/
│   ├── jarvis_backup_20260825_020000.sql.gz
│   ├── jarvis_backup_20260824_020000.sql.gz
│   └── ...
├── weekly/
│   ├── jarvis_backup_20260825_020000.sql.gz
│   ├── jarvis_backup_20260818_020000.sql.gz
│   └── ...
├── monthly/
│   ├── jarvis_backup_20260801_020000.sql.gz
│   ├── jarvis_backup_20260701_020000.sql.gz
│   └── ...
└── pre_migration/
    ├── pre_migration_001_20260825_120000.sql.gz
    └── ...
```

### Offsite Storage (Recommended)

**Options**:
- AWS S3 with lifecycle policies
- Google Cloud Storage
- Azure Blob Storage
- Backblaze B2
- rsync to remote server

**Recommendation**: Implement automated offsite backup sync using cron job or CI/CD pipeline.

---

## Monitoring

### Backup Monitoring

**Metrics to Monitor**:
- Backup success/failure
- Backup file size
- Backup duration
- Backup retention compliance
- Disk space usage

**Alerting**:
- Alert on backup failure
- Alert on backup size anomalies
- Alert on disk space < 20%
- Alert on backup age > 24 hours

### Restore Monitoring

**Metrics to Monitor**:
- Restore success/failure
- Restore duration
- Database verification results
- Application health after restore

---

## Security Considerations

### Backup Security

**Encryption**: Backups are not encrypted by default. Consider implementing:
- GPG encryption for backup files
- Encrypted storage (S3 with SSE)
- At-rest encryption for backup directory

**Access Control**:
- Restrict access to backup directory
- Use file system permissions
- Audit backup access logs

**Secrets in Backups**:
- Backups may contain sensitive data
- Treat backups as sensitive as the database itself
- Implement same security controls as database

### Restore Security

**Authorization**:
- Only authorized personnel should perform restores
- Require approval for production restores
- Audit all restore operations

**Validation**:
- Verify backup source before restore
- Verify backup integrity before restore
- Verify restore success after restore

---

## Troubleshooting

### Backup Fails

**Symptoms**: Backup script exits with error

**Common Causes**:
1. PostgreSQL container not running
2. Docker Compose not available
3. Insufficient disk space
4. Database connection issues

**Solutions**:
1. Check PostgreSQL container status: `docker ps`
2. Check Docker Compose: `docker-compose --version`
3. Check disk space: `Get-PSDrive C`
4. Check database connectivity: `docker-compose exec postgres psql -U jarvis -d jarvis -c "SELECT 1;"`

### Restore Fails

**Symptoms**: Restore script exits with error

**Common Causes**:
1. Backup file corrupted
2. PostgreSQL container not running
3. Insufficient permissions
4. Database in use by active connections

**Solutions**:
1. Verify backup integrity: `gzip -t backup.sql.gz`
2. Check PostgreSQL container status: `docker ps`
3. Stop application services before restore
4. Kill active connections: `docker-compose exec postgres psql -U jarvis -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'jarvis' AND pid <> pg_backend_pid();"`

### Backup File Too Large

**Symptoms**: Backup file size is unexpectedly large

**Common Causes**:
1. Large tables not excluded
2. Binary data in database
3. No compression enabled

**Solutions**:
1. Exclude large tables from backup
2. Enable compression
3. Implement table-level backup strategy

---

## Testing

### Backup Testing

**Test Frequency**: Weekly

**Test Procedure**:
1. Run backup script
2. Verify backup file exists
3. Test backup integrity
4. Restore to isolated database
5. Verify data consistency
6. Clean up test database

**Command**:
```powershell
.\scripts\production_backup.ps1
.\scripts\production_restore.ps1 -BackupFile "backups/jarvis_backup_YYYYMMDD_HHMMSS.sql.gz" -ProjectName "jarvis-test" -PostgresDb "test_restore" -DryRun
```

### Restore Testing

**Test Frequency**: Monthly

**Test Procedure**:
1. Create isolated test environment
2. Restore from recent backup
3. Run application smoke tests
4. Verify data integrity
5. Clean up test environment

**Command**:
```powershell
.\scripts\production_restore.ps1 -BackupFile "backups/jarvis_backup_YYYYMMDD_HHMMSS.sql.gz" -ProjectName "jarvis-test" -PostgresDb "test_restore"
```

---

## Sign-Off

**Runbook Date**: 2026-08-25
**Runbook By**: Cascade AI Assistant
**EPIC**: FINAL GO-LIVE DEPLOYMENT & PRODUCTION HANDOVER
**Phase**: Phase 4 - Production Database Backup
**Status**: COMPLETED

**Artifacts Created**:
- `scripts/production_backup.ps1` - Automated backup script
- `scripts/production_restore.ps1` - Automated restore script
- `reports/PRODUCTION_BACKUP_RESTORE_RUNBOOK.md` - This runbook

**Next Steps**:
1. Test backup script in production-like environment
2. Test restore script in isolated environment
3. Implement automated backup schedule
4. Configure offsite backup storage
5. Set up backup monitoring and alerting
