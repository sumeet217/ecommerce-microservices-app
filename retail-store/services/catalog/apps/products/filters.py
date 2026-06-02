"""
Product filtering — rich filter set for search, range queries, and faceting.
"""

import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    # ── Text search ───────────────────────────────────────────────────────────
    name = django_filters.CharFilter(lookup_expr="icontains")
    brand = django_filters.CharFilter(lookup_expr="icontains")
    sku = django_filters.CharFilter(lookup_expr="iexact")
    tags = django_filters.CharFilter(method="filter_by_tag", label="Tag contains")

    # ── Category ──────────────────────────────────────────────────────────────
    category = django_filters.NumberFilter(field_name="category__id")
    category_slug = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")

    # ── Price range ───────────────────────────────────────────────────────────
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    # ── Status & flags ────────────────────────────────────────────────────────
    status = django_filters.ChoiceFilter(choices=Product.Status.choices)
    is_featured = django_filters.BooleanFilter()
    in_stock = django_filters.BooleanFilter(
        field_name="stock_quantity",
        lookup_expr="gt",
        label="In stock only",
    )

    # ── Rating ────────────────────────────────────────────────────────────────
    min_rating = django_filters.NumberFilter(field_name="rating_avg", lookup_expr="gte")

    class Meta:
        model = Product
        fields = [
            "name", "brand", "sku", "tags",
            "category", "category_slug",
            "price_min", "price_max",
            "status", "is_featured", "in_stock",
            "min_rating",
        ]

    def filter_by_tag(self, queryset, name, value):
        """Filter products whose tag string contains the given tag."""
        return queryset.filter(tags__icontains=value)
