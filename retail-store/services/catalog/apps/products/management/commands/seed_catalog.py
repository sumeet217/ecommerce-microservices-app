"""
Management command: seed_catalog
Populates the database with demo categories and products for development/testing.

Usage:
    python manage.py seed_catalog
    python manage.py seed_catalog --clear     # wipe existing data first
"""

import logging
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.categories.models import Category
from apps.products.models import Product, ProductAttribute

logger = logging.getLogger(__name__)

CATEGORIES = [
    # (name, parent_name, description)
    ("Electronics", None, "All electronic gadgets and devices"),
    ("Phones & Tablets", "Electronics", "Smartphones, feature phones, and tablets"),
    ("Smartphones", "Phones & Tablets", "Latest smartphones from top brands"),
    ("Tablets", "Phones & Tablets", "iPads, Android tablets, and e-readers"),
    ("Laptops & Computers", "Electronics", "Laptops, desktops, and workstations"),
    ("Audio", "Electronics", "Headphones, earphones, speakers"),
    ("Cameras", "Electronics", "DSLR, mirrorless, and action cameras"),
    ("Fashion", None, "Clothing, footwear, and accessories"),
    ("Men's Clothing", "Fashion", "Shirts, trousers, and more for men"),
    ("Women's Clothing", "Fashion", "Dresses, tops, and more for women"),
    ("Footwear", "Fashion", "Shoes, sneakers, sandals for all"),
    ("Home & Kitchen", None, "Furniture, appliances, and kitchenware"),
    ("Appliances", "Home & Kitchen", "Refrigerators, washing machines, ACs"),
    ("Furniture", "Home & Kitchen", "Beds, sofas, tables, chairs"),
    ("Books", None, "Fiction, non-fiction, textbooks, and more"),
    ("Sports & Fitness", None, "Gym equipment, sportswear, outdoor gear"),
]

PRODUCTS = [
    # (sku, name, category, brand, price, discount_percent, stock, description, tags)
    (
        "SMRT-IPHONE15-128",
        "Apple iPhone 15 128GB",
        "Smartphones",
        "Apple",
        Decimal("79990"),
        Decimal("5"),
        150,
        "The iPhone 15 features a 6.1-inch Super Retina XDR display, A16 Bionic chip, and a 48MP main camera.",
        "iphone,apple,5g,ios",
    ),
    (
        "SMRT-SAMS-S24-256",
        "Samsung Galaxy S24 256GB",
        "Smartphones",
        "Samsung",
        Decimal("74999"),
        Decimal("10"),
        200,
        "Galaxy S24 with Snapdragon 8 Gen 3, 6.2-inch Dynamic AMOLED, and 50MP triple camera.",
        "samsung,android,5g,amoled",
    ),
    (
        "SMRT-PIXEL8-128",
        "Google Pixel 8 128GB",
        "Smartphones",
        "Google",
        Decimal("59999"),
        Decimal("8"),
        80,
        "Pixel 8 powered by Google Tensor G3 chip with 6.2-inch OLED and pro-grade camera system.",
        "pixel,google,android,tensor",
    ),
    (
        "TAB-IPADPRO-M4",
        "Apple iPad Pro M4 11-inch 256GB",
        "Tablets",
        "Apple",
        Decimal("109900"),
        Decimal("0"),
        60,
        "iPad Pro with M4 chip, Ultra Retina XDR display, and Apple Pencil Pro support.",
        "ipad,apple,tablet,m4",
    ),
    (
        "TAB-SAMS-TAB-S9",
        "Samsung Galaxy Tab S9 256GB",
        "Tablets",
        "Samsung",
        Decimal("87999"),
        Decimal("12"),
        45,
        "Galaxy Tab S9 with Snapdragon 8 Gen 2, 11-inch Dynamic AMOLED 2X, and S Pen included.",
        "samsung,tablet,android,s-pen",
    ),
    (
        "LAP-MBP-M3-PRO",
        "Apple MacBook Pro 14-inch M3 Pro",
        "Laptops & Computers",
        "Apple",
        Decimal("199900"),
        Decimal("3"),
        30,
        "MacBook Pro with M3 Pro chip, 18GB RAM, 512GB SSD, Liquid Retina XDR display.",
        "macbook,apple,laptop,m3",
    ),
    (
        "LAP-DELL-XPS15",
        "Dell XPS 15 9530 Intel Core i9",
        "Laptops & Computers",
        "Dell",
        Decimal("179990"),
        Decimal("7"),
        25,
        "Dell XPS 15 with 13th Gen Intel Core i9, 32GB RAM, 1TB SSD, and OLED display.",
        "dell,laptop,intel,oled,xps",
    ),
    (
        "AUD-SONY-WH1000XM5",
        "Sony WH-1000XM5 Wireless Headphones",
        "Audio",
        "Sony",
        Decimal("29990"),
        Decimal("20"),
        300,
        "Industry-leading noise canceling headphones with 30-hour battery life and Hi-Res Audio.",
        "sony,headphones,anc,wireless,bluetooth",
    ),
    (
        "AUD-BOSE-QC45",
        "Bose QuietComfort 45 Headphones",
        "Audio",
        "Bose",
        Decimal("24990"),
        Decimal("15"),
        180,
        "Premium noise-cancelling headphones with TriPort acoustic architecture and 24-hour battery.",
        "bose,headphones,anc,wireless",
    ),
    (
        "CAM-SONY-A7IV",
        "Sony Alpha A7 IV Full-Frame Mirrorless",
        "Cameras",
        "Sony",
        Decimal("254990"),
        Decimal("5"),
        20,
        "33MP BSI full-frame sensor, 10fps burst, 4K 60p video, 5-axis IBIS.",
        "sony,mirrorless,camera,fullframe",
    ),
    (
        "BOOK-CLEANCODE",
        "Clean Code by Robert C. Martin",
        "Books",
        "Pearson",
        Decimal("699"),
        Decimal("25"),
        500,
        "A Handbook of Agile Software Craftsmanship. Essential reading for every developer.",
        "programming,software,coding,agile",
    ),
    (
        "BOOK-SYSTEM-DESIGN",
        "System Design Interview - Alex Xu",
        "Books",
        "ByteByteGo",
        Decimal("2499"),
        Decimal("10"),
        350,
        "Insider's guide to system design interviews with real-world examples.",
        "system-design,interview,engineering",
    ),
    (
        "SPT-YOGA-MAT-PRO",
        "Lifelong Pro Yoga Mat 6mm",
        "Sports & Fitness",
        "Lifelong",
        Decimal("1299"),
        Decimal("30"),
        800,
        "Anti-skid EVA foam yoga mat with carrying strap. 183cm x 61cm, 6mm thick.",
        "yoga,fitness,exercise,mat",
    ),
    (
        "FASH-MENS-POLO-L",
        "Lacoste Classic Polo Shirt - Navy Blue L",
        "Men's Clothing",
        "Lacoste",
        Decimal("5990"),
        Decimal("0"),
        120,
        "Classic Lacoste polo in petit piqué cotton. Iconic crocodile emblem.",
        "polo,men,cotton,lacoste,premium",
    ),
    (
        "APP-LG-FRIDGE-500",
        "LG 500L Side-by-Side Refrigerator",
        "Appliances",
        "LG",
        Decimal("89990"),
        Decimal("18"),
        40,
        "LG 500L side-by-side refrigerator with InstaView Door-in-Door, Smart Inverter Compressor.",
        "lg,refrigerator,side-by-side,inverter",
    ),
]

