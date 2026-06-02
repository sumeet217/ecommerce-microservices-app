"""
UI Service — Django Settings
Stateless Django app that renders templates by calling backend APIs.
No database, no ORM, no migrations.
"""

from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="*", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="http://localhost,http://127.0.0.1,http://nginx", cast=Csv())
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False

# ─── Application Definition ───────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "django.contrib.sessions",
    "apps.store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ui_service.urls"
WSGI_APPLICATION = "ui_service.wsgi.application"

# ─── No database ──────────────────────────────────────────────────────────────
DATABASES = {}

# ─── Sessions (cookie-based, no DB required) ─────────────────────────────────
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_NAME = "retail_session"
SESSION_COOKIE_AGE = 7 * 24 * 3600  # 7 days
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# ─── Messages ─────────────────────────────────────────────────────────────────
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

# ─── Templates ────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "apps.store.context_processors.cart_context",
            ],
        },
    },
]

# ─── Static Files ─────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ─── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Backend Service URLs ─────────────────────────────────────────────────────
CATALOG_SERVICE_URL = config("CATALOG_SERVICE_URL", default="http://catalog-service:8001")
CART_SERVICE_URL    = config("CART_SERVICE_URL",    default="http://cart-service:8002")
ORDERS_SERVICE_URL  = config("ORDERS_SERVICE_URL",  default="http://orders-service:8003")
SERVICE_TIMEOUT     = config("SERVICE_TIMEOUT", default=8, cast=int)

# ─── Pagination ───────────────────────────────────────────────────────────────
PRODUCTS_PER_PAGE = config("PRODUCTS_PER_PAGE", default=12, cast=int)

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": config("LOG_LEVEL", default="INFO")},
}

SERVICE_NAME = "ui-service"
SERVICE_VERSION = "1.0.0"
