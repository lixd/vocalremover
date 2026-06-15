#!/bin/bash
set -e

echo "Running database migrations..."
.venv/bin/python manage.py migrate --noinput

if [ "$WORKER_MODE" = "worker" ]; then
    echo "Starting worker..."
    exec .venv/bin/python manage.py run_worker
else
    echo "Starting API server..."
    exec "$@"
fi
