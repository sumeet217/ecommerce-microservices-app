"""
Category serializers — multiple levels of detail for different API contexts.
"""

from rest_framework import serializers

from .models import Category


class CategoryMinimalSerializer(serializers.ModelSerializer):
    """Bare-minimum representation — used inside product responses."""

    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class CategorySerializer(serializers.ModelSerializer):
    """
    Standard list/detail serializer.
    Includes computed fields and a shallow parent reference.
    """

    full_path = serializers.ReadOnlyField()
    parent = CategoryMinimalSerializer(read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="parent",
        write_only=True,
        required=False,
        allow_null=True,
    )
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "parent",
            "parent_id",
            "full_path",
            "children_count",
            "is_active",
            "sort_order",
            "image",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at", "full_path")

    def get_children_count(self, obj: Category) -> int:
        return obj.children.filter(is_active=True).count()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Recursive tree representation — use only for small trees (< 200 nodes)
    as it performs N+1 queries without select_related prefetching.
    """

    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "sort_order", "is_active", "children")

    def get_children(self, obj: Category):
        active_children = obj.children.filter(is_active=True).order_by("sort_order", "name")
        return CategoryTreeSerializer(active_children, many=True).data
