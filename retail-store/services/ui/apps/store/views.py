"""
UI Service — Django views.

Session management:
    session_key — stored in the signed cookie session under key 'cart_session_key'.
    user_id     — same session; defaults to the session key (anonymous users).
"""

from __future__ import annotations

import uuid
import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from . import services

logger = logging.getLogger(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _session_key(request) -> str:
    """Return (or create) the cart session key stored in the Django session."""
    key = request.session.get("cart_session_key")
    if not key:
        key = f"ui-{uuid.uuid4().hex}"
        request.session["cart_session_key"] = key
    return key


def _user_id(request) -> str:
    """Anonymous user identity — reuses the session key as a stable identifier."""
    uid = request.session.get("user_id")
    if not uid:
        uid = f"guest-{uuid.uuid4().hex[:12]}"
        request.session["user_id"] = uid
    return uid


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE VIEWS
# ═══════════════════════════════════════════════════════════════════════════════


class HomeView(View):
    """GET / — Hero + featured products grid."""

    def get(self, request):
        featured = services.get_featured_products()
        categories = services.get_categories()
        return render(request, "store/home.html", {
            "featured_products": featured[:8],
            "categories": categories,
            "page_title": "RetailStore — Shop the Best",
        })


class ProductListView(View):
    """GET /products/ — searchable, filterable product grid."""

    def get(self, request):
        search      = request.GET.get("q", "").strip()
        category_id = request.GET.get("category", "")
        ordering    = request.GET.get("ordering", "-created_at")
        try:
            page = int(request.GET.get("page", 1))
        except ValueError:
            page = 1

        cat_id = int(category_id) if category_id.isdigit() else None
        data = services.get_products(
            page=page, page_size=12, search=search,
            category_id=cat_id, ordering=ordering,
        )
        categories = services.get_categories()

        return render(request, "store/product_list.html", {
            "products": data.get("results", []),
            "count": data.get("count", 0),
            "page": page,
            "has_next": bool(data.get("next")),
            "has_prev": page > 1,
            "search": search,
            "selected_category": cat_id,
            "selected_ordering": ordering,
            "categories": categories,
            "page_title": f"Products{' — ' + search if search else ''}",
        })


class ProductDetailView(View):
    """GET /products/<id>/ — product detail + add-to-cart form."""

    def get(self, request, product_id: int):
        product = services.get_product(product_id)
        if not product:
            messages.error(request, "Product not found.")
            return redirect("product-list")

        return render(request, "store/product_detail.html", {
            "product": product,
            "page_title": product.get("name", "Product Detail"),
        })


class CartView(View):
    """GET /cart/ — cart summary page."""

    def get(self, request):
        sk   = _session_key(request)
        cart = services.get_cart(sk)
        return render(request, "store/cart.html", {
            "cart": cart,
            "page_title": "Your Cart",
        })


class CartAddView(View):
    """POST /cart/add/ — add product to cart, redirect back."""

    def post(self, request):
        sk         = _session_key(request)
        product_id = request.POST.get("product_id", "")
        quantity   = request.POST.get("quantity", "1")
        next_url   = request.POST.get("next", "cart")

        try:
            pid = int(product_id)
            qty = max(1, int(quantity))
        except (ValueError, TypeError):
            messages.error(request, "Invalid product or quantity.")
            return redirect(next_url)

        status, data = services.cart_add(sk, pid, qty)
        if status == 201:
            messages.success(request, "Item added to your cart!")
        elif status == 422:
            messages.warning(request, data.get("error", "Item unavailable."))
        elif status == 404:
            messages.error(request, "Product not found in catalog.")
        else:
            messages.error(request, data.get("error", "Could not add item. Try again."))

        return redirect(next_url)


class CartUpdateView(View):
    """POST /cart/update/ — update quantity of a cart item."""

    def post(self, request):
        sk         = _session_key(request)
        product_id = request.POST.get("product_id", "")
        quantity   = request.POST.get("quantity", "1")

        try:
            pid = int(product_id)
            qty = max(1, int(quantity))
        except (ValueError, TypeError):
            messages.error(request, "Invalid data.")
            return redirect("cart")

        status, data = services.cart_update(sk, pid, qty)
        if status != 200:
            messages.error(request, data.get("error", "Could not update item."))
        return redirect("cart")


class CartRemoveView(View):
    """POST /cart/remove/ — remove item from cart."""

    def post(self, request):
        sk         = _session_key(request)
        product_id = request.POST.get("product_id", "")

        try:
            pid = int(product_id)
        except (ValueError, TypeError):
            messages.error(request, "Invalid product.")
            return redirect("cart")

        status, data = services.cart_remove(sk, pid)
        if status == 200:
            messages.success(request, "Item removed from cart.")
        else:
            messages.error(request, data.get("error", "Could not remove item."))
        return redirect("cart")


class CartClearView(View):
    """POST /cart/clear/ — clear entire cart."""

    def post(self, request):
        sk = _session_key(request)
        services.cart_clear(sk)
        messages.success(request, "Cart cleared.")
        return redirect("cart")


class CheckoutView(View):
    """GET/POST /checkout/ — shipping form → place order."""

    def get(self, request):
        sk   = _session_key(request)
        cart = services.get_cart(sk)
        if not cart.get("items"):
            messages.warning(request, "Your cart is empty.")
            return redirect("cart")
        return render(request, "store/checkout.html", {
            "cart": cart,
            "page_title": "Checkout",
        })

    def post(self, request):
        sk      = _session_key(request)
        user_id = _user_id(request)

        cart = services.get_cart(sk)
        if not cart.get("items"):
            messages.warning(request, "Your cart is empty.")
            return redirect("cart")

        shipping = {
            "name":         request.POST.get("name", ""),
            "address_line1":request.POST.get("address_line1", ""),
            "address_line2":request.POST.get("address_line2", ""),
            "city":         request.POST.get("city", ""),
            "pincode":      request.POST.get("pincode", ""),
            "country":      request.POST.get("country", "India"),
        }
        notes = request.POST.get("notes", "")

        status, data = services.place_order(user_id, sk, shipping, notes)
        if status == 201:
            order_id = data.get("id")
            # Re-generate the cart session key so next visit starts fresh
            request.session["cart_session_key"] = f"ui-{uuid.uuid4().hex}"
            return redirect("order-confirm", order_id=order_id)
        elif status == 422:
            messages.warning(request, data.get("error", "Cart is empty."))
            return redirect("cart")
        elif status == 503:
            messages.error(request, "Order service unavailable. Please try again.")
        else:
            messages.error(request, data.get("error", "Order placement failed."))

        return redirect("checkout")


class OrderConfirmView(View):
    """GET /orders/<id>/confirm/ — order placed confirmation page."""

    def get(self, request, order_id: int):
        uid   = _user_id(request)
        order = services.get_order(uid, order_id)
        if not order:
            messages.error(request, "Order not found.")
            return redirect("order-list")
        return render(request, "store/order_confirm.html", {
            "order": order,
            "page_title": f"Order #{order_id} Confirmed!",
        })


class OrderListView(View):
    """GET /orders/ — paginated order history."""

    def get(self, request):
        uid  = _user_id(request)
        try:
            page = int(request.GET.get("page", 1))
        except ValueError:
            page = 1
        data = services.get_orders(uid, page=page)
        return render(request, "store/order_list.html", {
            "orders": data.get("results", []),
            "count": data.get("count", 0),
            "page": page,
            "has_next": page * 10 < data.get("count", 0),
            "has_prev": page > 1,
            "page_title": "My Orders",
        })


class OrderDetailView(View):
    """GET /orders/<id>/ — full order detail."""

    def get(self, request, order_id: int):
        uid   = _user_id(request)
        order = services.get_order(uid, order_id)
        if not order:
            messages.error(request, "Order not found.")
            return redirect("order-list")
        return render(request, "store/order_detail.html", {
            "order": order,
            "page_title": f"Order #{order_id}",
        })


class OrderCancelView(View):
    """POST /orders/<id>/cancel/ — cancel an order."""

    def post(self, request, order_id: int):
        uid    = _user_id(request)
        reason = request.POST.get("reason", "Customer request")
        status, data = services.cancel_order(uid, order_id, reason)
        if status == 200:
            messages.success(request, f"Order #{order_id} has been cancelled.")
        elif status == 409:
            messages.error(request, data.get("error", "Order cannot be cancelled."))
        else:
            messages.error(request, "Could not cancel the order. Please try again.")
        return redirect("order-detail", order_id=order_id)
