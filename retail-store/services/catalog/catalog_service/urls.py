"""
Catalog Service — Root URL Configuration
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views import HealthCheckView, ReadinessCheckView

urlpatterns = [
    # ── Admin ──────────────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Health & Readiness (used by Docker / k8s probes) ──────────────────────
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("ready/", ReadinessCheckView.as_view(), name="readiness-check"),

    # ── Catalog API v1 ────────────────────────────────────────────────────────
    path("api/v1/catalog/", include("apps.categories.urls", namespace="categories")),
    path("api/v1/catalog/", include("apps.products.urls", namespace="products")),

    # ── OpenAPI Schema ────────────────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
