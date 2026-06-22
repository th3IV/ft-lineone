#!/bin/bash
set -e

SERVICE_TYPE="${SERVICE_TYPE:-web}"

if [ "$SERVICE_TYPE" = "celery-worker" ]; then
    exec celery -A app.celery_app worker --loglevel=info --concurrency=2
elif [ "$SERVICE_TYPE" = "celery-beat" ]; then
    exec celery -A app.celery_app beat --loglevel=info
else
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
fi
