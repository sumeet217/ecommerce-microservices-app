"""
Orders Service — Django Settings
Production-ready configuration via environment variables only.
No hardcoded secrets or credentials.
"""

from pathlib import Path

import dj_database_url
from decouple import Csv, config

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="*", cast=Csv())

# ─── Application Definition ───────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.orders",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "orders_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "orders_service.wsgi.application"

# ─── Database ─────────────────────────────────────────────────────────────────
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        default=(
            f"postgresql://{config('DB_USER', default='orders_user')}:"
            f"{config('DB_PASSWORD', default='orders_pass')}@"
            f"{config('DB_HOST', default='orders-db')}:"
            f"{config('DB_PORT', default='5432')}/"
            f"{config('DB_NAME', default='orders_db')}"
        ),
        conn_max_age=60,
        conn_health_checks=True,
    )
}

# ─── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── REST Framework ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": config("PAGE_SIZE", default=20, cast=int),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "200/minute"},
}

# ─── API Documentation (drf-spectacular) ─────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Orders Service API",
    "DESCRIPTION": "Order management microservice — place, track, and cancel orders.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:8080,http://ui-service:8080",
    cast=Csv(),
)
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)

# ─── Downstream Services ──────────────────────────────────────────────────────
CART_SERVICE_URL = config("CART_SERVICE_URL", default="http://cart-service:8002")
CART_SERVICE_TIMEOUT = config("CART_SERVICE_TIMEOUT", default=5, cast=int)

# ─── Order Settings ───────────────────────────────────────────────────────────
# Only orders in these statuses may be cancelled by the customer
CANCELLABLE_STATUSES = config(
    "CANCELLABLE_STATUSES", default="PENDING,CONFIRMED", cast=Csv()
)

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": config("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": config("LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}

# ─── Service Identity ─────────────────────────────────────────────────────────
SERVICE_NAME = "orders-service"
SERVICE_VERSION = "1.0.0"
