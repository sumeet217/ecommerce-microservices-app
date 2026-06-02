"""
Category API views.
"""

import logging

from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import CategoryFilter
from .models import Category
from .serializers import CategorySerializer, CategoryTreeSerializer

logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:   GET  /api/v1/catalog/categories/
    detail: GET  /api/v1/catalog/categories/{id}/
    tree:   GET  /api/v1/catalog/categories/tree/
    """

    serializer_class = CategorySerializer
    filterset_class = CategoryFilter
    search_fields = ["name", "description"]
    ordering_fields = ["name", "sort_order", "created_at"]
    ordering = ["sort_order", "name"]
    lookup_field = "pk"

    def get_queryset(self):
        return (
            Category.objects.filter(is_active=True)
            .select_related("parent")
            .prefetch_related(
                Prefetch(
                    "children",
                    queryset=Category.objects.filter(is_active=True),
                )
            )
        )

    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request: Request) -> Response:
        """
        Returns the full active category tree starting from root nodes.
        Useful for rendering navigation menus in the UI service.
        """
        root_categories = (
            Category.objects.filter(is_active=True, parent__isnull=True)
            .prefetch_related("children__children")
            .order_by("sort_order", "name")
        )
        serializer = CategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="children")
    def children(self, request: Request, pk=None) -> Response:
        """
        Returns immediate children of a given category.
        GET /api/v1/catalog/categories/{id}/children/
        """
        category = self.get_object()
        children_qs = category.children.filter(is_active=True).order_by("sort_order", "name")
        serializer = CategorySerializer(children_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
