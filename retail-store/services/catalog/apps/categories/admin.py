"""
Category Django Admin registration.
"""

from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "parent", "is_active", "sort_order", "created_at")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active", "sort_order")
    ordering = ("sort_order", "name")
    raw_id_fields = ("parent",)

    fieldsets = (
        ("Basic Info", {"fields": ("name", "slug", "description", "image")}),
        ("Hierarchy", {"fields": ("parent", "sort_order")}),
        ("Status", {"fields": ("is_active",)}),
    )
