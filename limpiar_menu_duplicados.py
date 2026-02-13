#!/usr/bin/env python
"""
Script para limpiar MenuItemRol duplicados
Ejecutar con: python manage.py shell < limpiar_menu_duplicados.py
"""

from django.db.models import Count
from inventario.models import MenuItemRol

# Buscar duplicados
print("Buscando MenuItemRol duplicados...")

# Agrupar por url_name y contar
duplicados = MenuItemRol.objects.values('url_name').annotate(count=Count('id')).filter(count__gt=1)

print(f"Se encontraron {duplicados.count()} URLs con duplicados")

for dup in duplicados:
    url_name = dup['url_name']
    items = MenuItemRol.objects.filter(url_name=url_name).order_by('id')
    print(f"\nURL: {url_name} - {items.count()} registros")
    
    for i, item in enumerate(items):
        print(f"  [{i}] ID: {item.id}, Nombre: {item.nombre_mostrado}")
    
    # Mantener el primero y eliminar los demás
    if items.count() > 1:
        primer_item = items.first()
        items_a_eliminar = items.exclude(id=primer_item.id)
        
        print(f"  Eliminando {items_a_eliminar.count()} registros duplicados...")
        items_a_eliminar.delete()
        print(f"  ✓ Hecho")

print("\n✅ Limpieza completada")
