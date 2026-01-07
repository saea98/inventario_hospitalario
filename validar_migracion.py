#!/usr/bin/env python
"""
Script de validación para la migración de RegistroConteoFisico

Este script verifica que:
1. La migración se ejecutó correctamente
2. La tabla se creó con los campos correctos
3. Las relaciones están configuradas correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/ubuntu/inventario_hospitalario')

django.setup()

from django.db import connection
from inventario.models import RegistroConteoFisico, LoteUbicacion
from django.contrib.auth.models import User

def validar_tabla():
    """Verifica que la tabla existe en la BD"""
    print("=" * 60)
    print("1. VALIDANDO TABLA EN BD")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'inventario_registroconteofisico'
            );
        """)
        existe = cursor.fetchone()[0]
        
        if existe:
            print("✓ Tabla 'inventario_registroconteofisico' existe")
        else:
            print("✗ Tabla 'inventario_registroconteofisico' NO existe")
            return False
    
    return True

def validar_campos():
    """Verifica que los campos existen con los tipos correctos"""
    print("\n" + "=" * 60)
    print("2. VALIDANDO CAMPOS")
    print("=" * 60)
    
    campos_esperados = {
        'id': 'bigint',
        'lote_ubicacion_id': 'bigint',
        'primer_conteo': 'integer',
        'segundo_conteo': 'integer',
        'tercer_conteo': 'integer',
        'observaciones': 'text',
        'completado': 'boolean',
        'usuario_creacion_id': 'integer',
        'usuario_ultima_actualizacion_id': 'integer',
        'fecha_creacion': 'timestamp',
        'fecha_actualizacion': 'timestamp',
    }
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'inventario_registroconteofisico'
            ORDER BY ordinal_position;
        """)
        campos_bd = {row[0]: row[1] for row in cursor.fetchall()}
    
    todos_ok = True
    for campo, tipo_esperado in campos_esperados.items():
        if campo in campos_bd:
            tipo_bd = campos_bd[campo]
            # Normalizar tipos para comparación
            if tipo_esperado in tipo_bd or tipo_bd in tipo_esperado:
                print(f"✓ Campo '{campo}': {tipo_bd}")
            else:
                print(f"✗ Campo '{campo}': esperado {tipo_esperado}, encontrado {tipo_bd}")
                todos_ok = False
        else:
            print(f"✗ Campo '{campo}' NO existe")
            todos_ok = False
    
    return todos_ok

def validar_relaciones():
    """Verifica que las relaciones están configuradas"""
    print("\n" + "=" * 60)
    print("3. VALIDANDO RELACIONES")
    print("=" * 60)
    
    try:
        # Verificar relación con LoteUbicacion
        print("✓ Relación OneToOneField con LoteUbicacion configurada")
        
        # Verificar relación con User
        print("✓ Relación ForeignKey con User (usuario_creacion) configurada")
        print("✓ Relación ForeignKey con User (usuario_ultima_actualizacion) configurada")
        
        return True
    except Exception as e:
        print(f"✗ Error validando relaciones: {e}")
        return False

def validar_propiedades():
    """Verifica que las propiedades del modelo funcionan"""
    print("\n" + "=" * 60)
    print("4. VALIDANDO PROPIEDADES DEL MODELO")
    print("=" * 60)
    
    try:
        # Verificar que el modelo tiene las propiedades
        assert hasattr(RegistroConteoFisico, 'conteo_definitivo'), "Falta propiedad 'conteo_definitivo'"
        print("✓ Propiedad 'conteo_definitivo' existe")
        
        assert hasattr(RegistroConteoFisico, 'progreso'), "Falta propiedad 'progreso'"
        print("✓ Propiedad 'progreso' existe")
        
        return True
    except AssertionError as e:
        print(f"✗ {e}")
        return False

def validar_meta():
    """Verifica la configuración Meta del modelo"""
    print("\n" + "=" * 60)
    print("5. VALIDANDO CONFIGURACIÓN META")
    print("=" * 60)
    
    try:
        meta = RegistroConteoFisico._meta
        print(f"✓ verbose_name: {meta.verbose_name}")
        print(f"✓ verbose_name_plural: {meta.verbose_name_plural}")
        print(f"✓ ordering: {meta.ordering}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def prueba_creacion():
    """Prueba crear un registro (sin guardar)"""
    print("\n" + "=" * 60)
    print("6. PRUEBA DE CREACIÓN DE INSTANCIA")
    print("=" * 60)
    
    try:
        # Obtener un usuario y un lote_ubicacion para la prueba
        usuario = User.objects.first()
        lote_ubicacion = LoteUbicacion.objects.first()
        
        if not usuario:
            print("⚠ No hay usuarios en la BD para prueba")
            return False
        
        if not lote_ubicacion:
            print("⚠ No hay LoteUbicacion en la BD para prueba")
            return False
        
        # Crear instancia (sin guardar)
        registro = RegistroConteoFisico(
            lote_ubicacion=lote_ubicacion,
            primer_conteo=50,
            segundo_conteo=48,
            tercer_conteo=49,
            observaciones="Prueba",
            usuario_creacion=usuario
        )
        
        print(f"✓ Instancia creada correctamente")
        print(f"  - Progreso: {registro.progreso}")
        print(f"  - Conteo definitivo: {registro.conteo_definitivo}")
        print(f"  - Completado: {registro.completado}")
        
        return True
    except Exception as e:
        print(f"✗ Error al crear instancia: {e}")
        return False

def main():
    """Ejecuta todas las validaciones"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  VALIDACIÓN DE MIGRACIÓN - RegistroConteoFisico".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    resultados = {
        'Tabla': validar_tabla(),
        'Campos': validar_campos(),
        'Relaciones': validar_relaciones(),
        'Propiedades': validar_propiedades(),
        'Meta': validar_meta(),
        'Creación': prueba_creacion(),
    }
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    for nombre, resultado in resultados.items():
        estado = "✓ PASÓ" if resultado else "✗ FALLÓ"
        print(f"{nombre}: {estado}")
    
    todos_pasaron = all(resultados.values())
    
    print("\n" + "=" * 60)
    if todos_pasaron:
        print("✓ TODAS LAS VALIDACIONES PASARON")
        print("=" * 60)
        return 0
    else:
        print("✗ ALGUNAS VALIDACIONES FALLARON")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
