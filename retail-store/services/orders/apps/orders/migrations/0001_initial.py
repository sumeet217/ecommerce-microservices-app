"""
Django database migration — initial schema for Orders Service.

Creates:
    orders_order      — top-level order record
    orders_order_item — line items frozen from the cart at placement time
"""

from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "user_id",
                    models.CharField(
                        db_index=True,
                        help_text="Identifier of the ordering user (UUID or session key).",
                        max_length=255,
                    ),
                ),
                (
                    "session_key",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="Cart session key used to place this order.",
                        max_length=255,
                    ),
                ),
                (
                    "total_price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Sum of all OrderItem subtotals at placement time.",
                        max_digits=14,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                    ),
                ),
                ("currency", models.CharField(default="INR", max_length=3)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("CONFIRMED", "Confirmed"),
                            ("SHIPPED", "Shipped"),
                            ("DELIVERED", "Delivered"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("shipping_name", models.CharField(blank=True, max_length=255)),
                ("shipping_address_line1", models.CharField(blank=True, max_length=512)),
                ("shipping_address_line2", models.CharField(blank=True, max_length=512)),
                ("shipping_city", models.CharField(blank=True, max_length=100)),
                ("shipping_pincode", models.CharField(blank=True, max_length=20)),
                (
                    "shipping_country",
                    models.CharField(blank=True, default="India", max_length=100),
                ),
                ("notes", models.TextField(blank=True)),
                ("cancellation_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Order",
                "verbose_name_plural": "Orders",
                "db_table": "orders_order",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.order",
                    ),
                ),
                ("product_id", models.PositiveIntegerField(db_index=True)),
                ("product_name", models.CharField(blank=True, max_length=512)),
                ("product_sku", models.CharField(blank=True, max_length=64)),
                (
                    "quantity",
                    models.PositiveIntegerField(
                        validators=[django.core.validators.MinValueValidator(1)]
                    ),
                ),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Price per unit at the time the order was placed.",
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                    ),
                ),
                ("currency", models.CharField(default="INR", max_length=3)),
            ],
            options={
                "verbose_name": "Order Item",
                "verbose_name_plural": "Order Items",
                "db_table": "orders_order_item",
                "ordering": ["id"],
            },
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["user_id", "status"], name="orders_orde_user_id_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(
                fields=["status", "created_at"], name="orders_orde_status_idx"
            ),
        ),
    ]
