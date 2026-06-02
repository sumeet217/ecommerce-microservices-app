"""
Factory Boy factories for generating test data.
"""

import factory
from faker import Faker

from apps.categories.models import Category
from apps.products.models import Product, ProductAttribute, ProductImage

fake = Faker()


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Category {n}")
    description = factory.LazyFunction(fake.sentence)
    is_active = True
    sort_order = factory.Sequence(lambda n: n)
    parent = None


class SubCategoryFactory(CategoryFactory):
    """A category with a parent."""

    name = factory.Sequence(lambda n: f"SubCategory {n}")
    parent = factory.SubFactory(CategoryFactory)


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product
        django_get_or_create = ("sku",)

    sku = factory.Sequence(lambda n: f"TEST-SKU-{n:04d}")
    name = factory.LazyFunction(lambda: fake.sentence(nb_words=4).rstrip("."))
    short_description = factory.LazyFunction(fake.sentence)
    description = factory.LazyFunction(fake.paragraph)
    category = factory.SubFactory(CategoryFactory)
    brand = factory.LazyFunction(fake.company)
    price = factory.LazyFunction(lambda: round(fake.pydecimal(left_digits=4, right_digits=2, positive=True), 2))
    discount_percent = 0
    currency = "INR"
    stock_quantity = 100
    status = Product.Status.ACTIVE
    is_featured = False
    rating_avg = 0
    rating_count = 0
    tags = factory.LazyFunction(lambda: ",".join(fake.words(3)))


class DiscountedProductFactory(ProductFactory):
    discount_percent = factory.LazyFunction(lambda: fake.pydecimal(
        left_digits=2, right_digits=2, positive=True, min_value=5, max_value=50
    ))


class FeaturedProductFactory(ProductFactory):
    is_featured = True


class OutOfStockProductFactory(ProductFactory):
    stock_quantity = 0
    status = Product.Status.OUT_OF_STOCK


class ProductImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductImage

    product = factory.SubFactory(ProductFactory)
    alt_text = factory.LazyFunction(fake.sentence)
    is_primary = False
    sort_order = factory.Sequence(lambda n: n)


class ProductAttributeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductAttribute

    product = factory.SubFactory(ProductFactory)
    name = factory.LazyFunction(lambda: fake.word().capitalize())
    value = factory.LazyFunction(fake.word)
    unit = ""
