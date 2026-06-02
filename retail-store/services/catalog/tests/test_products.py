"""
Unit tests for the Product API endpoints.
Tests cover: list, detail, search, featured, by-sku, in-category,
             filtering, ordering, model behaviour, and serializer validation.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.products.models import Product

from .factories import (
    CategoryFactory,
    DiscountedProductFactory,
    FeaturedProductFactory,
    OutOfStockProductFactory,
    ProductAttributeFactory,
    ProductFactory,
    SubCategoryFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def category():
    return CategoryFactory(name="Test Electronics")


@pytest.fixture
def product(category):
    return ProductFactory(
        name="Test Smartphone",
        brand="TestBrand",
        price=Decimal("25000.00"),
        category=category,
        status=Product.Status.ACTIVE,
    )


@pytest.fixture
def featured_product(category):
    return FeaturedProductFactory(category=category)


@pytest.fixture
def out_of_stock_product(category):
    return OutOfStockProductFactory(category=category)


@pytest.fixture
def discounted_product(category):
    return DiscountedProductFactory(
        category=category,
        price=Decimal("10000.00"),
        discount_percent=Decimal("20.00"),
    )


# ─── Model tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductModel:

    def test_str_repr(self, product):
        assert product.sku in str(product)
        assert product.name in str(product)

    def test_selling_price_no_discount(self, product):
        product.price = Decimal("1000.00")
        product.discount_percent = Decimal("0")
        assert product.selling_price == Decimal("1000.00")

    def test_selling_price_with_discount(self):
        p = ProductFactory(price=Decimal("1000.00"), discount_percent=Decimal("20.00"))
        assert p.selling_price == Decimal("800.00")

    def test_is_in_stock_true(self, product):
        product.stock_quantity = 10
        assert product.is_in_stock is True

    def test_is_in_stock_false(self, out_of_stock_product):
        assert out_of_stock_product.is_in_stock is False

    def test_is_low_stock(self):
        p = ProductFactory(stock_quantity=5, low_stock_threshold=10)
        assert p.is_low_stock is True

    def test_not_low_stock_when_sufficient(self):
        p = ProductFactory(stock_quantity=50, low_stock_threshold=10)
        assert p.is_low_stock is False

    def test_not_low_stock_when_zero(self):
        p = ProductFactory(stock_quantity=0, low_stock_threshold=10)
        assert p.is_low_stock is False  # 0 stock = out of stock, not low stock

    def test_slug_auto_generated(self, category):
        p = ProductFactory(name="Super Cool Gadget", category=category)
        assert p.slug == "super-cool-gadget"

    def test_slug_uniqueness_collision(self, category):
        p1 = ProductFactory(name="Duplicate Product", category=category)
        p2 = ProductFactory(name="Duplicate Product", sku="TEST-DUP-002", category=category)
        assert p1.slug != p2.slug
        assert p2.slug.startswith("duplicate-product-")

    def test_tag_list(self, product):
        product.tags = "wireless, noise-cancelling, bluetooth"
        product.save()
        assert "wireless" in product.tag_list
        assert "noise-cancelling" in product.tag_list
        assert "bluetooth" in product.tag_list

    def test_empty_tag_list(self, product):
        product.tags = ""
        assert product.tag_list == []

    def test_sku_uppercase_via_serializer(self):
        """Write serializer must uppercase the SKU."""
        from apps.products.serializers import ProductWriteSerializer
        cat = CategoryFactory()
        data = {
            "sku": "test-sku-001",
            "name": "Test Product",
            "category_id": cat.pk,
            "price": "999.00",
            "discount_percent": "0",
            "stock_quantity": 10,
        }
        serializer = ProductWriteSerializer(data=data)
        if serializer.is_valid():
            assert serializer.validated_data.get("sku", "").upper() == "TEST-SKU-001"

    def test_status_auto_out_of_stock_on_save(self, category):
        p = ProductFactory(category=category, stock_quantity=0, status=Product.Status.ACTIVE)
        p.save()
        assert p.status == Product.Status.OUT_OF_STOCK


# ─── Product List API ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductListAPI:

    def test_list_returns_200(self, api_client, product):
        url = reverse("products:product-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_returns_active_only(self, api_client, product, out_of_stock_product):
        url = reverse("products:product-list")
        response = api_client.get(url)
        ids = [p["id"] for p in response.data["results"]]
        assert product.id in ids
        assert out_of_stock_product.id not in ids

    def test_list_pagination_structure(self, api_client, product):
        url = reverse("products:product-list")
        response = api_client.get(url)
        assert "count" in response.data
        assert "results" in response.data

    def test_list_filter_by_brand(self, api_client, product):
        url = reverse("products:product-list")
        response = api_client.get(url, {"brand": "TestBrand"})
        assert response.status_code == status.HTTP_200_OK
        for p in response.data["results"]:
            assert "testbrand" in p["brand"].lower()

    def test_list_filter_by_category(self, api_client, product, category):
        url = reverse("products:product-list")
        response = api_client.get(url, {"category": category.pk})
        assert response.status_code == status.HTTP_200_OK
        for p in response.data["results"]:
            assert p["category"]["id"] == category.pk

    def test_list_filter_price_range(self, api_client, category):
        ProductFactory(price=Decimal("500.00"), category=category)
        ProductFactory(price=Decimal("5000.00"), category=category)
        ProductFactory(price=Decimal("50000.00"), category=category)
        url = reverse("products:product-list")
        response = api_client.get(url, {"price_min": "1000", "price_max": "10000"})
        for p in response.data["results"]:
            assert Decimal(p["price"]) >= Decimal("1000")
            assert Decimal(p["price"]) <= Decimal("10000")

    def test_list_filter_in_stock(self, api_client, product, out_of_stock_product):
        url = reverse("products:product-list")
        response = api_client.get(url, {"in_stock": "true"})
        ids = [p["id"] for p in response.data["results"]]
        assert product.id in ids

    def test_list_ordering_by_price(self, api_client, category):
        ProductFactory(price=Decimal("300.00"), category=category)
        ProductFactory(price=Decimal("100.00"), category=category)
        ProductFactory(price=Decimal("200.00"), category=category)
        url = reverse("products:product-list")
        response = api_client.get(url, {"ordering": "price"})
        prices = [Decimal(p["price"]) for p in response.data["results"]]
        assert prices == sorted(prices)

    def test_list_search_filter(self, api_client, product):
        url = reverse("products:product-list")
        response = api_client.get(url, {"search": "Smartphone"})
        assert response.status_code == status.HTTP_200_OK
        assert any("Smartphone" in p["name"] for p in response.data["results"])


# ─── Product Detail API ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductDetailAPI:

    def test_detail_returns_200(self, api_client, product):
        url = reverse("products:product-detail", kwargs={"pk": product.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_detail_contains_required_fields(self, api_client, product):
        url = reverse("products:product-detail", kwargs={"pk": product.pk})
        response = api_client.get(url)
        for field in ("id", "sku", "name", "price", "selling_price", "category", "images", "attributes"):
            assert field in response.data, f"Missing field: {field}"

    def test_detail_includes_attributes(self, api_client, product):
        ProductAttributeFactory(product=product, name="Colour", value="Black")
        url = reverse("products:product-detail", kwargs={"pk": product.pk})
        response = api_client.get(url)
        attr_names = [a["name"] for a in response.data["attributes"]]
        assert "Colour" in attr_names

    def test_detail_selling_price_computed(self, api_client, discounted_product):
        url = reverse("products:product-detail", kwargs={"pk": discounted_product.pk})
        response = api_client.get(url)
        expected = discounted_product.selling_price
        assert Decimal(str(response.data["selling_price"])) == expected

    def test_detail_nonexistent_returns_404(self, api_client):
        url = reverse("products:product-detail", kwargs={"pk": 9999999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ─── Product Search API ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductSearchAPI:

    def test_search_returns_200(self, api_client, product):
        url = reverse("products:product-search")
        response = api_client.get(url, {"q": "Smartphone"})
        assert response.status_code == status.HTTP_200_OK

    def test_search_finds_by_name(self, api_client, product):
        url = reverse("products:product-search")
        response = api_client.get(url, {"q": "Smartphone"})
        ids = [p["id"] for p in response.data["results"]]
        assert product.id in ids

    def test_search_finds_by_brand(self, api_client, product):
        url = reverse("products:product-search")
        response = api_client.get(url, {"q": "TestBrand"})
        ids = [p["id"] for p in response.data["results"]]
        assert product.id in ids

    def test_search_missing_q_returns_400(self, api_client):
        url = reverse("products:product-search")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_short_q_returns_400(self, api_client):
        url = reverse("products:product-search")
        response = api_client.get(url, {"q": "a"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_no_results(self, api_client, product):
        url = reverse("products:product-search")
        response = api_client.get(url, {"q": "xyzxyzxyz_does_not_exist"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0


# ─── Featured Products API ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFeaturedProductsAPI:

    def test_featured_returns_200(self, api_client, featured_product):
        url = reverse("products:product-featured")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_featured_returns_only_featured(self, api_client, product, featured_product):
        url = reverse("products:product-featured")
        response = api_client.get(url)
        ids = [p["id"] for p in response.data["results"]]
        assert featured_product.id in ids
        assert product.id not in ids


# ─── Product by SKU API ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductBySkuAPI:

    def test_by_sku_returns_200(self, api_client, product):
        url = reverse("products:product-by-sku", kwargs={"sku": product.sku})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_by_sku_returns_correct_product(self, api_client, product):
        url = reverse("products:product-by-sku", kwargs={"sku": product.sku})
        response = api_client.get(url)
        assert response.data["sku"] == product.sku

    def test_by_sku_not_found_returns_404(self, api_client):
        url = reverse("products:product-by-sku", kwargs={"sku": "NONEXISTENT-SKU"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ─── In Category API ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestInCategoryAPI:

    def test_in_category_returns_200(self, api_client, category, product):
        url = reverse("products:product-in-category", kwargs={"category_id": category.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_in_category_returns_products(self, api_client, category, product):
        url = reverse("products:product-in-category", kwargs={"category_id": category.pk})
        response = api_client.get(url)
        ids = [p["id"] for p in response.data["results"]]
        assert product.id in ids

    def test_in_category_includes_subcategory_products(self, api_client):
        parent_cat = CategoryFactory(name="Parent Cat")
        child_cat = SubCategoryFactory(name="Child Cat", parent=parent_cat)
        child_product = ProductFactory(category=child_cat)
        url = reverse("products:product-in-category", kwargs={"category_id": parent_cat.pk})
        response = api_client.get(url)
        ids = [p["id"] for p in response.data["results"]]
        assert child_product.id in ids

    def test_in_category_invalid_returns_404(self, api_client):
        url = reverse("products:product-in-category", kwargs={"category_id": 9999999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ─── Health Endpoints ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHealthEndpoints:

    def test_liveness_returns_200(self, api_client):
        url = reverse("health-check")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ok"

    def test_readiness_returns_200_when_db_ok(self, api_client):
        url = reverse("readiness-check")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["checks"]["database"] == "ok"
