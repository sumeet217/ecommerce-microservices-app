"""
Orders Service — Cart Service HTTP client.

Calls the Cart Service to:
  1. Fetch the current cart items for a session (used during order placement).
  2. Clear the cart after a successful order.

Uses httpx for synchronous HTTP.
"""

from __future__ import annotations

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

CART_URL: str = getattr(settings, "CART_SERVICE_URL", "http://cart-service:8002")
TIMEOUT: int = getattr(settings, "CART_SERVICE_TIMEOUT", 5)


class CartServiceError(Exception):
    """Raised on unexpected Cart Service responses."""


class EmptyCartError(CartServiceError):
    """Raised when the cart has no items to place an order from."""


def _build_client(session_key: str) -> httpx.Client:
    return httpx.Client(
        base_url=CART_URL,
        timeout=TIMEOUT,
        headers={
            "Accept": "application/json",
            "X-Session-Key": session_key,
            "X-Request-Source": "orders-service",
        },
    )


def get_cart(session_key: str) -> dict:
    """
    Fetch the full cart from the Cart Service for the given session key.

    Returns the cart dict, e.g.:
        {
            "session_key": "abc123",
            "items": [
                {"product_id": 1, "quantity": 2, "price": "999.00",
                 "name": "Widget", "sku": "W-001", "currency": "INR",
                 "subtotal": "1998.00"},
                ...
            ],
            "total_items": 2,
            "subtotal": "1998.00",
            ...
        }

    Raises:
        EmptyCartError    — cart exists but has no items
        CartServiceError  — network / HTTP error
    """
    try:
        with _build_client(session_key) as client:
            response = client.get("/api/v1/cart/")
    except httpx.TimeoutException as exc:
        raise CartServiceError(
            f"Timed out connecting to Cart Service ({CART_URL})."
        ) from exc
    except httpx.RequestError as exc:
        raise CartServiceError(
            f"Network error connecting to Cart Service: {exc}"
        ) from exc

    if response.status_code != 200:
        raise CartServiceError(
            f"Cart Service returned HTTP {response.status_code} fetching cart."
        )

    try:
        data = response.json()
    except Exception as exc:
        raise CartServiceError("Cart Service returned a non-JSON response.") from exc

    if not data.get("items"):
        raise EmptyCartError("The cart is empty. Add items before placing an order.")

    return data


def clear_cart(session_key: str) -> None:
    """
    Issue DELETE /api/v1/cart/clear/ on the Cart Service.

    Errors are logged but NOT re-raised — a failure to clear the cart
    must not roll back an already-committed order (the order is the
    source of truth; the cart is ephemeral).
    """
    try:
        with _build_client(session_key) as client:
            response = client.delete("/api/v1/cart/clear/")
        if response.status_code not in (200, 204):
            logger.warning(
                "Cart clear for session %s returned HTTP %s.",
                session_key,
                response.status_code,
            )
        else:
            logger.info("Cart %s cleared after order placement.", session_key)
    except Exception as exc:
        logger.error(
            "Failed to clear cart for session %s: %s — cart may need manual cleanup.",
            session_key,
            exc,
        )
