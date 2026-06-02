"""
Orders Service — DRF serializers.

Output:
    OrderItemSerializer   — single line item
    OrderSerializer       — full order + nested items

Input:
    PlaceOrderSerializer  — POST /orders/place/
    CancelOrderSerializer — PUT /orders/<id>/cancel/
"""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from .models import Order, OrderItem


# ─── Output serializers ───────────────────────────────────────────────────────


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_id",
            "product_name",
            "product_sku",
            "quantity",
            "unit_price",
            "currency",
            "subtotal",
        ]

    def get_subtotal(self, obj: OrderItem) -> str:
        return str(obj.subtotal)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    is_cancellable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user_id",
            "session_key",
            "status",
            "is_cancellable",
            "total_price",
            "currency",
            "shipping_name",
            "shipping_address_line1",
            "shipping_address_line2",
            "shipping_city",
            "shipping_pincode",
            "shipping_country",
            "notes",
            "cancellation_reason",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "total_price",
            "created_at",
            "updated_at",
        ]


# ─── Input serializers ────────────────────────────────────────────────────────


class ShippingAddressSerializer(serializers.Serializer):
    """Optional nested shipping address block inside PlaceOrderSerializer."""

    name = serializers.CharField(max_length=255, required=False, default="")
    address_line1 = serializers.CharField(max_length=512, required=False, default="")
    address_line2 = serializers.CharField(max_length=512, required=False, default="")
    city = serializers.CharField(max_length=100, required=False, default="")
    pincode = serializers.CharField(max_length=20, required=False, default="")
    country = serializers.CharField(max_length=100, required=False, default="India")


class PlaceOrderSerializer(serializers.Serializer):
    """
    Validates the body of POST /api/v1/orders/place/

    Required:
        user_id     — customer identifier (UUID string, email, or session key)
        session_key — cart session key to pull items from

    Optional:
        shipping    — nested address block
        notes       — free-text order notes
    """

    user_id = serializers.CharField(max_length=255)
    session_key = serializers.CharField(max_length=255)
    shipping = ShippingAddressSerializer(required=False)
    notes = serializers.CharField(
        max_length=2048, required=False, default="", allow_blank=True
    )

    def validate_user_id(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("user_id must not be blank.")
        return value.strip()

    def validate_session_key(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("session_key must not be blank.")
        return value.strip()


class CancelOrderSerializer(serializers.Serializer):
    """
    Validates the body of PUT /api/v1/orders/<id>/cancel/

    Optional:
        reason — human-readable cancellation reason
    """

    reason = serializers.CharField(
        max_length=1024, required=False, default="", allow_blank=True
    )
