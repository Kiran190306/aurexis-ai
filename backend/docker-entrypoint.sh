#!/bin/sh
set -e

echo "Starting database migrations..."
echo "Working directory: $(pwd)"
echo "Alembic files:"
ls -la /app/alembic/versions/
echo "Running alembic heads:"
alembic heads
echo "Running alembic history:"
alembic history
echo "Running alembic upgrade head:"
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
