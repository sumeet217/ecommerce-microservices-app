"""
Orders Service — business-logic service layer.

Keeps views thin by handling:
    - Fetching cart from Cart Service
    - Atomically creating Order + OrderItems
    - Clearing the cart post-commit
    - Status transitions
"""

from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction

from .cart_client import CartServiceError, EmptyCartError, clear_cart, get_cart
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


# ─── Order placement ─────────────────────────────────────────────────────────


def place_order(
    user_id: str,
    session_key: str,
    shipping: dict | None = None,
    notes: str = "",
) -> Order:
    """
    Place a new order by pulling items from the Cart Service.

    Steps:
        1. Fetch the cart (raises EmptyCartError / CartServiceError)
        2. Atomically create Order + OrderItems in a DB transaction
        3. Fire-and-forget: clear the cart (errors are logged, not raised)

    Returns the saved Order instance (with prefetched items).

    Raises:
        EmptyCartError    — cart is empty
        CartServiceError  — cannot reach Cart Service
        ValueError        — cart data is malformed
    """
    shipping = shipping or {}

    # ── Step 1: Fetch cart ────────────────────────────────────────────────────
    cart_data = get_cart(session_key)  # raises on error or empty cart
    cart_items: list[dict] = cart_data.get("items", [])

    if not cart_items:
        raise EmptyCartError("The cart is empty. Add items before placing an order.")

    # ── Step 2: Persist order + items atomically ───────────────────────────────
    with transaction.atomic():
        # Compute total from the cart's own subtotals (already validated by
        # the Cart Service against the Catalog price)
        total_price = sum(
            Decimal(str(item.get("subtotal", "0.00"))) for item in cart_items
        ).quantize(Decimal("0.01"))

        order = Order.objects.create(
            user_id=user_id,
            session_key=session_key,
            status=Order.Status.PENDING,
            total_price=total_price,
            currency=cart_data.get("currency", "INR"),
            shipping_name=shipping.get("name", ""),
            shipping_address_line1=shipping.get("address_line1", ""),
            shipping_address_line2=shipping.get("address_line2", ""),
            shipping_city=shipping.get("city", ""),
            shipping_pincode=shipping.get("pincode", ""),
            shipping_country=shipping.get("country", "India"),
            notes=notes,
        )

        order_items = []
        for item in cart_items:
            try:
                order_items.append(
                    OrderItem(
                        order=order,
                        product_id=int(item["product_id"]),
                        product_name=item.get("name", ""),
                        product_sku=item.get("sku", ""),
                        quantity=int(item["quantity"]),
                        unit_price=Decimal(str(item["price"])),
                        currency=item.get("currency", "INR"),
                    )
                )
            except (KeyError, ValueError, TypeError) as exc:
                raise ValueError(
                    f"Malformed cart item — could not create order line: {exc}"
                ) from exc

        OrderItem.objects.bulk_create(order_items)

    logger.info(
        "Order #%s placed for user %s — %d items, total %s.",
        order.pk,
        user_id,
        len(order_items),
        total_price,
    )

    # ── Step 3: Clear cart (best-effort) ──────────────────────────────────────
    clear_cart(session_key)

    # Reload with items
    return Order.objects.prefetch_related("items").get(pk=order.pk)


# ─── Order cancellation ───────────────────────────────────────────────────────


def cancel_order(order: Order, reason: str = "") -> Order:
    """
    Cancel an order.  Only PENDING / CONFIRMED orders may be cancelled
    (configurable via CANCELLABLE_STATUSES in settings).

    Raises:
        ValueError — order is not in a cancellable status
    """
    if not order.is_cancellable:
        raise ValueError(
            f"Order #{order.pk} cannot be cancelled "
            f"(current status: {order.status!r})."
        )

    order.transition_to(Order.Status.CANCELLED)
    order.cancellation_reason = reason
    order.save(update_fields=["status", "cancellation_reason", "updated_at"])

    logger.info(
        "Order #%s cancelled (was %s). Reason: %r",
        order.pk,
        order.status,
        reason,
    )
    return order
