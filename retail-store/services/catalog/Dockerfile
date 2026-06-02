# ══════════════════════════════════════════════════════════════════════════════
#  Catalog Service — Multi-stage Dockerfile
#  Stage 1 (builder): install Python deps into a venv
#  Stage 2 (runtime): copy the venv, run as non-root user
# ══════════════════════════════════════════════════════════════════════════════

# ─── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install OS-level build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create an isolated virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt


# ─── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="retail-store-dev" \
      service="catalog-service" \
      version="1.0.0"

# Install runtime-only OS dependencies (no build tools)
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

# ── Create directories for static/media files ────────────────────────────────
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appgroup /app/staticfiles /app/media

# ── Make entrypoint executable ────────────────────────────────────────────────
RUN chmod +x /app/entrypoint.sh

# ── Environment defaults (overridden at runtime by docker-compose / k8s) ──────
ENV DJANGO_SETTINGS_MODULE=catalog_service.settings \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# ── Switch to non-root ─────────────────────────────────────────────────────────
USER appuser

# ── Health check (uses the /health/ endpoint) ──────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/ || exit 1

EXPOSE ${PORT}

ENTRYPOINT ["/app/entrypoint.sh"]
