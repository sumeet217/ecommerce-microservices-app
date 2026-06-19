"""
Auth Service — pytest configuration and shared fixtures.

Uses pytest-django with a real SQLite test database (no PostgreSQL needed
for unit tests). All JWT operations work against SQLite.
"""

import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_service.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production-auth-svc")
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
    # Speed up tests — faster hashing, still functionally correct
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    # Disable token blacklist for simple tests (re-enabled in integration tests)
    # Keep blacklist app installed so migrations run correctly


# ─── Shared fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def user_data():
    """Default valid registration payload."""
    return {
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "StrongPass123!",
        "password_confirm": "StrongPass123!",
    }


@pytest.fixture
def registered_user(db):
    """A saved CustomUser instance created via the manager."""
    from tests.factories import UserFactory

    return UserFactory()


@pytest.fixture
def auth_client(api_client, registered_user):
    """APIClient pre-authenticated with a valid JWT access token."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(registered_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client, registered_user
