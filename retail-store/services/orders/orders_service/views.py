"""Orders Service — Health and Readiness probes."""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """GET /health/ — liveness probe."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return Response(
            {"status": "ok", "service": "orders-service", "version": "1.0.0"},
            status=status.HTTP_200_OK,
        )


class ReadinessCheckView(APIView):
    """GET /ready/ — readiness probe (verifies DB connectivity)."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        checks = {}

        # ── PostgreSQL connectivity ────────────────────────────────────────
        try:
            from django.db import connection

            connection.ensure_connection()
            checks["postgres"] = "ok"
        except Exception as exc:
            logger.error("PostgreSQL readiness check failed: %s", exc)
            checks["postgres"] = "unavailable"

        all_ok = all(v == "ok" for v in checks.values())
        return Response(
            {
                "status": "ready" if all_ok else "not_ready",
                "service": "orders-service",
                "checks": checks,
            },
            status=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
