"""
Product API views.
Supports list, detail, search, and featured endpoints.
"""

import logging

from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import ProductFilter
from .models import Product
from .serializers import ProductDetailSerializer, ProductListSerializer, ProductWriteSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Returns a paginated list of active products with filtering and search.",
        parameters=[
            OpenApiParameter("q", str, description="Full-text search across name, brand, description, tags"),
            OpenApiParameter("category", int, description="Filter by category ID"),
            OpenApiParameter("brand", str, description="Filter by brand name (case-insensitive)"),
            OpenApiParameter("price_min", float, description="Minimum price filter"),
            OpenApiParameter("price_max", float, description="Maximum price filter"),
            OpenApiParameter("in_stock", bool, description="Only return in-stock products"),
            OpenApiParameter("is_featured", bool, description="Only return featured products"),
        ],
    ),
    retrieve=extend_schema(
        summary="Get product detail",
        description="Returns full product detail including images and attributes.",
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    list:       GET    /api/v1/catalog/products/
    retrieve:   GET    /api/v1/catalog/products/{id}/
    search:     GET    /api/v1/catalog/products/search/?q=<term>
    featured:   GET    /api/v1/catalog/products/featured/
    by_sku:     GET    /api/v1/catalog/products/by-sku/{sku}/
    """

    filterset_class = ProductFilter
    search_fields = ["name", "description", "short_description", "brand", "tags", "sku"]
    ordering_fields = ["name", "price", "rating_avg", "created_at", "discount_percent"]
    ordering = ["-created_at"]

    def get_queryset(self):
        base_qs = (
            Product.objects.filter(status=Product.Status.ACTIVE)
            .select_related("category")
            .prefetch_related("images", "attributes")
        )
        return base_qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductWriteSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    # ── Custom actions ─────────────────────────────────────────────────────────

    @extend_schema(
        summary="Search products",
        parameters=[
            OpenApiParameter(
                "q",
                str,
                required=True,
                description="Search term matched against name, description, brand, and tags.",
            )
        ],
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request: Request) -> Response:
        """
        Full-text product search.
        GET /api/v1/catalog/products/search/?q=<term>
        """
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response(
                {"detail": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(query) < 2:
            return Response(
                {"detail": "Search term must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(short_description__icontains=query)
            | Q(brand__icontains=query)
            | Q(tags__icontains=query)
            | Q(sku__iexact=query)
            | Q(category__name__icontains=query)
        ).distinct()

        # Apply standard ordering
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = ProductListSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @extend_schema(summary="Get featured products")
    @action(detail=False, methods=["get"], url_path="featured")
    def featured(self, request: Request) -> Response:
        """
        Returns featured / promoted products.
        GET /api/v1/catalog/products/featured/
        """
        queryset = self.get_queryset().filter(is_featured=True)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = ProductListSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @extend_schema(
        summary="Get product by SKU",
        parameters=[OpenApiParameter("sku", str, location="path", description="Product SKU")],
    )
    @action(detail=False, methods=["get"], url_path=r"by-sku/(?P<sku>[A-Z0-9\-]+)")
    def by_sku(self, request: Request, sku: str = None) -> Response:
        """
        Lookup a product by its SKU — used by the Cart and Orders services.
        GET /api/v1/catalog/products/by-sku/{SKU}/
        """
        try:
            product = self.get_queryset().get(sku=sku.upper())
        except Product.DoesNotExist:
            return Response(
                {"detail": f"Product with SKU '{sku}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProductDetailSerializer(product, context=self.get_serializer_context())
        return Response(serializer.data)

    @extend_schema(summary="Get products by category")
    @action(detail=False, methods=["get"], url_path=r"in-category/(?P<category_id>[0-9]+)")
    def in_category(self, request: Request, category_id: int = None) -> Response:
        """
        Returns all active products within a given category (and subcategories).
        GET /api/v1/catalog/products/in-category/{id}/
        """
        from apps.categories.models import Category

        try:
            category = Category.objects.get(pk=category_id, is_active=True)
        except Category.DoesNotExist:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Collect IDs of the category and all its children (one level deep)
        cat_ids = [category.pk] + list(
            category.children.filter(is_active=True).values_list("pk", flat=True)
        )
        queryset = self.get_queryset().filter(category__id__in=cat_ids)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = ProductListSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
