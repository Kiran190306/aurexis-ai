#!/bin/sh
set -e

echo "=== ALEMBIC FORENSIC DIAGNOSTIC ==="
echo "Working directory: $(pwd)"
echo "=== /app CONTENTS ==="
ls -la /app
echo "=== ALEMBIC DIRECTORY ==="
ls -la /app/alembic
echo "=== ALEMBIC VERSIONS ==="
find /app/alembic -maxdepth 2 -type f -print

echo "=== ALEMBIC HEADS ==="
alembic heads
HEAD_STATUS=$?
echo "alembic heads exit status: $HEAD_STATUS"

echo "=== ALEMBIC HISTORY ==="
alembic history
HISTORY_STATUS=$?
echo "alembic history exit status: $HISTORY_STATUS"

echo "=== ALEMBIC CURRENT ==="
alembic current
CURRENT_STATUS=$?
echo "alembic current exit status: $CURRENT_STATUS"

echo "=== ALEMBIC CURRENT VERBOSE ==="
alembic current --verbose
VERBOSE_STATUS=$?
echo "alembic current verbose exit status: $VERBOSE_STATUS"

echo "=== ALEMBIC UPGRADE SQL ==="
alembic upgrade head --sql
SQL_STATUS=$?
echo "alembic upgrade --sql exit status: $SQL_STATUS"

echo "=== ALEMBIC UPGRADE ==="
alembic upgrade head
UPGRADE_STATUS=$?
echo "alembic upgrade exit status: $UPGRADE_STATUS"

echo "=== ALEMBIC CURRENT AFTER UPGRADE ==="
alembic current
POST_STATUS=$?
echo "alembic current after upgrade exit status: $POST_STATUS"

echo "Database migrations completed successfully."
echo "Starting Aurexis AI Backend..."

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
