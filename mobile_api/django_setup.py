"""Inicializa Django para usar ORM desde FastAPI."""

import os
import sys


def setup_django():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_hospitalario.settings')
    import django

    django.setup()