ATTRIBUTES = {
    "SMRT-IPHONE15-128": [
        ("RAM", "6", "GB"),
        ("Storage", "128", "GB"),
        ("Display", "6.1", "inch"),
        ("Battery", "3349", "mAh"),
        ("OS", "iOS 17", ""),
    ],
    "SMRT-SAMS-S24-256": [
        ("RAM", "8", "GB"),
        ("Storage", "256", "GB"),
        ("Display", "6.2", "inch"),
        ("Battery", "4000", "mAh"),
        ("OS", "Android 14", ""),
    ],
    "LAP-MBP-M3-PRO": [
        ("RAM", "18", "GB"),
        ("Storage", "512", "GB"),
        ("Display", "14.2", "inch"),
        ("Chip", "Apple M3 Pro", ""),
        ("Battery Life", "18", "hours"),
    ],
    "AUD-SONY-WH1000XM5": [
        ("Driver Size", "30", "mm"),
        ("Frequency Response", "4-40000", "Hz"),
        ("Battery Life", "30", "hours"),
        ("Weight", "250", "g"),
        ("Connectivity", "Bluetooth 5.2", ""),
    ],
}


class Command(BaseCommand):
    help = "Seed the catalog database with sample categories and products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing catalog data..."))
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared."))

        self._seed_categories()
        self._seed_products()
        self.stdout.write(self.style.SUCCESS("✓ Catalog seeding complete."))

    def _seed_categories(self):
        self.stdout.write("Seeding categories...")
        cat_map = {}

        for name, parent_name, description in CATEGORIES:
            parent = cat_map.get(parent_name) if parent_name else None
            obj, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "parent": parent,
                    "is_active": True,
                },
            )
            cat_map[name] = obj
            if created:
                self.stdout.write(f"  + Category: {obj.full_path}")

        self.stdout.write(self.style.SUCCESS(f"  {len(CATEGORIES)} categories ready."))

    def _seed_products(self):
        self.stdout.write("Seeding products...")
        created_count = 0

        for sku, name, cat_name, brand, price, discount, stock, description, tags in PRODUCTS:
            try:
                category = Category.objects.get(name=cat_name)
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  Category '{cat_name}' not found, skipping {sku}."))
                continue

            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": category,
                    "brand": brand,
                    "price": price,
                    "discount_percent": discount,
                    "stock_quantity": stock,
                    "description": description,
                    "tags": tags,
                    "status": Product.Status.ACTIVE,
                    "is_featured": discount > 10,
                },
            )

            if created:
                # Add attributes if defined
                for attr_name, attr_val, attr_unit in ATTRIBUTES.get(sku, []):
                    ProductAttribute.objects.get_or_create(
                        product=product,
                        name=attr_name,
                        defaults={"value": attr_val, "unit": attr_unit},
                    )
                created_count += 1
                self.stdout.write(f"  + Product: {sku} — {name}")

        self.stdout.write(self.style.SUCCESS(f"  {created_count} products created."))
