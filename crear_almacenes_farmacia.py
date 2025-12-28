"""
Script para crear almacenes Farmacia para cada institución.
Ejecutar con: python manage.py shell < crear_almacenes_farmacia.py
"""

from inventario.models import Institucion, Almacen

# Obtener todas las instituciones excepto la de clave DFSSA004936
instituciones = Institucion.objects.exclude(clave='DFSSA004936')

almacenes_creados = 0
almacenes_existentes = 0

for institucion in instituciones:
    # Verificar si ya existe un almacén Farmacia para esta institución
    almacen_existente = Almacen.objects.filter(
        nombre='Farmacia',
        institucion=institucion
    ).exists()
    
    if almacen_existente:
        print(f"✓ Almacén Farmacia ya existe para {institucion.nombre}")
        almacenes_existentes += 1
    else:
        # Crear el almacén Farmacia
        almacen = Almacen.objects.create(
            nombre='Farmacia',
            codigo=f"FARM-{institucion.clave}",
            institucion=institucion,
            tipo='FARMACIA',
            estado=1
        )
        print(f"✓ Almacén Farmacia creado para {institucion.nombre}")
        almacenes_creados += 1

print(f"\n📊 Resumen:")
print(f"   Almacenes creados: {almacenes_creados}")
print(f"   Almacenes existentes: {almacenes_existentes}")
print(f"   Total: {almacenes_creados + almacenes_existentes}")
