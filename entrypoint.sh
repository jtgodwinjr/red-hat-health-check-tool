#!/bin/bash
set -e

DATA_DIR="${HEALTHCHECK_DATA_DIR:-/data}"
mkdir -p "$DATA_DIR"

echo "Running database migrations..."
python backend/manage.py migrate --noinput

echo "Collecting static files..."
python backend/manage.py collectstatic --noinput 2>/dev/null || true

if [ ! -f "$DATA_DIR/admin_token" ]; then
    TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "$TOKEN" > "$DATA_DIR/admin_token"
    echo ""
    echo "========================================"
    echo "  ADMIN ACCESS TOKEN (save this!):"
    echo "  $TOKEN"
    echo "========================================"
    echo ""
fi

echo "Starting Huey consumer in background..."
python backend/manage.py run_huey --workers 2 --quiet &

echo "Starting web server on port ${PORT:-8080}..."
exec gunicorn backend.healthcheck.wsgi:application \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers "${WEB_WORKERS:-2}" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
