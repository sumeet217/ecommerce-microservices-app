"""
Cart Service — Catalog Service HTTP client.

Uses httpx for synchronous HTTP calls to validate product existence
and fetch the current price before adding an item to the cart.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

CATALOG_URL: str = getattr(settings, "CATALOG_SERVICE_URL", "http://catalog-service:8001")
TIMEOUT: int = getattr(settings, "CATALOG_SERVICE_TIMEOUT", 5)


class CatalogServiceError(Exception):
    """Raised when the Catalog Service returns an unexpected response."""


class ProductNotFoundError(CatalogServiceError):
    """Raised when the requested product does not exist in the catalog."""


class ProductUnavailableError(CatalogServiceError):
    """Raised when the product exists but is not available for purchase."""


def _build_client() -> httpx.Client:
    return httpx.Client(
        base_url=CATALOG_URL,
        timeout=TIMEOUT,
        headers={"Accept": "application/json", "X-Request-Source": "cart-service"},
    )


def get_product(product_id: int) -> dict:
    """
    Fetch a product from the Catalog Service by primary key.

    Returns a dict with at least:
        id, name, sku, price (str), currency, status, stock_quantity

    Raises:
        ProductNotFoundError      — HTTP 404
        ProductUnavailableError   — product exists but status != 'active'
        CatalogServiceError       — any other HTTP / network error
    """
    url = f"/api/v1/catalog/products/{product_id}/"
    try:
        with _build_client() as client:
            response = client.get(url)
    except httpx.TimeoutException as exc:
        raise CatalogServiceError(
            f"Timed out connecting to Catalog Service ({CATALOG_URL})."
        ) from exc
    except httpx.RequestError as exc:
        raise CatalogServiceError(
            f"Network error connecting to Catalog Service: {exc}"
        ) from exc

    if response.status_code == 404:
        raise ProductNotFoundError(f"Product {product_id} not found in the catalog.")

    if response.status_code != 200:
        raise CatalogServiceError(
            f"Catalog Service returned HTTP {response.status_code} for product {product_id}."
        )

    try:
        data = response.json()
    except Exception as exc:
        raise CatalogServiceError("Catalog Service returned non-JSON response.") from exc

    status = data.get("status", "")
    if status not in ("active",):
        raise ProductUnavailableError(
            f"Product '{data.get('name', product_id)}' is not available for purchase "
            f"(status={status!r})."
        )

    if data.get("stock_quantity", 0) <= 0:
        raise ProductUnavailableError(
            f"Product '{data.get('name', product_id)}' is out of stock."
        )

    return data
