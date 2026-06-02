#!/usr/bin/env bash
# ─── Catalog Service Entrypoint ───────────────────────────────────────────────
# Waits for the database, applies migrations, and starts Gunicorn.
# Designed to run inside Docker as a non-root user.

set -euo pipefail

log() { echo "[entrypoint] $(date -u '+%Y-%m-%dT%H:%M:%SZ') — $*"; }

# ── 1. Wait for PostgreSQL ─────────────────────────────────────────────────────
DB_HOST="${DB_HOST:-catalog-db}"
DB_PORT="${DB_PORT:-5432}"
MAX_RETRIES=30
RETRY_INTERVAL=2

log "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
for i in $(seq 1 $MAX_RETRIES); do
    if python -c "
import sys, psycopg2, os
try:
    psycopg2.connect(
        host=os.environ.get('DB_HOST', 'catalog-db'),
        port=int(os.environ.get('DB_PORT', 5432)),
        dbname=os.environ.get('DB_NAME', 'catalog_db'),
        user=os.environ.get('DB_USER', 'catalog_user'),
        password=os.environ.get('DB_PASSWORD', 'catalog_pass'),
        connect_timeout=3,
    )
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
        log "PostgreSQL is ready."
        break
    fi
    log "  attempt $i/$MAX_RETRIES — retrying in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        log "ERROR: PostgreSQL did not become ready in time. Aborting."
        exit 1
    fi
done

# ── 2. Apply migrations ────────────────────────────────────────────────────────
log "Running database migrations..."
python manage.py migrate --noinput

# ── 3. Collect static files ────────────────────────────────────────────────────
log "Collecting static files..."
python manage.py collectstatic --noinput --clear

# ── 4. Create superuser (dev only, controlled by env var) ──────────────────────
if [ "${CREATE_SUPERUSER:-false}" = "true" ]; then
    log "Creating Django superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME:-admin}').exists():
    User.objects.create_superuser(
        '${DJANGO_SUPERUSER_USERNAME:-admin}',
        '${DJANGO_SUPERUSER_EMAIL:-admin@example.com}',
        '${DJANGO_SUPERUSER_PASSWORD:-adminpass123}',
    )
    print('Superuser created.')
else:
    print('Superuser already exists.')
"
fi

# ── 5. Seed demo data (dev only) ───────────────────────────────────────────────
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
    log "Seeding demo catalog data..."
    python manage.py seed_catalog
fi

# ── 6. Start Gunicorn ──────────────────────────────────────────────────────────
log "Starting Gunicorn..."
exec gunicorn catalog_service.wsgi:application \
    --config gunicorn.conf.py
