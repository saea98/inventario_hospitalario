#!/usr/bin/env python
"""
Script para agregar la opción de Administración de Roles al menú
Ejecutar: python manage.py shell < agregar_admin_roles_menu.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_hospitalario.settings')
django.setup()

from django.contrib.auth.models import Group
from inventario.models import MenuItemRol

print("🔧 Agregando opción 'Administración de Roles' al menú...\n")

# Crear la opción de administración de roles si no existe
menu_item, created = MenuItemRol.objects.get_or_create(
    menu_item='admin_roles',
    defaults={
        'nombre_mostrado': 'Administración de Roles',
        'icono': 'fas fa-user-shield',
        'url_name': 'admin_roles:dashboard',
        'orden': 5,
        'activo': True,
        'es_submenu': False,
    }
)

if created:
    print("✅ Opción 'Administración de Roles' CREADA")
else:
    print("ℹ️  Opción 'Administración de Roles' ya existe")

# Obtener el rol Administrador
try:
    admin_role = Group.objects.get(name='Administrador')
    menu_item.roles_permitidos.add(admin_role)
    print("✅ Asignada al rol: Administrador")
except Group.DoesNotExist:
    print("❌ Rol 'Administrador' no encontrado")

print("\n✨ Opción agregada al menú correctamente")
print("📍 Acceso: /admin-roles/")
