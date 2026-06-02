"""
UI Service — HTTP client layer.

All calls to the three backend services go through this module.
Every function returns plain Python dicts/lists so views stay clean.
Errors are logged and empty/None is returned — the UI degrades gracefully.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT = getattr(settings, "SERVICE_TIMEOUT", 8)
CATALOG = getattr(settings, "CATALOG_SERVICE_URL", "http://catalog-service:8001")
CART    = getattr(settings, "CART_SERVICE_URL",    "http://cart-service:8002")
ORDERS  = getattr(settings, "ORDERS_SERVICE_URL",  "http://orders-service:8003")


# ─── Generic helper ───────────────────────────────────────────────────────────


def _get(base: str, path: str, params: dict | None = None,
         headers: dict | None = None) -> dict | list | None:
    url = urljoin(base, path)
    try:
        r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as exc:
        logger.warning("GET %s → %s", url, exc.response.status_code)
        return None
    except Exception as exc:
        logger.error("GET %s failed: %s", url, exc)
        return None


def _post(base: str, path: str, json: dict,
          headers: dict | None = None) -> tuple[int, dict]:
    url = urljoin(base, path)
    try:
        r = requests.post(url, json=json, headers=headers, timeout=TIMEOUT)
        return r.status_code, r.json()
    except Exception as exc:
        logger.error("POST %s failed: %s", url, exc)
        return 503, {"error": str(exc)}


def _put(base: str, path: str, json: dict,
         headers: dict | None = None) -> tuple[int, dict]:
    url = urljoin(base, path)
    try:
        r = requests.put(url, json=json, headers=headers, timeout=TIMEOUT)
        return r.status_code, r.json()
    except Exception as exc:
        logger.error("PUT %s failed: %s", url, exc)
        return 503, {"error": str(exc)}


def _delete(base: str, path: str, json: dict | None = None,
            headers: dict | None = None) -> tuple[int, dict]:
    url = urljoin(base, path)
    try:
        r = requests.delete(url, json=json, headers=headers, timeout=TIMEOUT)
        return r.status_code, (r.json() if r.content else {})
    except Exception as exc:
        logger.error("DELETE %s failed: %s", url, exc)
        return 503, {"error": str(exc)}


def _cart_headers(session_key: str) -> dict:
    return {"X-Session-Key": session_key}


# ═══════════════════════════════════════════════════════════════════════════════
# CATALOG SERVICE
# ═══════════════════════════════════════════════════════════════════════════════


def get_featured_products() -> list[dict]:
    data = _get(CATALOG, "/api/v1/catalog/products/featured/")
    if data and isinstance(data, dict):
        return data.get("results", data.get("items", []))
    return []


def get_products(page: int = 1, page_size: int = 12,
                 search: str = "", category_id: int | None = None,
                 ordering: str = "-created_at") -> dict:
    """Returns paginated product list: {count, next, previous, results}."""
    params: dict = {"page": page, "page_size": page_size, "ordering": ordering}
    if search:
        params["search"] = search
    if category_id:
        params["category"] = category_id

    if search:
        data = _get(CATALOG, "/api/v1/catalog/products/search/",
                    params={"q": search, "page": page})
    else:
        data = _get(CATALOG, "/api/v1/catalog/products/", params=params)

    return data or {"count": 0, "results": []}


def get_product(product_id: int) -> dict | None:
    return _get(CATALOG, f"/api/v1/catalog/products/{product_id}/")


def get_categories() -> list[dict]:
    data = _get(CATALOG, "/api/v1/catalog/categories/")
    if data and isinstance(data, dict):
        return data.get("results", [])
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# CART SERVICE
# ═══════════════════════════════════════════════════════════════════════════════


def get_cart(session_key: str) -> dict:
    data = _get(CART, "/api/v1/cart/", headers=_cart_headers(session_key))
    return data or {"items": [], "total_items": 0, "subtotal": "0.00"}


def cart_add(session_key: str, product_id: int, quantity: int = 1) -> tuple[int, dict]:
    return _post(
        CART, "/api/v1/cart/add/",
        json={"product_id": product_id, "quantity": quantity,
              "validate_with_catalog": True},
        headers=_cart_headers(session_key),
    )


def cart_update(session_key: str, product_id: int, quantity: int) -> tuple[int, dict]:
    return _put(
        CART, "/api/v1/cart/update/",
        json={"product_id": product_id, "quantity": quantity},
        headers=_cart_headers(session_key),
    )


def cart_remove(session_key: str, product_id: int) -> tuple[int, dict]:
    return _delete(
        CART, "/api/v1/cart/remove/",
        json={"product_id": product_id},
        headers=_cart_headers(session_key),
    )


def cart_clear(session_key: str) -> tuple[int, dict]:
    return _delete(CART, "/api/v1/cart/clear/",
                   headers=_cart_headers(session_key))


# ═══════════════════════════════════════════════════════════════════════════════
# ORDERS SERVICE
# ═══════════════════════════════════════════════════════════════════════════════


def place_order(user_id: str, session_key: str, shipping: dict,
                notes: str = "") -> tuple[int, dict]:
    return _post(
        ORDERS, "/api/v1/orders/place/",
        json={"user_id": user_id, "session_key": session_key,
              "shipping": shipping, "notes": notes},
    )


def get_orders(user_id: str, page: int = 1) -> dict:
    data = _get(ORDERS, "/api/v1/orders/",
                params={"page": page, "page_size": 10},
                headers={"X-User-Id": user_id})
    return data or {"count": 0, "results": []}


def get_order(user_id: str, order_id: int) -> dict | None:
    return _get(ORDERS, f"/api/v1/orders/{order_id}/",
                headers={"X-User-Id": user_id})


def cancel_order(user_id: str, order_id: int,
                 reason: str = "") -> tuple[int, dict]:
    return _put(
        ORDERS, f"/api/v1/orders/{order_id}/cancel/",
        json={"reason": reason},
        headers={"X-User-Id": user_id},
    )
