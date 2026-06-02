"""
WSGI config for the Catalog Service.
Exposes the module-level WSGI callable as a variable named ``application``.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "catalog_service.settings")

application = get_wsgi_application()
