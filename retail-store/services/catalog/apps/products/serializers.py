"""
Product serializers — multiple verbosity levels for different consumers.
"""

from decimal import Decimal

from rest_framework import serializers

from apps.categories.serializers import CategoryMinimalSerializer

from .models import Product, ProductAttribute, ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt_text", "is_primary", "sort_order")


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ("id", "name", "value", "unit")


class ProductListSerializer(serializers.ModelSerializer):
    """
    Compact representation used in list endpoints.
    Avoids N+1 by relying on select_related/prefetch_related set in the view.
    """

    category = CategoryMinimalSerializer(read_only=True)
    selling_price = serializers.ReadOnlyField()
    primary_image_url = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "name",
            "slug",
            "short_description",
            "category",
            "brand",
            "price",
            "discount_percent",
            "selling_price",
            "currency",
            "stock_quantity",
            "status",
            "is_featured",
            "is_in_stock",
            "rating_avg",
            "rating_count",
            "primary_image_url",
            "tag_list",
            "created_at",
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Full product detail — includes images, attributes, and all fields.
    """

    category = CategoryMinimalSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    selling_price = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()
    primary_image_url = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "name",
            "slug",
            "description",
            "short_description",
            "category",
            "brand",
            "tags",
            "tag_list",
            "price",
            "discount_percent",
            "selling_price",
            "currency",
            "stock_quantity",
            "low_stock_threshold",
            "is_in_stock",
            "is_low_stock",
            "weight_grams",
            "status",
            "is_featured",
            "rating_avg",
            "rating_count",
            "images",
            "primary_image_url",
            "attributes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id", "slug", "selling_price", "is_in_stock", "is_low_stock",
            "tag_list", "primary_image_url", "created_at", "updated_at",
        )


class ProductWriteSerializer(serializers.ModelSerializer):
    """
    Write serializer — used for create/update operations.
    Validates business rules (e.g. discount cannot exceed 90%).
    """

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__("apps.categories.models", fromlist=["Category"]).Category.objects.filter(is_active=True),
        source="category",
    )

    class Meta:
        model = Product
        fields = (
            "sku",
            "name",
            "description",
            "short_description",
            "category_id",
            "brand",
            "tags",
            "price",
            "discount_percent",
            "currency",
            "stock_quantity",
            "low_stock_threshold",
            "weight_grams",
            "status",
            "is_featured",
        )

    def validate_discount_percent(self, value: Decimal) -> Decimal:
        if value > 90:
            raise serializers.ValidationError("Discount cannot exceed 90%.")
        return value

    def validate_price(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate(self, attrs):
        # Ensure SKU is uppercase
        if "sku" in attrs:
            attrs["sku"] = attrs["sku"].upper()
        return attrs
