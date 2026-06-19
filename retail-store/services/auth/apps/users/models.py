"""
Auth Service — CustomUser Model

Uses AbstractBaseUser so email is the primary login identifier.
Django's default AbstractBaseUser provides: password, last_login,
is_active. We add: email, first_name, last_name, is_staff,
is_superuser, date_joined.
"""

import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager that uses email instead of username as the unique identifier."""

    def create_user(self, email: str, password: str = None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    """
    Custom user model where email is the unique login identifier.

    Fields
    ------
    id           : UUID primary key — avoids sequential integer enumeration.
    email        : Unique user identifier; used for login.
    first_name   : User's first / given name.
    last_name    : User's family name.
    is_active    : Soft-delete / account enable flag (default True).
    is_staff     : Grants Django admin access.
    is_superuser : Full permission bypass.
    date_joined  : Timestamp when the account was created.
    last_login   : Inherited from AbstractBaseUser; updated by JWT on login.
    password     : Inherited from AbstractBaseUser; stored as PBKDF2 hash.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    # Use email as the unique identifier for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        """Return the short name for the user."""
        return self.first_name

    def has_perm(self, perm, obj=None):
        """Full permissions for superusers."""
        return self.is_superuser

    def has_module_perms(self, app_label):
        """Full module permissions for superusers."""
        return self.is_superuser
