#!/usr/bin/env bash
# ─── Auth Service Entrypoint ──────────────────────────────────────────────────
# Waits for PostgreSQL, runs migrations, then starts Gunicorn.

set -euo pipefail

log() { echo "[entrypoint] $(date -u '+%Y-%m-%dT%H:%M:%SZ') — $*"; }

# ── 1. Wait for PostgreSQL ─────────────────────────────────────────────────────
DB_HOST="${DB_HOST:-auth-db}"
DB_PORT="${DB_PORT:-5432}"
MAX_RETRIES=30
RETRY_INTERVAL=2

log "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
for i in $(seq 1 $MAX_RETRIES); do
    if python -c "
import sys, psycopg2, os
try:
    psycopg2.connect(
        host=os.environ.get('DB_HOST', 'auth-db'),
        port=int(os.environ.get('DB_PORT', 5432)),
        dbname=os.environ.get('DB_NAME', 'auth_db'),
        user=os.environ.get('DB_USER', 'auth_user'),
        password=os.environ.get('DB_PASSWORD', 'auth_pass'),
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

# ── 3. Start Gunicorn ──────────────────────────────────────────────────────────
log "Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn auth_service.wsgi:application \
    --config gunicorn.conf.py
