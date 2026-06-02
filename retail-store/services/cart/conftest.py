"""
Cart Service — pytest configuration and shared fixtures.

Uses fakeredis so tests run without a live Redis instance.
"""

import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cart_service.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

# ─── Override cache backend with fakeredis before Django sets up ──────────────


def pytest_configure(config):
    """Replace django-redis cache with fakeredis for all tests."""
    from django.conf import settings

    if not settings.configured:
        django.setup()

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "cart-test",
        }
    }


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_cache():
    """Wipe the in-memory cache before every test so carts don't bleed between tests."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def session_key():
    return "test-session-abc123"


@pytest.fixture
def seeded_cart(session_key):
    """
    A cart with one pre-loaded item (product_id=1, qty=2, price=999.00).
    Returns the Cart object so tests can inspect it.
    """
    from apps.cart.models import CartRepository
    cart = CartRepository.add_item(
        session_key=session_key,
        product_id=1,
        quantity=2,
        price="999.00",
        name="Test Product",
        sku="SKU-001",
        currency="INR",
    )
    return cart
