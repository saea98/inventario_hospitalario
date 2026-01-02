#!/usr/bin/env python
"""
Script para agregar el Dashboard de Movimientos al menú
Ejecutar con: python manage.py shell < agregar_dashboard_menu.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_hospitalario.settings')
django.setup()

from inventario.models import MenuItemRol
from django.contrib.auth.models import Group

# Obtener el menú padre "Reportes"
try:
    reportes_menu = MenuItemRol.objects.get(menu_item='reportes_dashboard')
    print(f"✓ Menú padre 'Reportes' encontrado: {reportes_menu}")
except MenuItemRol.DoesNotExist:
    print("✗ Menú padre 'Reportes' no encontrado")
    reportes_menu = None

# Crear o actualizar el menú del Dashboard de Movimientos
dashboard_movimientos, created = MenuItemRol.objects.get_or_create(
    menu_item='dashboard_movimientos',
    defaults={
        'nombre_mostrado': 'Dashboard de Movimientos',
        'icono': 'fas fa-chart-line',
        'url_name': 'dashboard_movimientos',
        'orden': 1,
        'activo': True,
        'es_submenu': True,
        'menu_padre': reportes_menu,
    }
)

if created:
    print(f"✓ Dashboard de Movimientos creado: {dashboard_movimientos}")
else:
    print(f"✓ Dashboard de Movimientos ya existe: {dashboard_movimientos}")
    # Actualizar si es necesario
    dashboard_movimientos.nombre_mostrado = 'Dashboard de Movimientos'
    dashboard_movimientos.icono = 'fas fa-chart-line'
    dashboard_movimientos.url_name = 'dashboard_movimientos'
    dashboard_movimientos.es_submenu = True
    dashboard_movimientos.menu_padre = reportes_menu
    dashboard_movimientos.save()
    print("✓ Dashboard de Movimientos actualizado")

# Asignar a todos los roles
try:
    roles = Group.objects.all()
    dashboard_movimientos.roles_permitidos.set(roles)
    print(f"✓ Asignado a {roles.count()} roles")
except Exception as e:
    print(f"✗ Error al asignar roles: {e}")

print("\n✓ ¡Configuración completada!")
