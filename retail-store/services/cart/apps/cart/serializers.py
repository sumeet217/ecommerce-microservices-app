"""
Cart Service — DRF serializers.

Input serializers validate incoming request payloads.
CartItemSerializer / CartSerializer are used for output only.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from rest_framework import serializers


# ─── Output serializers ───────────────────────────────────────────────────────


class CartItemSerializer(serializers.Serializer):
    """Read-only serializer for a single cart line item."""

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    price = serializers.CharField()
    name = serializers.CharField()
    sku = serializers.CharField()
    currency = serializers.CharField()
    subtotal = serializers.CharField()


class CartSerializer(serializers.Serializer):
    """Read-only serializer for the full cart response."""

    session_key = serializers.CharField()
    items = CartItemSerializer(many=True)
    total_items = serializers.IntegerField()
    total_unique_items = serializers.IntegerField()
    subtotal = serializers.CharField()
    currency = serializers.CharField()
    created_at = serializers.FloatField()
    updated_at = serializers.FloatField()


# ─── Input serializers ────────────────────────────────────────────────────────


class AddItemSerializer(serializers.Serializer):
    """
    Validates the body of POST /cart/add/

    Required fields:
        product_id  — integer, positive
        quantity    — integer, 1–99 (server-side max enforced separately)

    Optional fields:
        validate_with_catalog — bool (default True).
            Set False in tests / when catalog is unavailable.
    """

    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=99, default=1)
    validate_with_catalog = serializers.BooleanField(default=True, required=False)

    def validate_quantity(self, value: int) -> int:
        from django.conf import settings
        max_qty = getattr(settings, "CART_MAX_QUANTITY_PER_ITEM", 99)
        if value > max_qty:
            raise serializers.ValidationError(
                f"Maximum quantity per item is {max_qty}."
            )
        return value


class UpdateItemSerializer(serializers.Serializer):
    """
    Validates the body of PUT /cart/update/

    Required fields:
        product_id — which item to update
        quantity   — new quantity (must be ≥ 1)
    """

    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=99)

    def validate_quantity(self, value: int) -> int:
        from django.conf import settings
        max_qty = getattr(settings, "CART_MAX_QUANTITY_PER_ITEM", 99)
        if value > max_qty:
            raise serializers.ValidationError(
                f"Maximum quantity per item is {max_qty}."
            )
        return value


class RemoveItemSerializer(serializers.Serializer):
    """
    Validates the body of DELETE /cart/remove/

    Required fields:
        product_id — which item to remove
    """

    product_id = serializers.IntegerField(min_value=1)
