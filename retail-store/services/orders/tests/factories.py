"""
Test factories for the Orders Service.
Uses factory_boy to create Order and OrderItem instances.
"""

from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.orders.models import Order, OrderItem


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    user_id = factory.Sequence(lambda n: f"user-{n:04d}")
    session_key = factory.Sequence(lambda n: f"session-{n:04d}")
    status = Order.Status.PENDING
    total_price = Decimal("2497.00")
    currency = "INR"
    shipping_name = "Test User"
    shipping_address_line1 = "123 Test Street"
    shipping_city = "Mumbai"
    shipping_pincode = "400001"
    shipping_country = "India"
    notes = ""
    cancellation_reason = ""


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product_id = factory.Sequence(lambda n: n + 1)
    product_name = factory.Sequence(lambda n: f"Product {n}")
    product_sku = factory.Sequence(lambda n: f"SKU-{n:04d}")
    quantity = 1
    unit_price = Decimal("999.00")
    currency = "INR"


class PendingOrderFactory(OrderFactory):
    status = Order.Status.PENDING


class ConfirmedOrderFactory(OrderFactory):
    status = Order.Status.CONFIRMED


class ShippedOrderFactory(OrderFactory):
    status = Order.Status.SHIPPED


class DeliveredOrderFactory(OrderFactory):
    status = Order.Status.DELIVERED


class CancelledOrderFactory(OrderFactory):
    status = Order.Status.CANCELLED
    cancellation_reason = "Customer request"
