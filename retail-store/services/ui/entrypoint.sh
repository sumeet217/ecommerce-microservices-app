#!/usr/bin/env bash
# ─── UI Service Entrypoint ────────────────────────────────────────────────────
# Collects static files, then starts Gunicorn (Nginx serves /static/).

set -euo pipefail
log() { echo "[entrypoint] $(date -u '+%Y-%m-%dT%H:%M:%SZ') — $*"; }

log "Collecting static files…"
python manage.py collectstatic --noinput --clear

log "Starting Gunicorn on port ${GUNICORN_PORT:-8080}…"
exec gunicorn ui_service.wsgi:application --config gunicorn.conf.py
