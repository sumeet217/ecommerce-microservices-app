#!/usr/bin/env bash
# ─── Cart Service Entrypoint ──────────────────────────────────────────────────
# Waits for Redis to be reachable, then starts Gunicorn.
# No database migrations needed — all cart data lives in Redis.

set -euo pipefail

log() { echo "[entrypoint] $(date -u '+%Y-%m-%dT%H:%M:%SZ') — $*"; }

# ── 1. Wait for Redis ─────────────────────────────────────────────────────────
REDIS_URL="${REDIS_URL:-redis://redis:6379/0}"
# Extract host and port from REDIS_URL (supports redis://host:port/db)
REDIS_HOST=$(python -c "from urllib.parse import urlparse; u=urlparse('${REDIS_URL}'); print(u.hostname or 'redis')")
REDIS_PORT=$(python -c "from urllib.parse import urlparse; u=urlparse('${REDIS_URL}'); print(u.port or 6379)")

MAX_RETRIES=30
RETRY_INTERVAL=2

log "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
for i in $(seq 1 $MAX_RETRIES); do
    if python -c "
import sys, redis as r
try:
    c = r.Redis(host='${REDIS_HOST}', port=${REDIS_PORT}, socket_connect_timeout=3)
    c.ping()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
        log "Redis is ready."
        break
    fi
    log "  attempt $i/$MAX_RETRIES — retrying in ${RETRY_INTERVAL}s..."
    sleep "$RETRY_INTERVAL"
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        log "ERROR: Redis did not become ready in time. Aborting."
        exit 1
    fi
done

# ── 2. Start Gunicorn ──────────────────────────────────────────────────────────
log "Starting Gunicorn on port ${PORT:-8002}..."
exec gunicorn cart_service.wsgi:application \
    --config gunicorn.conf.py
