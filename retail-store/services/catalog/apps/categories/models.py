"""
Category models — supports unlimited depth via MPTT-style self-referential FK.
Uses a simple adjacency list (parent FK) which is sufficient for 3-tier
product hierarchies (e.g. Electronics → Phones → Smartphones).
"""

import logging

from django.db import models
from django.utils.text import slugify

logger = logging.getLogger(__name__)


class Category(models.Model):
    """
    Hierarchical product category.
    A null parent means the category is a root-level category.
    """

    name = models.CharField(max_length=255, unique=True, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        db_index=True,
    )
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveSmallIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "catalog_category"
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["parent", "is_active"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    @property
    def full_path(self) -> str:
        """Returns breadcrumb path, e.g. 'Electronics > Phones > Smartphones'."""
        parts = [self.name]
        node = self.parent
        while node is not None:
            parts.insert(0, node.name)
            node = node.parent
        return " > ".join(parts)

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def depth(self) -> int:
        """0-indexed depth in the hierarchy."""
        d = 0
        node = self.parent
        while node is not None:
            d += 1
            node = node.parent
        return d
