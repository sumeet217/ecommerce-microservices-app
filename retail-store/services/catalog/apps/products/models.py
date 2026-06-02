"""
Product models — core entities for the Catalog Service.

Entities:
  Product        — the main sellable item
  ProductImage   — one-to-many images per product
  ProductAttribute — flexible key/value attributes (colour, size, material…)
"""

import logging
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.categories.models import Category

logger = logging.getLogger(__name__)


class Product(models.Model):
    """
    Core product entity.

    Pricing strategy: price is the base (MRP); discount_percent reduces it.
    The effective selling price is computed as a property.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        OUT_OF_STOCK = "out_of_stock", "Out of Stock"

    # ── Identity ───────────────────────────────────────────────────────────────
    sku = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Stock Keeping Unit — must be globally unique.",
    )
    name = models.CharField(max_length=512, db_index=True)
    slug = models.SlugField(max_length=512, unique=True, blank=True, db_index=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=512, blank=True)

    # ── Classification ─────────────────────────────────────────────────────────
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        db_index=True,
    )
    brand = models.CharField(max_length=255, blank=True, db_index=True)
    tags = models.CharField(
        max_length=1024,
        blank=True,
        help_text="Comma-separated tags for filtering (e.g. 'wireless,noise-cancelling').",
    )

    # ── Pricing ────────────────────────────────────────────────────────────────
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Base / MRP price.",
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    currency = models.CharField(max_length=3, default="INR")

    # ── Inventory ──────────────────────────────────────────────────────────────
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)

    # ── Physical attributes ────────────────────────────────────────────────────
    weight_grams = models.PositiveIntegerField(null=True, blank=True)

    # ── Status & visibility ───────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    is_featured = models.BooleanField(default=False, db_index=True)

    # ── Ratings (denormalised for fast reads; updated by the Orders service) ──
    rating_avg = models.DecimalField(
        max_digits=3, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    rating_count = models.PositiveIntegerField(default=0)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalog_product"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_featured"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["brand", "status"]),
            models.Index(fields=["price"]),
        ]

    # ── Lifecycle ──────────────────────────────────────────────────────────────
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Auto-set status to out_of_stock if stock is 0 and product was active
        if self.stock_quantity == 0 and self.status == self.Status.ACTIVE:
            self.status = self.Status.OUT_OF_STOCK

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"[{self.sku}] {self.name}"

    # ── Computed properties ────────────────────────────────────────────────────
    @property
    def selling_price(self):
        """Effective price after discount."""
        from decimal import Decimal
        discount = (self.discount_percent / Decimal("100")) * self.price
        return round(self.price - discount, 2)

    @property
    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def tag_list(self) -> list:
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def primary_image_url(self) -> str | None:
        img = self.images.filter(is_primary=True).first()
        if img and img.image:
            return img.image.url
        img = self.images.first()
        return img.image.url if img and img.image else None


class ProductImage(models.Model):
    """One-to-many images associated with a product."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="products/images/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "catalog_product_image"
        ordering = ["-is_primary", "sort_order"]
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self) -> str:
        return f"Image for {self.product.sku} (primary={self.is_primary})"


class ProductAttribute(models.Model):
    """
    Flexible key-value attributes for a product (e.g. colour=Red, size=XL).
    Stored as plain text; type-safe variants can be added via separate tables.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="attributes",
    )
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=512)
    unit = models.CharField(max_length=50, blank=True, help_text="e.g. cm, kg, GHz")

    class Meta:
        db_table = "catalog_product_attribute"
        unique_together = ("product", "name")
        verbose_name = "Product Attribute"
        verbose_name_plural = "Product Attributes"

    def __str__(self) -> str:
        unit_str = f" {self.unit}" if self.unit else ""
        return f"{self.name}: {self.value}{unit_str}"
