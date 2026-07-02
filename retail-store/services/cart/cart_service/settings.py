"""
Cart Service — Django Settings
All config via environment variables. Redis is the primary data store.
"""

from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="*", cast=Csv())

# ─── Application Definition ───────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "apps.cart",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "cart_service.urls"
WSGI_APPLICATION = "cart_service.wsgi.application"

# ─── No relational database needed ────────────────────────────────────────────
# Cart data lives entirely in Redis.
DATABASES = {}

# ─── Redis ────────────────────────────────────────────────────────────────────
REDIS_URL = config("REDIS_URL", default="redis://redis:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 50,
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
        },
        "KEY_PREFIX": "cart",
        "TIMEOUT": None,  # Cart keys manage their own TTL
    }
}

# ─── Cart Settings ────────────────────────────────────────────────────────────
CART_TTL_SECONDS = config("CART_TTL_SECONDS", default=60 * 60 * 24 * 7, cast=int)  # 7 days
CART_MAX_ITEMS = config("CART_MAX_ITEMS", default=50, cast=int)
CART_MAX_QUANTITY_PER_ITEM = config("CART_MAX_QUANTITY_PER_ITEM", default=99, cast=int)

# ─── Downstream Services ──────────────────────────────────────────────────────
CATALOG_SERVICE_URL = config("CATALOG_SERVICE_URL", default="http://catalog-service:8001")
CATALOG_SERVICE_TIMEOUT = config("CATALOG_SERVICE_TIMEOUT", default=5, cast=int)

# ─── REST Framework ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "200/minute"},
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Cart Service API",
    "DESCRIPTION": "Redis-backed shopping cart microservice.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:8080,http://ui-service:8080",
    cast=Csv(),
)
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}},
    "root": {"handlers": ["console"], "level": config("LOG_LEVEL", default="INFO")},
}

SERVICE_NAME = "cart-service"
SERVICE_VERSION = "1.0.0"
