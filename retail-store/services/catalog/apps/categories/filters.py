"""
Category filtering via django-filter.
"""

import django_filters

from .models import Category


class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    is_active = django_filters.BooleanFilter()
    parent = django_filters.NumberFilter(field_name="parent__id")
    root_only = django_filters.BooleanFilter(
        field_name="parent",
        lookup_expr="isnull",
        label="Root categories only",
    )

    class Meta:
        model = Category
        fields = ["name", "is_active", "parent", "root_only"]
