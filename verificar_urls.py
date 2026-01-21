#!/usr/bin/env python
"""
Script para verificar que las URLs de disponibilidad están correctamente registradas.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_hospitalario.settings')
sys.path.insert(0, '/home/ubuntu/inventario_hospitalario')

django.setup()

from django.urls import get_resolver
from django.urls.exceptions import Resolver404

# Obtener el resolver
resolver = get_resolver()

# URLs a verificar
urls_a_verificar = [
    'inventario:reporte_disponibilidad_lotes',
    'inventario:exportar_disponibilidad_excel',
]

print("=" * 80)
print("VERIFICACIÓN DE URLs - REPORTE DE DISPONIBILIDAD")
print("=" * 80)

for url_name in urls_a_verificar:
    try:
        url = resolver.reverse(url_name)
        print(f"✓ {url_name:40} -> {url}")
    except Resolver404:
        print(f"✗ {url_name:40} -> NO ENCONTRADA")

print("\n" + "=" * 80)
print("VERIFICACIÓN DE IMPORTACIONES")
print("=" * 80)

try:
    from inventario.views_reporte_disponibilidad import reporte_disponibilidad_lotes, exportar_disponibilidad_excel
    print("✓ Vistas importadas correctamente")
    print(f"  - reporte_disponibilidad_lotes: {reporte_disponibilidad_lotes}")
    print(f"  - exportar_disponibilidad_excel: {exportar_disponibilidad_excel}")
except ImportError as e:
    print(f"✗ Error al importar vistas: {e}")

print("\n" + "=" * 80)
print("VERIFICACIÓN DE TEMPLATES")
print("=" * 80)

from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist

try:
    template = get_template('inventario/reportes/reporte_disponibilidad_lotes.html')
    print("✓ Template encontrado y cargado correctamente")
except TemplateDoesNotExist as e:
    print(f"✗ Template no encontrado: {e}")

print("\n" + "=" * 80)
print("VERIFICACIÓN DE MODELOS")
print("=" * 80)

try:
    from inventario.models import Lote, Producto, Institucion
    print("✓ Modelos importados correctamente")
    print(f"  - Lote: {Lote}")
    print(f"  - Producto: {Producto}")
    print(f"  - Institucion: {Institucion}")
except ImportError as e:
    print(f"✗ Error al importar modelos: {e}")

print("\n" + "=" * 80)
print("RESUMEN DE RUTAS DISPONIBLES")
print("=" * 80)

# Mostrar todas las rutas que contienen 'disponibilidad'
print("\nRutas que contienen 'disponibilidad':")
for pattern in resolver.url_patterns:
    if hasattr(pattern, 'pattern'):
        if 'disponibilidad' in str(pattern.pattern):
            print(f"  - {pattern.pattern}")

print("\nRutas que contienen 'reportes':")
for pattern in resolver.url_patterns:
    if hasattr(pattern, 'pattern'):
        if 'reportes' in str(pattern.pattern):
            print(f"  - {pattern.pattern}")

print("\n" + "=" * 80)
