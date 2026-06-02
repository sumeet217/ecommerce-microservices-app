"""
Orders app — Django ORM models.

Entities:
    Order      — the top-level order record belonging to a user session
    OrderItem  — individual line items frozen from the cart at placement time

Status flow (enforced in the service layer, not the DB):
    PENDING → CONFIRMED → SHIPPED → DELIVERED
                       └──────────────────────→ CANCELLED
    PENDING → CANCELLED   (customer-initiated)
    CONFIRMED → CANCELLED (customer-initiated, within policy window)
"""

from __future__ import annotations

import logging
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

logger = logging.getLogger(__name__)


class Order(models.Model):
    """
    Top-level order record.

    user_id is a bare integer (no FK to a User table) so the Orders
    Service stays decoupled from an Auth service.  In a real system
    this would be a UUID referencing the User Service.

    session_key is stored so that the cart can be cleared atomically
    after the order is committed.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    # ── Ownership ─────────────────────────────────────────────────────────────
    user_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Identifier of the ordering user (UUID or session key).",
    )
    session_key = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Cart session key used to place this order.",
    )

    # ── Financials ────────────────────────────────────────────────────────────
    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Sum of all OrderItem subtotals at placement time.",
    )
    currency = models.CharField(max_length=3, default="INR")

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # ── Shipping address (optional — captured at placement) ──────────────────
    shipping_name = models.CharField(max_length=255, blank=True)
    shipping_address_line1 = models.CharField(max_length=512, blank=True)
    shipping_address_line2 = models.CharField(max_length=512, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_pincode = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, default="India", blank=True)

    # ── Notes ─────────────────────────────────────────────────────────────────
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders_order"
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_id", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Order #{self.pk} [{self.status}] — {self.user_id}"

    # ── Status helpers ────────────────────────────────────────────────────────
    @property
    def is_cancellable(self) -> bool:
        from django.conf import settings

        cancellable = getattr(settings, "CANCELLABLE_STATUSES", ["PENDING", "CONFIRMED"])
        return self.status in cancellable

    def transition_to(self, new_status: str) -> None:
        """
        Apply a status transition.  Raises ValueError for illegal moves.

        Valid forward transitions:
            PENDING    → CONFIRMED | CANCELLED
            CONFIRMED  → SHIPPED   | CANCELLED
            SHIPPED    → DELIVERED
            DELIVERED  → (terminal — no further transitions)
            CANCELLED  → (terminal — no further transitions)
        """
        TRANSITIONS: dict[str, list[str]] = {
            self.Status.PENDING: [self.Status.CONFIRMED, self.Status.CANCELLED],
            self.Status.CONFIRMED: [self.Status.SHIPPED, self.Status.CANCELLED],
            self.Status.SHIPPED: [self.Status.DELIVERED],
            self.Status.DELIVERED: [],
            self.Status.CANCELLED: [],
        }
        allowed = TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition order from {self.status!r} to {new_status!r}. "
                f"Allowed: {allowed or ['(none — terminal state)']}"
            )
        self.status = new_status


class OrderItem(models.Model):
    """
    Immutable snapshot of a cart line item at the moment the order was placed.

    Prices are frozen so that future catalog price changes do not
    affect historical orders.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    # ── Product reference (logical FK to Catalog Service) ─────────────────────
    product_id = models.PositiveIntegerField(db_index=True)
    product_name = models.CharField(max_length=512, blank=True)
    product_sku = models.CharField(max_length=64, blank=True)

    # ── Snapshot values ───────────────────────────────────────────────────────
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Price per unit at the time the order was placed.",
    )
    currency = models.CharField(max_length=3, default="INR")

    class Meta:
        db_table = "orders_order_item"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"OrderItem #{self.pk} — product {self.product_id} × {self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))
