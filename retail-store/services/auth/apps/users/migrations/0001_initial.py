"""
Initial migration for the CustomUser model.
Creates the 'users' table that token_blacklist and other apps depend on.
"""

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CustomUser",
            fields=[
                # Inherited from AbstractBaseUser
                (
                    "password",
                    models.CharField(max_length=128, verbose_name="password"),
                ),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                # Custom fields
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "email",
                    models.EmailField(db_index=True, max_length=254, unique=True),
                ),
                (
                    "first_name",
                    models.CharField(blank=True, max_length=150),
                ),
                (
                    "last_name",
                    models.CharField(blank=True, max_length=150),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True),
                ),
                (
                    "is_staff",
                    models.BooleanField(default=False),
                ),
                (
                    "is_superuser",
                    models.BooleanField(default=False),
                ),
                (
                    "date_joined",
                    models.DateTimeField(auto_now_add=True),
                ),
            ],
            options={
                "verbose_name": "User",
                "verbose_name_plural": "Users",
                "db_table": "users",
                "ordering": ["-date_joined"],
            },
        ),
    ]
