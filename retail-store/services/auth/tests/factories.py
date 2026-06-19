"""
Auth Service — Test Factories

Uses factory_boy to create CustomUser instances for tests.
"""

import factory
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    """Factory for creating CustomUser instances with realistic data."""

    class Meta:
        model = "users.CustomUser"
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "StrongPass123!")
    is_active = True
    is_staff = False
    is_superuser = False


class AdminUserFactory(UserFactory):
    """Factory for creating admin/superuser instances."""

    email = factory.Sequence(lambda n: f"admin{n}@example.com")
    is_staff = True
    is_superuser = True


class InactiveUserFactory(UserFactory):
    """Factory for creating deactivated user accounts."""

    email = factory.Sequence(lambda n: f"inactive{n}@example.com")
    is_active = False
