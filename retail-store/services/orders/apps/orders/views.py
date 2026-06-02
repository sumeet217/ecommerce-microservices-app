"""
Orders Service — API views.

Endpoints:
    POST   /api/v1/orders/place/         → place a new order (pulls from cart)
    GET    /api/v1/orders/               → list orders for a user
    GET    /api/v1/orders/<id>/          → order detail
    PUT    /api/v1/orders/<id>/cancel/   → cancel an order
"""

from __future__ import annotations

import logging

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .cart_client import CartServiceError, EmptyCartError
from .models import Order
from .serializers import CancelOrderSerializer, OrderSerializer, PlaceOrderSerializer
from .services import cancel_order, place_order

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _get_user_id(request: Request) -> str | None:
    """
    Resolve the caller's user identifier.

    Priority:
        1. X-User-Id request header      (set by an API gateway / auth middleware)
        2. ?user_id query parameter       (for simple non-authenticated use)
    """
    uid = request.META.get("HTTP_X_USER_ID", "").strip()
    if uid:
        return uid
    return request.query_params.get("user_id", "").strip() or None


# ─── Views ────────────────────────────────────────────────────────────────────


class PlaceOrderView(APIView):
    """
    POST /api/v1/orders/place/

    Body (JSON):
        {
            "user_id": "user-uuid-or-email",
            "session_key": "cart-session-key",
            "shipping": {                       // optional
                "name": "Sumeet Mankari",
                "address_line1": "123 Main St",
                "city": "Mumbai",
                "pincode": "400001",
                "country": "India"
            },
            "notes": "Leave at door"            // optional
        }

    Behaviour:
        1. Validates payload
        2. Fetches cart from Cart Service using session_key
        3. Creates Order + OrderItems atomically in PostgreSQL
        4. Clears cart (best-effort — failure does NOT roll back the order)
        5. Returns the created order (HTTP 201)
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = PlaceOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        shipping = data.get("shipping", {})

        try:
            order = place_order(
                user_id=data["user_id"],
                session_key=data["session_key"],
                shipping=shipping,
                notes=data.get("notes", ""),
            )
        except EmptyCartError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except CartServiceError as exc:
            logger.error("Cart Service error during order placement: %s", exc)
            return Response(
                {"error": "Could not reach the Cart Service. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderListView(APIView):
    """
    GET /api/v1/orders/?user_id=<uid>[&status=PENDING][&page=1]

    Returns a paginated list of orders belonging to the given user.
    Filterable by status.  Ordered newest-first.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, *args, **kwargs) -> Response:
        user_id = _get_user_id(request)
        if not user_id:
            return Response(
                {"error": "user_id is required (via X-User-Id header or ?user_id= param)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs: QuerySet = (
            Order.objects.filter(user_id=user_id)
            .prefetch_related("items")
            .order_by("-created_at")
        )

        # Optional status filter
        status_filter = request.query_params.get("status", "").strip().upper()
        if status_filter:
            valid_statuses = [s.value for s in Order.Status]
            if status_filter not in valid_statuses:
                return Response(
                    {
                        "error": f"Invalid status filter {status_filter!r}. "
                        f"Valid values: {valid_statuses}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            qs = qs.filter(status=status_filter)

        # Manual pagination
        try:
            page_size = int(request.query_params.get("page_size", 20))
            page = int(request.query_params.get("page", 1))
        except ValueError:
            page_size, page = 20, 1

        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)
        offset = (page - 1) * page_size

        total = qs.count()
        orders = qs[offset : offset + page_size]

        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": OrderSerializer(orders, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class OrderDetailView(APIView):
    """
    GET /api/v1/orders/<id>/

    Returns full order detail including all line items.
    The caller must supply the matching user_id for ownership verification.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, order_id: int, *args, **kwargs) -> Response:
        user_id = _get_user_id(request)

        qs = Order.objects.prefetch_related("items")

        # Ownership check: if user_id is provided, scope to that user
        if user_id:
            order = get_object_or_404(qs, pk=order_id, user_id=user_id)
        else:
            order = get_object_or_404(qs, pk=order_id)

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class CancelOrderView(APIView):
    """
    PUT /api/v1/orders/<id>/cancel/

    Body (JSON):
        {"reason": "Changed my mind"}   // optional

    Only PENDING and CONFIRMED orders may be cancelled (configurable
    via the CANCELLABLE_STATUSES setting).
    """

    authentication_classes = []
    permission_classes = []

    def put(self, request: Request, order_id: int, *args, **kwargs) -> Response:
        serializer = CancelOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        user_id = _get_user_id(request)
        qs = Order.objects.prefetch_related("items")

        if user_id:
            order = get_object_or_404(qs, pk=order_id, user_id=user_id)
        else:
            order = get_object_or_404(qs, pk=order_id)

        try:
            order = cancel_order(order, reason=serializer.validated_data.get("reason", ""))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
