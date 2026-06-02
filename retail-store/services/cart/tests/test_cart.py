"""
Unit tests for the Cart Service.

Coverage:
  - CartItem / Cart model layer (subtotals, aggregates)
  - CartRepository CRUD operations (add, update, remove, clear, constraints)
  - REST API endpoints (GET, POST, PUT, DELETE)
  - Catalog validation bypass (validate_with_catalog=false)
  - Error paths (item not found, quantity limits, cart size limit)
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.cart.models import Cart, CartItem, CartRepository


# ══════════════════════════════════════════════════════════════════════════════
# CartItem model tests
# ══════════════════════════════════════════════════════════════════════════════


class TestCartItemModel:

    def test_subtotal_calculation(self):
        item = CartItem(product_id=1, quantity=3, price="100.00")
        assert item.subtotal == Decimal("300.00")

    def test_subtotal_fractional_price(self):
        item = CartItem(product_id=2, quantity=2, price="49.99")
        assert item.subtotal == Decimal("99.98")

    def test_to_dict_includes_subtotal(self):
        item = CartItem(product_id=1, quantity=1, price="250.50", name="Widget", sku="W-01")
        d = item.to_dict()
        assert d["subtotal"] == "250.50"
        assert d["product_id"] == 1
        assert d["sku"] == "W-01"

    def test_from_dict_roundtrip(self):
        original = CartItem(product_id=5, quantity=4, price="75.00", name="Gadget", sku="G-05")
        restored = CartItem.from_dict(original.to_dict())
        assert restored.product_id == 5
        assert restored.quantity == 4
        assert restored.price == "75.00"

    def test_default_currency_is_inr(self):
        item = CartItem(product_id=1, quantity=1, price="10.00")
        assert item.currency == "INR"


# ══════════════════════════════════════════════════════════════════════════════
# Cart aggregate tests
# ══════════════════════════════════════════════════════════════════════════════


class TestCartAggregate:

    def test_empty_cart_subtotal_is_zero(self):
        cart = Cart(session_key="sk")
        assert cart.subtotal == Decimal("0.00")
        assert cart.total_items == 0
        assert cart.total_unique_items == 0

    def test_total_items_sums_quantities(self):
        cart = Cart(
            session_key="sk",
            items={
                1: CartItem(product_id=1, quantity=3, price="10.00"),
                2: CartItem(product_id=2, quantity=2, price="20.00"),
            },
        )
        assert cart.total_items == 5
        assert cart.total_unique_items == 2

    def test_subtotal_sums_all_line_items(self):
        cart = Cart(
            session_key="sk",
            items={
                1: CartItem(product_id=1, quantity=2, price="100.00"),
                2: CartItem(product_id=2, quantity=1, price="50.00"),
            },
        )
        assert cart.subtotal == Decimal("250.00")

    def test_to_response_dict_structure(self):
        cart = Cart(session_key="xyz")
        d = cart.to_response_dict()
        assert "session_key" in d
        assert "items" in d
        assert "subtotal" in d
        assert "total_items" in d


# ══════════════════════════════════════════════════════════════════════════════
# CartRepository tests
# ══════════════════════════════════════════════════════════════════════════════


class TestCartRepository:

    def test_get_empty_cart_returns_cart_object(self, session_key):
        cart = CartRepository.get(session_key)
        assert isinstance(cart, Cart)
        assert cart.total_items == 0

    def test_add_item_persists_and_returns_cart(self, session_key):
        cart = CartRepository.add_item(
            session_key=session_key,
            product_id=10,
            quantity=1,
            price="500.00",
            name="Product A",
            sku="PA-001",
        )
        assert 10 in cart.items
        assert cart.items[10].quantity == 1
        assert cart.items[10].price == "500.00"

    def test_add_item_twice_increments_quantity(self, session_key):
        CartRepository.add_item(session_key, 10, 2, "100.00", "A")
        cart = CartRepository.add_item(session_key, 10, 3, "100.00", "A")
        assert cart.items[10].quantity == 5

    def test_add_item_updates_price_snapshot_on_second_add(self, session_key):
        CartRepository.add_item(session_key, 10, 1, "100.00", "A")
        cart = CartRepository.add_item(session_key, 10, 1, "120.00", "A")
        assert cart.items[10].price == "120.00"

    def test_update_item_changes_quantity(self, session_key, seeded_cart):
        cart = CartRepository.update_item(session_key, product_id=1, quantity=5)
        assert cart.items[1].quantity == 5

    def test_update_item_raises_keyerror_if_not_in_cart(self, session_key):
        with pytest.raises(KeyError):
            CartRepository.update_item(session_key, product_id=999, quantity=1)

    def test_update_item_raises_value_error_if_quantity_zero(self, session_key, seeded_cart):
        with pytest.raises(ValueError):
            CartRepository.update_item(session_key, product_id=1, quantity=0)

    def test_remove_item_deletes_it(self, session_key, seeded_cart):
        cart = CartRepository.remove_item(session_key, product_id=1)
        assert 1 not in cart.items

    def test_remove_item_raises_keyerror_if_missing(self, session_key):
        with pytest.raises(KeyError):
            CartRepository.remove_item(session_key, product_id=9999)

    def test_clear_empties_cart(self, session_key, seeded_cart):
        CartRepository.clear(session_key)
        cart = CartRepository.get(session_key)
        assert cart.total_items == 0

    def test_max_items_limit(self, session_key):
        """Cart refuses a new unique item once MAX_ITEMS is reached."""
        original_max = CartRepository.MAX_ITEMS
        CartRepository.MAX_ITEMS = 2
        try:
            CartRepository.add_item(session_key, 1, 1, "10.00")
            CartRepository.add_item(session_key, 2, 1, "20.00")
            with pytest.raises(ValueError, match="maximum"):
                CartRepository.add_item(session_key, 3, 1, "30.00")
        finally:
            CartRepository.MAX_ITEMS = original_max

    def test_max_quantity_per_item_limit(self, session_key):
        """Incrementing a single item beyond MAX_QTY raises ValueError."""
        original_max = CartRepository.MAX_QTY
        CartRepository.MAX_QTY = 5
        try:
            CartRepository.add_item(session_key, 1, 3, "10.00")
            with pytest.raises(ValueError, match="[Mm]aximum"):
                CartRepository.add_item(session_key, 1, 3, "10.00")   # total = 6
        finally:
            CartRepository.MAX_QTY = original_max

    def test_get_after_save_restores_items(self, session_key):
        CartRepository.add_item(session_key, 42, 7, "250.00", "Thing", "T-42", "INR")
        loaded = CartRepository.get(session_key)
        assert loaded.items[42].quantity == 7
        assert loaded.items[42].name == "Thing"


# ══════════════════════════════════════════════════════════════════════════════
# API endpoint tests
# ══════════════════════════════════════════════════════════════════════════════

SESSION_HEADER = {"HTTP_X_SESSION_KEY": "api-test-session"}


class TestCartDetailEndpoint:

    def test_get_empty_cart_returns_200(self, api_client):
        response = api_client.get("/api/v1/cart/", **SESSION_HEADER)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_items"] == 0
        assert data["items"] == []

    def test_get_populated_cart(self, api_client, session_key, seeded_cart):
        response = api_client.get(
            "/api/v1/cart/",
            HTTP_X_SESSION_KEY=session_key,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_items"] == 2
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == 1


class TestCartAddEndpoint:

    def test_add_item_without_catalog_validation(self, api_client):
        payload = {
            "product_id": 100,
            "quantity": 2,
            "validate_with_catalog": False,
        }
        response = api_client.post(
            "/api/v1/cart/add/",
            data=payload,
            format="json",
            **SESSION_HEADER,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert any(item["product_id"] == 100 for item in data["items"])

    def test_add_item_with_catalog_validation_success(self, api_client):
        mock_product = {
            "id": 5,
            "name": "Awesome Widget",
            "sku": "AW-005",
            "price": "1500.00",
            "selling_price": "1200.00",
            "currency": "INR",
            "status": "active",
            "stock_quantity": 10,
        }
        with patch(
            "apps.cart.views.get_product", return_value=mock_product
        ):
            response = api_client.post(
                "/api/v1/cart/add/",
                data={"product_id": 5, "quantity": 1, "validate_with_catalog": True},
                format="json",
                **SESSION_HEADER,
            )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        item = next(i for i in data["items"] if i["product_id"] == 5)
        # Price snapshot should be selling_price from catalog
        assert item["price"] == "1200.00"
        assert item["name"] == "Awesome Widget"

    def test_add_item_product_not_found_in_catalog(self, api_client):
        from apps.cart.catalog_client import ProductNotFoundError
        with patch("apps.cart.views.get_product", side_effect=ProductNotFoundError("Not found")):
            response = api_client.post(
                "/api/v1/cart/add/",
                data={"product_id": 999, "quantity": 1, "validate_with_catalog": True},
                format="json",
                **SESSION_HEADER,
            )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_item_product_unavailable_in_catalog(self, api_client):
        from apps.cart.catalog_client import ProductUnavailableError
        with patch(
            "apps.cart.views.get_product",
            side_effect=ProductUnavailableError("Out of stock"),
        ):
            response = api_client.post(
                "/api/v1/cart/add/",
                data={"product_id": 10, "quantity": 1, "validate_with_catalog": True},
                format="json",
                **SESSION_HEADER,
            )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_add_item_catalog_service_down(self, api_client):
        from apps.cart.catalog_client import CatalogServiceError
        with patch(
            "apps.cart.views.get_product",
            side_effect=CatalogServiceError("timeout"),
        ):
            response = api_client.post(
                "/api/v1/cart/add/",
                data={"product_id": 1, "quantity": 1, "validate_with_catalog": True},
                format="json",
                **SESSION_HEADER,
            )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_add_item_invalid_payload(self, api_client):
        response = api_client.post(
            "/api/v1/cart/add/",
            data={"product_id": -1, "quantity": 0},
            format="json",
            **SESSION_HEADER,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.json()

    def test_add_item_missing_product_id(self, api_client):
        response = api_client.post(
            "/api/v1/cart/add/",
            data={"quantity": 1},
            format="json",
            **SESSION_HEADER,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCartUpdateEndpoint:

    def test_update_quantity(self, api_client, session_key, seeded_cart):
        response = api_client.put(
            "/api/v1/cart/update/",
            data={"product_id": 1, "quantity": 10},
            format="json",
            HTTP_X_SESSION_KEY=session_key,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        item = next(i for i in data["items"] if i["product_id"] == 1)
        assert item["quantity"] == 10

    def test_update_nonexistent_item_returns_404(self, api_client, session_key):
        response = api_client.put(
            "/api/v1/cart/update/",
            data={"product_id": 9999, "quantity": 1},
            format="json",
            HTTP_X_SESSION_KEY=session_key,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_invalid_payload(self, api_client):
        response = api_client.put(
            "/api/v1/cart/update/",
            data={"product_id": 1, "quantity": -5},
            format="json",
            **SESSION_HEADER,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCartRemoveEndpoint:

    def test_remove_existing_item(self, api_client, session_key, seeded_cart):
        response = api_client.delete(
            "/api/v1/cart/remove/",
            data={"product_id": 1},
            format="json",
            HTTP_X_SESSION_KEY=session_key,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(i["product_id"] != 1 for i in data["items"])

    def test_remove_nonexistent_item_returns_404(self, api_client, session_key):
        response = api_client.delete(
            "/api/v1/cart/remove/",
            data={"product_id": 8888},
            format="json",
            HTTP_X_SESSION_KEY=session_key,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_invalid_payload(self, api_client):
        response = api_client.delete(
            "/api/v1/cart/remove/",
            data={},
            format="json",
            **SESSION_HEADER,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCartClearEndpoint:

    def test_clear_empties_cart(self, api_client, session_key, seeded_cart):
        response = api_client.delete(
            "/api/v1/cart/clear/",
            HTTP_X_SESSION_KEY=session_key,
        )
        assert response.status_code == status.HTTP_200_OK
        assert "cleared" in response.json()["message"].lower()

        # Verify cart is empty
        get_resp = api_client.get("/api/v1/cart/", HTTP_X_SESSION_KEY=session_key)
        assert get_resp.json()["total_items"] == 0

    def test_clear_already_empty_cart_is_idempotent(self, api_client):
        response = api_client.delete("/api/v1/cart/clear/", **SESSION_HEADER)
        assert response.status_code == status.HTTP_200_OK


# ══════════════════════════════════════════════════════════════════════════════
# Session key resolution tests
# ══════════════════════════════════════════════════════════════════════════════


class TestSessionKeyResolution:

    def test_x_session_key_header_is_used(self, api_client):
        """Two requests with the same X-Session-Key share the same cart."""
        api_client.post(
            "/api/v1/cart/add/",
            data={"product_id": 77, "quantity": 3, "validate_with_catalog": False},
            format="json",
            HTTP_X_SESSION_KEY="shared-key",
        )
        response = api_client.get("/api/v1/cart/", HTTP_X_SESSION_KEY="shared-key")
        data = response.json()
        assert data["total_items"] == 3

    def test_different_session_keys_are_isolated(self, api_client):
        """Items added under key-A must not appear under key-B."""
        api_client.post(
            "/api/v1/cart/add/",
            data={"product_id": 1, "quantity": 1, "validate_with_catalog": False},
            format="json",
            HTTP_X_SESSION_KEY="key-A",
        )
        response = api_client.get("/api/v1/cart/", HTTP_X_SESSION_KEY="key-B")
        assert response.json()["total_items"] == 0
