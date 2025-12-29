#!/usr/bin/env python
"""
Script para agregar el item de menú de Historial de Conteos Físicos
Ejecutar: python manage.py shell < agregar_menu_conteos.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_hospitalario.settings')
django.setup()

from django.contrib.auth.models import Group
from inventario.models import MenuItemRol

# Obtener los grupos (roles) para los que será visible
try:
    supervisores = Group.objects.get(name='Supervisión')
    administradores = Group.objects.get(name='Administrador')
    almaceneros = Group.objects.get(name='Almacenero')
    gestores = Group.objects.get(name='Gestor de Inventario')
except Group.DoesNotExist as e:
    print(f"Error: No se encontró el grupo {e}")
    exit(1)

# Crear o actualizar el item de menú
menu_item, created = MenuItemRol.objects.update_or_create(
    url_name='historial_conteos',
    defaults={
        'menu_item': 'historial_conteos',
        'nombre_mostrado': 'Historial de Conteos',
        'icono': 'fas fa-history',
        'orden': 50,
        'activo': True,
        'es_submenu': False,
        'menu_padre': None,
    }
)

# Asignar los roles permitidos
menu_item.roles_permitidos.set([supervisores, administradores, almaceneros, gestores])

if created:
    print("✅ Item de menú 'Historial de Conteos' creado exitosamente")
else:
    print("✅ Item de menú 'Historial de Conteos' actualizado exitosamente")

print(f"   URL: historial_conteos")
print(f"   Roles permitidos: Supervisión, Administrador, Almacenero, Gestor de Inventario")
