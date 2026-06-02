"""
Unit tests for the Orders Service.

Coverage:
  - Order model (status transitions, is_cancellable, subtotal)
  - OrderItem model (subtotal)
  - Service layer (place_order, cancel_order)
  - REST API endpoints (place, list, detail, cancel)
  - Error paths (empty cart, cart service down, wrong status, ownership)
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Order, OrderItem
from apps.orders.services import cancel_order, place_order

from .factories import (
    CancelledOrderFactory,
    ConfirmedOrderFactory,
    DeliveredOrderFactory,
    OrderFactory,
    OrderItemFactory,
    PendingOrderFactory,
    ShippedOrderFactory,
)


# ══════════════════════════════════════════════════════════════════════════════
# Order model tests
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestOrderModel:

    def test_str_representation(self):
        order = OrderFactory(user_id="alice")
        assert "alice" in str(order)
        assert str(order.pk) in str(order)

    # ── Status transitions ────────────────────────────────────────────────────

    def test_pending_can_transition_to_confirmed(self):
        order = PendingOrderFactory()
        order.transition_to(Order.Status.CONFIRMED)
        assert order.status == Order.Status.CONFIRMED

    def test_pending_can_transition_to_cancelled(self):
        order = PendingOrderFactory()
        order.transition_to(Order.Status.CANCELLED)
        assert order.status == Order.Status.CANCELLED

    def test_confirmed_can_transition_to_shipped(self):
        order = ConfirmedOrderFactory()
        order.transition_to(Order.Status.SHIPPED)
        assert order.status == Order.Status.SHIPPED

    def test_confirmed_can_transition_to_cancelled(self):
        order = ConfirmedOrderFactory()
        order.transition_to(Order.Status.CANCELLED)
        assert order.status == Order.Status.CANCELLED

    def test_shipped_can_transition_to_delivered(self):
        order = ShippedOrderFactory()
        order.transition_to(Order.Status.DELIVERED)
        assert order.status == Order.Status.DELIVERED

    def test_shipped_cannot_be_cancelled(self):
        order = ShippedOrderFactory()
        with pytest.raises(ValueError, match="Cannot transition"):
            order.transition_to(Order.Status.CANCELLED)

    def test_delivered_is_terminal(self):
        order = DeliveredOrderFactory()
        with pytest.raises(ValueError, match="Cannot transition"):
            order.transition_to(Order.Status.CONFIRMED)

    def test_cancelled_is_terminal(self):
        order = CancelledOrderFactory()
        with pytest.raises(ValueError, match="Cannot transition"):
            order.transition_to(Order.Status.CONFIRMED)

    def test_pending_cannot_jump_to_delivered(self):
        order = PendingOrderFactory()
        with pytest.raises(ValueError):
            order.transition_to(Order.Status.DELIVERED)

    # ── is_cancellable ────────────────────────────────────────────────────────

    def test_pending_order_is_cancellable(self):
        order = PendingOrderFactory()
        assert order.is_cancellable is True

    def test_confirmed_order_is_cancellable(self):
        order = ConfirmedOrderFactory()
        assert order.is_cancellable is True

    def test_shipped_order_is_not_cancellable(self):
        order = ShippedOrderFactory()
        assert order.is_cancellable is False

    def test_delivered_order_is_not_cancellable(self):
        order = DeliveredOrderFactory()
        assert order.is_cancellable is False

    def test_already_cancelled_order_is_not_cancellable(self):
        order = CancelledOrderFactory()
        assert order.is_cancellable is False


# ══════════════════════════════════════════════════════════════════════════════
# OrderItem model tests
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestOrderItemModel:

    def test_subtotal_is_quantity_times_unit_price(self):
        order = OrderFactory()
        item = OrderItemFactory(order=order, quantity=3, unit_price=Decimal("100.00"))
        assert item.subtotal == Decimal("300.00")

    def test_subtotal_rounds_to_two_decimal_places(self):
        order = OrderFactory()
        item = OrderItemFactory(order=order, quantity=3, unit_price=Decimal("33.333"))
        # 3 × 33.333 = 99.999 → rounds to 100.00
        assert item.subtotal == Decimal("99.999").quantize(Decimal("0.01"))

    def test_str_representation(self):
        order = OrderFactory()
        item = OrderItemFactory(order=order, product_id=42)
        assert "42" in str(item)


# ══════════════════════════════════════════════════════════════════════════════
# Service layer tests
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestPlaceOrderService:

    def test_creates_order_and_items(self, mock_cart_items, session_key, user_id):
        with patch("apps.orders.services.get_cart", return_value=mock_cart_items), \
             patch("apps.orders.services.clear_cart"):
            order = place_order(user_id=user_id, session_key=session_key)

        assert order.pk is not None
        assert order.status == Order.Status.PENDING
        assert order.user_id == user_id
        assert order.session_key == session_key
        assert order.items.count() == 2
        assert order.total_price == Decimal("2497.00")

    def test_order_item_fields_are_correct(self, mock_cart_items, session_key, user_id):
        with patch("apps.orders.services.get_cart", return_value=mock_cart_items), \
             patch("apps.orders.services.clear_cart"):
            order = place_order(user_id=user_id, session_key=session_key)

        headphones = order.items.get(product_id=1)
        assert headphones.quantity == 2
        assert headphones.unit_price == Decimal("999.00")
        assert headphones.product_name == "Wireless Headphones"
        assert headphones.product_sku == "WH-001"

    def test_shipping_fields_are_stored(self, mock_cart_items, session_key, user_id):
        shipping = {
            "name": "Sumeet Mankari",
            "address_line1": "123 Test Road",
            "city": "Mumbai",
            "pincode": "400001",
            "country": "India",
        }
        with patch("apps.orders.services.get_cart", return_value=mock_cart_items), \
             patch("apps.orders.services.clear_cart"):
            order = place_order(
                user_id=user_id,
                session_key=session_key,
                shipping=shipping,
            )

        assert order.shipping_name == "Sumeet Mankari"
        assert order.shipping_city == "Mumbai"
        assert order.shipping_pincode == "400001"

    def test_cart_is_cleared_after_order(self, mock_cart_items, session_key, user_id):
        mock_clear = MagicMock()
        with patch("apps.orders.services.get_cart", return_value=mock_cart_items), \
             patch("apps.orders.services.clear_cart", mock_clear):
            place_order(user_id=user_id, session_key=session_key)

        mock_clear.assert_called_once_with(session_key)

    def test_empty_cart_raises_empty_cart_error(self, session_key, user_id):
        from apps.orders.cart_client import EmptyCartError

        with patch("apps.orders.services.get_cart", side_effect=EmptyCartError("empty")):
            with pytest.raises(EmptyCartError):
                place_order(user_id=user_id, session_key=session_key)

    def test_cart_service_error_propagates(self, session_key, user_id):
        from apps.orders.cart_client import CartServiceError

        with patch(
            "apps.orders.services.get_cart",
            side_effect=CartServiceError("timeout"),
        ):
            with pytest.raises(CartServiceError):
                place_order(user_id=user_id, session_key=session_key)

    def test_no_db_write_on_cart_service_failure(self, session_key, user_id):
        from apps.orders.cart_client import CartServiceError

        with patch(
            "apps.orders.services.get_cart",
            side_effect=CartServiceError("down"),
        ):
            with pytest.raises(CartServiceError):
                place_order(user_id=user_id, session_key=session_key)

        assert Order.objects.count() == 0


@pytest.mark.django_db
class TestCancelOrderService:

    def test_cancel_pending_order(self):
        order = PendingOrderFactory()
        cancelled = cancel_order(order, reason="Changed mind")
        assert cancelled.status == Order.Status.CANCELLED
        assert cancelled.cancellation_reason == "Changed mind"

    def test_cancel_confirmed_order(self):
        order = ConfirmedOrderFactory()
        cancelled = cancel_order(order, reason="Duplicate order")
        assert cancelled.status == Order.Status.CANCELLED

    def test_cancel_shipped_order_raises(self):
        order = ShippedOrderFactory()
        with pytest.raises(ValueError, match="cannot be cancelled"):
            cancel_order(order)

    def test_cancel_delivered_order_raises(self):
        order = DeliveredOrderFactory()
        with pytest.raises(ValueError, match="cannot be cancelled"):
            cancel_order(order)

    def test_cancel_already_cancelled_raises(self):
        order = CancelledOrderFactory()
        with pytest.raises(ValueError):
            cancel_order(order)

    def test_cancel_persists_to_db(self):
        order = PendingOrderFactory()
        cancel_order(order, reason="Test reason")
        refreshed = Order.objects.get(pk=order.pk)
        assert refreshed.status == Order.Status.CANCELLED
        assert refreshed.cancellation_reason == "Test reason"


# ══════════════════════════════════════════════════════════════════════════════
# API endpoint tests
# ══════════════════════════════════════════════════════════════════════════════

USER_HEADER = {"HTTP_X_USER_ID": "user-api-test"}


@pytest.mark.django_db
class TestPlaceOrderEndpoint:

    def test_place_order_success(self, api_client, mock_cart_items):
        with patch("apps.orders.views.place_order") as mock_place:
            # Return a realistic Order-like object
            mock_order = PendingOrderFactory()
            OrderItemFactory(order=mock_order, product_id=1, quantity=2)
            mock_place.return_value = Order.objects.prefetch_related("items").get(
                pk=mock_order.pk
            )

            response = api_client.post(
                "/api/v1/orders/place/",
                data={
                    "user_id": "user-001",
                    "session_key": "sess-001",
                },
                format="json",
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["status"] == Order.Status.PENDING

    def test_place_order_missing_required_fields(self, api_client):
        response = api_client.post(
            "/api/v1/orders/place/",
            data={"user_id": "user-001"},   # missing session_key
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.json()

    def test_place_order_empty_cart_returns_422(self, api_client):
        from apps.orders.cart_client import EmptyCartError

        with patch(
            "apps.orders.views.place_order",
            side_effect=EmptyCartError("Cart is empty"),
        ):
            response = api_client.post(
                "/api/v1/orders/place/",
                data={"user_id": "u1", "session_key": "sk1"},
                format="json",
            )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_place_order_cart_service_down_returns_503(self, api_client):
        from apps.orders.cart_client import CartServiceError

        with patch(
            "apps.orders.views.place_order",
            side_effect=CartServiceError("timeout"),
        ):
            response = api_client.post(
                "/api/v1/orders/place/",
                data={"user_id": "u1", "session_key": "sk1"},
                format="json",
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_place_order_with_full_shipping_address(self, api_client):
        pending = PendingOrderFactory(
            shipping_name="Alice",
            shipping_city="Bengaluru",
        )
        pending_with_items = Order.objects.prefetch_related("items").get(pk=pending.pk)

        with patch("apps.orders.views.place_order", return_value=pending_with_items):
            response = api_client.post(
                "/api/v1/orders/place/",
                data={
                    "user_id": "user-001",
                    "session_key": "sess-001",
                    "shipping": {
                        "name": "Alice",
                        "address_line1": "456 MG Road",
                        "city": "Bengaluru",
                        "pincode": "560001",
                        "country": "India",
                    },
                    "notes": "Ring doorbell twice",
                },
                format="json",
            )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestOrderListEndpoint:

    def test_list_requires_user_id(self, api_client):
        response = api_client.get("/api/v1/orders/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_returns_only_user_orders(self, api_client):
        OrderFactory(user_id="alice", total_price="100.00")
        OrderFactory(user_id="alice", total_price="200.00")
        OrderFactory(user_id="bob", total_price="50.00")

        response = api_client.get("/api/v1/orders/", HTTP_X_USER_ID="alice")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 2
        assert all(o["user_id"] == "alice" for o in data["results"])

    def test_list_filter_by_status(self, api_client):
        OrderFactory(user_id="alice", status=Order.Status.PENDING)
        OrderFactory(user_id="alice", status=Order.Status.DELIVERED)

        response = api_client.get(
            "/api/v1/orders/?status=PENDING", HTTP_X_USER_ID="alice"
        )
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["status"] == "PENDING"

    def test_list_invalid_status_filter_returns_400(self, api_client):
        response = api_client.get(
            "/api/v1/orders/?status=BOGUS", HTTP_X_USER_ID="alice"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_pagination(self, api_client):
        for _ in range(5):
            OrderFactory(user_id="pager")

        response = api_client.get(
            "/api/v1/orders/?page_size=2&page=1", HTTP_X_USER_ID="pager"
        )
        data = response.json()
        assert data["count"] == 5
        assert len(data["results"]) == 2

    def test_list_empty_for_unknown_user(self, api_client):
        response = api_client.get("/api/v1/orders/", HTTP_X_USER_ID="nobody")
        data = response.json()
        assert data["count"] == 0

    def test_user_id_via_query_param(self, api_client):
        OrderFactory(user_id="charlie")
        response = api_client.get("/api/v1/orders/?user_id=charlie")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1


@pytest.mark.django_db
class TestOrderDetailEndpoint:

    def test_get_order_detail(self, api_client):
        order = OrderFactory(user_id="alice")
        OrderItemFactory(order=order, product_id=10)

        response = api_client.get(
            f"/api/v1/orders/{order.pk}/", HTTP_X_USER_ID="alice"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == order.pk
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == 10

    def test_get_nonexistent_order_returns_404(self, api_client):
        response = api_client.get("/api/v1/orders/9999/", HTTP_X_USER_ID="alice")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_wrong_user_cannot_see_order(self, api_client):
        order = OrderFactory(user_id="alice")
        response = api_client.get(
            f"/api/v1/orders/{order.pk}/", HTTP_X_USER_ID="bob"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_order_detail_includes_is_cancellable(self, api_client):
        order = PendingOrderFactory(user_id="alice")
        response = api_client.get(
            f"/api/v1/orders/{order.pk}/", HTTP_X_USER_ID="alice"
        )
        assert response.json()["is_cancellable"] is True

    def test_delivered_order_is_not_cancellable_in_response(self, api_client):
        order = DeliveredOrderFactory(user_id="alice")
        response = api_client.get(
            f"/api/v1/orders/{order.pk}/", HTTP_X_USER_ID="alice"
        )
        assert response.json()["is_cancellable"] is False


@pytest.mark.django_db
class TestCancelOrderEndpoint:

    def test_cancel_pending_order(self, api_client):
        order = PendingOrderFactory(user_id="alice")
        response = api_client.put(
            f"/api/v1/orders/{order.pk}/cancel/",
            data={"reason": "Changed my mind"},
            format="json",
            HTTP_X_USER_ID="alice",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "CANCELLED"
        assert data["cancellation_reason"] == "Changed my mind"

    def test_cancel_confirmed_order(self, api_client):
        order = ConfirmedOrderFactory(user_id="alice")
        response = api_client.put(
            f"/api/v1/orders/{order.pk}/cancel/",
            data={},
            format="json",
            HTTP_X_USER_ID="alice",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_cancel_shipped_order_returns_409(self, api_client):
        order = ShippedOrderFactory(user_id="alice")
        response = api_client.put(
            f"/api/v1/orders/{order.pk}/cancel/",
            data={},
            format="json",
            HTTP_X_USER_ID="alice",
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "error" in response.json()

    def test_cancel_delivered_order_returns_409(self, api_client):
        order = DeliveredOrderFactory(user_id="alice")
        response = api_client.put(
            f"/api/v1/orders/{order.pk}/cancel/",
            data={},
            format="json",
            HTTP_X_USER_ID="alice",
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_cancel_nonexistent_order_returns_404(self, api_client):
        response = api_client.put(
            "/api/v1/orders/9999/cancel/",
            data={},
            format="json",
            HTTP_X_USER_ID="alice",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_another_users_order_returns_404(self, api_client):
        order = PendingOrderFactory(user_id="alice")
        response = api_client.put(
            f"/api/v1/orders/{order.pk}/cancel/",
            data={},
            format="json",
            HTTP_X_USER_ID="bob",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_without_reason_is_allowed(self, api_client):
        order = PendingOrderFactory(user_id="alice")
        response = api_client.put(
            f"/api/v1/orders/{order.pk}/cancel/",
            data={},
            format="json",
            HTTP_X_USER_ID="alice",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_db_is_updated_after_cancel(self, api_client):
        order = PendingOrderFactory(user_id="alice")
        api_client.put(
            f"/api/v1/orders/{order.pk}/cancel/",
            data={"reason": "Duplicate"},
            format="json",
            HTTP_X_USER_ID="alice",
        )
        refreshed = Order.objects.get(pk=order.pk)
        assert refreshed.status == Order.Status.CANCELLED
        assert refreshed.cancellation_reason == "Duplicate"


# ══════════════════════════════════════════════════════════════════════════════
# Health endpoint tests
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestHealthEndpoints:

    def test_health_check_returns_200(self, api_client):
        response = api_client.get("/health/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "orders-service"

    def test_readiness_check_with_working_db(self, api_client):
        response = api_client.get("/ready/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["checks"]["postgres"] == "ok"
