"""
WSGI config for inventario_hospitalario project.

Expone Django y monta la API móvil FastAPI en /api/v1 (mismo puerto 8000).
Así funciona en producción sin cambiar OpenResty/nginx.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_hospitalario.settings')

django_application = get_wsgi_application()


def _build_application():
    enabled = os.environ.get('MOBILE_API_ENABLED', 'true').lower() not in ('false', '0')
    if not enabled:
        return django_application

    from a2wsgi import ASGIMiddleware

    from inventario_hospitalario.wsgi_mobile_mount import PathPrefixMiddleware
    from mobile_api.main import app as mobile_api_app

    mobile_wsgi = ASGIMiddleware(mobile_api_app)
    return PathPrefixMiddleware(django_application, '/api/v1', mobile_wsgi)


application = _build_application()
