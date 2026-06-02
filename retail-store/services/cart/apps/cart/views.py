"""
Cart Service — API views.

Session management:
    We identify a cart by a session key.  The key is taken from:
        1. The X-Session-Key header (preferred — works with stateless clients)
        2. Django's built-in session framework (fallback for browser clients)

Endpoints:
    GET    /api/v1/cart/          → view cart
    POST   /api/v1/cart/add/      → add item (calls Catalog to validate)
    PUT    /api/v1/cart/update/   → update quantity
    DELETE /api/v1/cart/remove/   → remove single item
    DELETE /api/v1/cart/clear/    → clear entire cart
"""

from __future__ import annotations

import logging
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .catalog_client import (
    CatalogServiceError,
    ProductNotFoundError,
    ProductUnavailableError,
    get_product,
)
from .models import CartRepository
from .serializers import (
    AddItemSerializer,
    RemoveItemSerializer,
    UpdateItemSerializer,
)

logger = logging.getLogger(__name__)


# ─── Session helper ───────────────────────────────────────────────────────────


def _get_session_key(request: Request) -> str:
    """
    Resolve the cart session key from the request.

    Priority:
        1. X-Session-Key header  (for API/mobile clients)
        2. Django session key    (for browser clients)
        3. Auto-generate a new UUID (last resort)
    """
    key = request.META.get("HTTP_X_SESSION_KEY", "").strip()
    if key:
        return key

    if hasattr(request, "session"):
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key

    # Fallback: stateless — generate ephemeral key (client won't persist it)
    return f"anon-{uuid.uuid4().hex}"


def _ok(cart, http_status=status.HTTP_200_OK) -> Response:
    return Response(cart.to_response_dict(), status=http_status)


# ─── Views ────────────────────────────────────────────────────────────────────


class CartDetailView(APIView):
    """
    GET /api/v1/cart/
    Returns the current state of the cart.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, *args, **kwargs) -> Response:
        session_key = _get_session_key(request)
        cart = CartRepository.get(session_key)
        return _ok(cart)


class CartAddView(APIView):
    """
    POST /api/v1/cart/add/

    Body (JSON):
        {
            "product_id": 42,
            "quantity": 2,
            "validate_with_catalog": true    // optional, default true
        }

    When validate_with_catalog is true (default), the view calls the
    Catalog Service to verify the product exists, is active, and has
    stock.  The price is always taken from the catalog response to
    prevent price tampering.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = AddItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        product_id: int = data["product_id"]
        quantity: int = data["quantity"]
        do_validate: bool = data.get("validate_with_catalog", True)

        # ── Catalog validation ─────────────────────────────────────────────
        product_name = ""
        product_sku = ""
        product_price = "0.00"
        product_currency = "INR"

        if do_validate:
            try:
                product = get_product(product_id)
            except ProductNotFoundError as exc:
                return Response(
                    {"error": str(exc)}, status=status.HTTP_404_NOT_FOUND
                )
            except ProductUnavailableError as exc:
                return Response(
                    {"error": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            except CatalogServiceError as exc:
                logger.error("Catalog Service error: %s", exc)
                return Response(
                    {"error": "Could not reach the Catalog Service. Please try again later."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # Use the catalog's selling_price (after discount)
            product_price = str(product.get("selling_price") or product.get("price", "0.00"))
            product_name = product.get("name", "")
            product_sku = product.get("sku", "")
            product_currency = product.get("currency", "INR")

        # ── Persist ────────────────────────────────────────────────────────
        session_key = _get_session_key(request)
        try:
            cart = CartRepository.add_item(
                session_key=session_key,
                product_id=product_id,
                quantity=quantity,
                price=product_price,
                name=product_name,
                sku=product_sku,
                currency=product_currency,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return _ok(cart, http_status=status.HTTP_201_CREATED)


class CartUpdateView(APIView):
    """
    PUT /api/v1/cart/update/

    Body (JSON):
        {"product_id": 42, "quantity": 5}
    """

    authentication_classes = []
    permission_classes = []

    def put(self, request: Request, *args, **kwargs) -> Response:
        serializer = UpdateItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        session_key = _get_session_key(request)

        try:
            cart = CartRepository.update_item(
                session_key=session_key,
                product_id=data["product_id"],
                quantity=data["quantity"],
            )
        except KeyError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return _ok(cart)


class CartRemoveView(APIView):
    """
    DELETE /api/v1/cart/remove/

    Body (JSON):
        {"product_id": 42}
    """

    authentication_classes = []
    permission_classes = []

    def delete(self, request: Request, *args, **kwargs) -> Response:
        serializer = RemoveItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        session_key = _get_session_key(request)
        product_id: int = serializer.validated_data["product_id"]

        try:
            cart = CartRepository.remove_item(session_key=session_key, product_id=product_id)
        except KeyError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return _ok(cart)


class CartClearView(APIView):
    """
    DELETE /api/v1/cart/clear/
    Removes all items from the cart.
    """

    authentication_classes = []
    permission_classes = []

    def delete(self, request: Request, *args, **kwargs) -> Response:
        session_key = _get_session_key(request)
        CartRepository.clear(session_key)
        return Response(
            {"message": "Cart cleared successfully.", "session_key": session_key},
            status=status.HTTP_200_OK,
        )
