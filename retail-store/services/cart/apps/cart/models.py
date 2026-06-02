"""
Cart models — schema + Redis repository.

There is no relational database in this service.
CartItem is a plain dataclass used for validation and serialisation.
The CartRepository class handles all reads/writes to Redis via Django's
cache framework (backed by django-redis).

Redis key layout:
    cart:<session_key>          → JSON dict  {product_id: {qty, price, name, sku}}
    cart:<session_key>:meta     → JSON dict  {created_at, updated_at}
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ─── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class CartItem:
    """
    A single line-item in the cart.

    Fields mirror what the Catalog Service returns for a product,
    plus the quantity the customer wants to purchase.
    """

    product_id: int
    quantity: int
    price: str          # stored as string to avoid float precision issues
    name: str = ""
    sku: str = ""
    currency: str = "INR"

    # ── Derived ───────────────────────────────────────────────────────────────
    @property
    def subtotal(self) -> Decimal:
        return (Decimal(self.price) * self.quantity).quantize(Decimal("0.01"))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["subtotal"] = str(self.subtotal)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "CartItem":
        return cls(
            product_id=int(data["product_id"]),
            quantity=int(data["quantity"]),
            price=str(data["price"]),
            name=data.get("name", ""),
            sku=data.get("sku", ""),
            currency=data.get("currency", "INR"),
        )


@dataclass
class Cart:
    """
    Represents the full cart for a session.
    """

    session_key: str
    items: dict[int, CartItem] = field(default_factory=dict)   # keyed by product_id
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # ── Aggregates ────────────────────────────────────────────────────────────
    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items.values())

    @property
    def total_unique_items(self) -> int:
        return len(self.items)

    @property
    def subtotal(self) -> Decimal:
        return sum(
            (item.subtotal for item in self.items.values()), Decimal("0.00")
        ).quantize(Decimal("0.01"))

    def to_response_dict(self) -> dict:
        return {
            "session_key": self.session_key,
            "items": [item.to_dict() for item in self.items.values()],
            "total_items": self.total_items,
            "total_unique_items": self.total_unique_items,
            "subtotal": str(self.subtotal),
            "currency": "INR",
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ─── Redis Repository ─────────────────────────────────────────────────────────


class CartRepository:
    """
    Encapsulates all Redis I/O for cart data.

    Keys:
        {prefix}:data:<session_key>  — JSON-encoded cart items dict
    """

    TTL: int = getattr(settings, "CART_TTL_SECONDS", 7 * 24 * 3600)
    MAX_ITEMS: int = getattr(settings, "CART_MAX_ITEMS", 50)
    MAX_QTY: int = getattr(settings, "CART_MAX_QUANTITY_PER_ITEM", 99)

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _data_key(session_key: str) -> str:
        return f"data:{session_key}"

    @classmethod
    def _load_raw(cls, session_key: str) -> dict:
        raw = cache.get(cls._data_key(session_key))
        if raw is None:
            return {}
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Corrupted cart data for session %s — resetting.", session_key)
                return {}
        return raw  # django-redis may deserialise automatically

    @classmethod
    def _save_raw(cls, session_key: str, data: dict) -> None:
        cache.set(cls._data_key(session_key), data, timeout=cls.TTL)

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def get(cls, session_key: str) -> Cart:
        """Load a Cart from Redis (empty Cart if key doesn't exist)."""
        raw = cls._load_raw(session_key)
        items: dict[int, CartItem] = {}
        meta = raw.get("_meta", {})
        for str_pid, item_data in raw.items():
            if str_pid == "_meta":
                continue
            try:
                item = CartItem.from_dict(item_data)
                items[item.product_id] = item
            except (KeyError, ValueError) as exc:
                logger.warning("Skipping malformed cart item %s: %s", str_pid, exc)

        return Cart(
            session_key=session_key,
            items=items,
            created_at=meta.get("created_at", time.time()),
            updated_at=meta.get("updated_at", time.time()),
        )

    @classmethod
    def save(cls, cart: Cart) -> None:
        """Persist a Cart back to Redis."""
        cart.updated_at = time.time()
        data: dict = {"_meta": {"created_at": cart.created_at, "updated_at": cart.updated_at}}
        for pid, item in cart.items.items():
            data[str(pid)] = {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "name": item.name,
                "sku": item.sku,
                "currency": item.currency,
            }
        cls._save_raw(cart.session_key, data)
        logger.debug("Cart %s saved (%d items).", cart.session_key, len(cart.items))

    @classmethod
    def add_item(
        cls,
        session_key: str,
        product_id: int,
        quantity: int,
        price: str,
        name: str = "",
        sku: str = "",
        currency: str = "INR",
    ) -> Cart:
        """
        Add or increment an item in the cart.
        Raises ValueError on constraint violations.
        """
        cart = cls.get(session_key)

        if product_id in cart.items:
            # Increment existing
            new_qty = cart.items[product_id].quantity + quantity
            if new_qty > cls.MAX_QTY:
                raise ValueError(
                    f"Quantity {new_qty} exceeds the maximum of {cls.MAX_QTY} per item."
                )
            cart.items[product_id].quantity = new_qty
            # Always update price snapshot to the latest validated price
            cart.items[product_id].price = price
        else:
            if len(cart.items) >= cls.MAX_ITEMS:
                raise ValueError(
                    f"Cart already has {cls.MAX_ITEMS} unique items (the maximum)."
                )
            if quantity > cls.MAX_QTY:
                raise ValueError(
                    f"Quantity {quantity} exceeds the maximum of {cls.MAX_QTY} per item."
                )
            cart.items[product_id] = CartItem(
                product_id=product_id,
                quantity=quantity,
                price=price,
                name=name,
                sku=sku,
                currency=currency,
            )

        cls.save(cart)
        return cart

    @classmethod
    def update_item(cls, session_key: str, product_id: int, quantity: int) -> Cart:
        """
        Set the quantity of an existing cart item.
        Raises KeyError if item not found, ValueError on constraint violation.
        """
        cart = cls.get(session_key)
        if product_id not in cart.items:
            raise KeyError(f"Product {product_id} is not in the cart.")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1. Use remove to delete an item.")
        if quantity > cls.MAX_QTY:
            raise ValueError(f"Quantity {quantity} exceeds the maximum of {cls.MAX_QTY}.")
        cart.items[product_id].quantity = quantity
        cls.save(cart)
        return cart

    @classmethod
    def remove_item(cls, session_key: str, product_id: int) -> Cart:
        """Remove an item from the cart. Raises KeyError if not found."""
        cart = cls.get(session_key)
        if product_id not in cart.items:
            raise KeyError(f"Product {product_id} is not in the cart.")
        del cart.items[product_id]
        cls.save(cart)
        return cart

    @classmethod
    def clear(cls, session_key: str) -> None:
        """Delete the entire cart from Redis."""
        cache.delete(cls._data_key(session_key))
        logger.info("Cart %s cleared.", session_key)
