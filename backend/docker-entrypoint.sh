#!/bin/sh
set -e

echo "Starting database migrations..."
alembic upgrade head
MIGRATION_STATUS=$?
echo "Migration exit status: $MIGRATION_STATUS"
if [ $MIGRATION_STATUS -ne 0 ]; then
    echo "ERROR: Database migration failed with status $MIGRATION_STATUS"
    exit $MIGRATION_STATUS
fi
echo "Current Alembic revision:"
alembic current
echo "Database migrations completed successfully."
echo "Starting Aurexis AI Backend..."

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
