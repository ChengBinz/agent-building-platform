#!/bin/sh
set -e

echo "Running database migrations..."

# Run migration fix script first, then upgrade
python scripts/fix_migration.py
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
