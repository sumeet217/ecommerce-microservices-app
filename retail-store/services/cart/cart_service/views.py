"""Cart Service — Health and Readiness probes."""

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return Response(
            {"status": "ok", "service": "cart-service", "version": "1.0.0"},
            status=status.HTTP_200_OK,
        )


class ReadinessCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        checks = {}

        # ── Redis connectivity ─────────────────────────────────────────────────
        try:
            from django.core.cache import cache
            cache.set("_readiness_probe", "ok", timeout=5)
            result = cache.get("_readiness_probe")
            checks["redis"] = "ok" if result == "ok" else "error"
        except Exception as exc:
            logger.error("Redis readiness check failed: %s", exc)
            checks["redis"] = "unavailable"

        all_ok = all(v == "ok" for v in checks.values())
        return Response(
            {
                "status": "ready" if all_ok else "not_ready",
                "service": "cart-service",
                "checks": checks,
            },
            status=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
