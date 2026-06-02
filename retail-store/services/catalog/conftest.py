"""
Root conftest — pytest configuration and shared fixtures for catalog service.
"""

import django
import os
import pytest

# Ensure Django settings are configured before test collection
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "catalog_service.settings")


@pytest.fixture(scope="session")
def django_db_setup():
    """Use a test database for all tests."""
    pass
