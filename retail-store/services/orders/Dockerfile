# ══════════════════════════════════════════════════════════════════════════════
#  Orders Service — Multi-stage Dockerfile
#  Stage 1 (builder): install Python deps into an isolated venv
#  Stage 2 (runtime): copy the venv, run as non-root user
# ══════════════════════════════════════════════════════════════════════════════

# ─── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt


# ─── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="retail-store-dev" \
      service="orders-service" \
      version="1.0.0"

# Runtime-only OS packages (libpq5 for psycopg2, curl for health check)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user ──────────────────────────────────────────────────────────────
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

# ── Copy virtual environment from builder ──────────────────────────────────────
ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# ── Application files ─────────────────────────────────────────────────────────
WORKDIR /app
COPY --chown=appuser:appgroup . /app

# ── Make entrypoint executable ────────────────────────────────────────────────
RUN chmod +x /app/entrypoint.sh

# ── Environment defaults ──────────────────────────────────────────────────────
ENV DJANGO_SETTINGS_MODULE=orders_service.settings \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8003

# ── Switch to non-root ─────────────────────────────────────────────────────────
USER appuser

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/ || exit 1

EXPOSE ${PORT}

ENTRYPOINT ["/app/entrypoint.sh"]
