# ══════════════════════════════════════════════════════════════════════════════
#  UI Service — Multi-stage Dockerfile
#
#  Stage 1 (builder): install Python deps + collect static files
#  Stage 2 (runtime): Nginx + Gunicorn in a single container via supervisord
#    - Nginx on :80  → serves static files, proxies to Gunicorn
#    - Gunicorn on :8080 → Django UI app
# ══════════════════════════════════════════════════════════════════════════════

# ─── Stage 1: Python builder ─────────────────────────────────────────────────
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt /tmp/
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

# Pre-collect static files in the builder so runtime image has them ready
WORKDIR /app
COPY . /app
RUN DJANGO_SECRET_KEY=build-time-placeholder \
    DJANGO_DEBUG=False \
    python manage.py collectstatic --noinput


# ─── Stage 2: Runtime (Nginx + Gunicorn) ─────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="retail-store-dev" \
      service="ui-service" \
      version="1.0.0"

# Install Nginx + supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx \
        supervisor \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root app user (Nginx master still runs as root for :80 binding) ───────
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# ── Copy venv ─────────────────────────────────────────────────────────────────
ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# ── Copy app + collected static files ────────────────────────────────────────
WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /app /app

# ── Nginx config ─────────────────────────────────────────────────────────────
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# ── Supervisord config ────────────────────────────────────────────────────────
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ── Make entrypoint executable ────────────────────────────────────────────────
RUN chmod +x /app/entrypoint.sh

# ── Env defaults ──────────────────────────────────────────────────────────────
ENV DJANGO_SETTINGS_MODULE=ui_service.settings \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GUNICORN_PORT=8080 \
    PORT=80

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost/nginx-health || exit 1

EXPOSE 80

# supervisord manages both Nginx and Gunicorn
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
