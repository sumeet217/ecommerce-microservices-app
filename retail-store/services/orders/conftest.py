"""
Orders Service — pytest configuration and shared fixtures.

Uses pytest-django with a real SQLite test database (no PostgreSQL needed
for unit tests).  Cart Service HTTP calls are always mocked.
"""

import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orders_service.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DJANGO_DEBUG", "True")

# ─── Override database to SQLite for tests ────────────────────────────────────


def pytest_configure(config):
    """Use an in-memory SQLite database instead of PostgreSQL for unit tests."""
    from django.conf import settings

    if not settings.configured:
        django.setup()

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    # Speed up tests — no need for password hashing
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


# ─── Shared fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def user_id():
    return "user-test-001"


@pytest.fixture
def session_key():
    return "session-test-abc123"


@pytest.fixture
def mock_cart_items():
    """A realistic mock cart payload returned by the Cart Service."""
    return {
        "session_key": "session-test-abc123",
        "items": [
            {
                "product_id": 1,
                "quantity": 2,
                "price": "999.00",
                "name": "Wireless Headphones",
                "sku": "WH-001",
                "currency": "INR",
                "subtotal": "1998.00",
            },
            {
                "product_id": 2,
                "quantity": 1,
                "price": "499.00",
                "name": "USB Cable",
                "sku": "UC-002",
                "currency": "INR",
                "subtotal": "499.00",
            },
        ],
        "total_items": 3,
        "subtotal": "2497.00",
        "currency": "INR",
    }
