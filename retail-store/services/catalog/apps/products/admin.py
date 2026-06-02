"""
Product Django Admin — rich interface for product management.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Product, ProductAttribute, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "is_primary", "sort_order")


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 2
    fields = ("name", "value", "unit")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku", "name", "category", "brand", "price",
        "discount_percent", "selling_price_display",
        "stock_quantity", "status", "is_featured",
        "rating_avg", "created_at",
    )
    list_filter = ("status", "is_featured", "category", "brand", "currency")
    search_fields = ("sku", "name", "brand", "tags", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("status", "is_featured", "stock_quantity")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = [ProductImageInline, ProductAttributeInline]

    fieldsets = (
        ("Identity", {
            "fields": ("sku", "name", "slug", "short_description", "description"),
        }),
        ("Classification", {
            "fields": ("category", "brand", "tags"),
        }),
        ("Pricing", {
            "fields": ("price", "discount_percent", "currency"),
        }),
        ("Inventory", {
            "fields": ("stock_quantity", "low_stock_threshold", "weight_grams"),
        }),
        ("Status & Visibility", {
            "fields": ("status", "is_featured"),
        }),
        ("Ratings (read-only)", {
            "fields": ("rating_avg", "rating_count"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("rating_avg", "rating_count", "created_at", "updated_at")

    def selling_price_display(self, obj):
        sp = obj.selling_price
        if obj.discount_percent > 0:
            return format_html(
                '<span style="color:green;">{} {}</span>',
                obj.currency,
                sp,
            )
        return f"{obj.currency} {sp}"

    selling_price_display.short_description = "Selling Price"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "alt_text", "sort_order")
    list_filter = ("is_primary",)
    search_fields = ("product__sku", "product__name", "alt_text")


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "value", "unit")
    search_fields = ("product__sku", "name", "value")
