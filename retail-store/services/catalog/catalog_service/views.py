"""
Catalog Service — Health & Readiness probe views.
Used by Docker HEALTHCHECK, load-balancers, and orchestrators.
"""

import logging

from django.db import connection, OperationalError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Liveness probe — returns 200 as long as the process is running.
    Does NOT check downstream dependencies.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "status": "ok",
                "service": "catalog-service",
                "version": "1.0.0",
            },
            status=status.HTTP_200_OK,
        )


class ReadinessCheckView(APIView):
    """
    Readiness probe — verifies the service can handle traffic.
    Checks DB connectivity before reporting ready.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        checks = {}

        # ── Database ──────────────────────────────────────────────────────────
        try:
            connection.ensure_connection()
            checks["database"] = "ok"
        except OperationalError as exc:
            logger.error("Database readiness check failed: %s", exc)
            checks["database"] = "unavailable"

        all_ok = all(v == "ok" for v in checks.values())
        http_status = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(
            {
                "status": "ready" if all_ok else "not_ready",
                "service": "catalog-service",
                "checks": checks,
            },
            status=http_status,
        )
