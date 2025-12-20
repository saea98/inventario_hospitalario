#!/usr/bin/env python
"""
Script para aplicar decoradores @requiere_rol() a las vistas principales
Este script identifica las vistas y aplica los decoradores necesarios
"""

import os
import re

# Mapeo de vistas a roles permitidos
VISTAS_ROLES = {
    # Administración
    'views.py': {
        'lista_instituciones': ['Administrador'],
        'lista_productos': ['Administrador'],
        'lista_proveedores': ['Administrador'],
        'lista_alcaldias': ['Administrador'],
        'lista_almacenes': ['Administrador'],
    },
    # Entrada al Almacén
    'views_entrada_salida.py': {
        'entrada_almacen_paso1': ['Almacenero', 'Supervisión', 'Control Calidad'],
        'entrada_almacen_paso2': ['Almacenero', 'Supervisión', 'Control Calidad'],
        'entrada_almacen_confirmacion': ['Almacenero', 'Supervisión', 'Control Calidad'],
    },
    # Lotes
    'views_lotes.py': {
        'lista_lotes': ['Almacenero', 'Supervisión', 'Control Calidad', 'Facturación', 'Gestor de Inventario'],
        'carga_lotes_excel': ['Almacenero', 'Supervisión'],
    },
    # Movimientos
    'views_movimientos.py': {
        'lista_movimientos': ['Supervisión', 'Gestor de Inventario'],
    },
}

def get_decorator_line(roles):
    """Genera la línea del decorador para los roles dados"""
    roles_str = ', '.join(f"'{rol}'" for rol in roles)
    return f"@requiere_rol({roles_str})\n"

def apply_decorators():
    """Aplica los decoradores a las vistas"""
    
    base_path = '/home/ubuntu/inventario_hospitalario/inventario'
    
    print("\n" + "="*70)
    print("🔐 APLICAR DECORADORES DE ROLES A VISTAS")
    print("="*70 + "\n")
    
    for archivo, vistas in VISTAS_ROLES.items():
        filepath = os.path.join(base_path, archivo)
        
        if not os.path.exists(filepath):
            print(f"⚠️  Archivo no encontrado: {archivo}")
            continue
        
        print(f"\n📄 Procesando: {archivo}")
        print("-" * 70)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        modificado = False
        
        for vista, roles in vistas.items():
            # Buscar la definición de la función
            patron = rf"(^def {vista}\()"
            
            if re.search(patron, contenido, re.MULTILINE):
                # Verificar si ya tiene el decorador
                decorador_patron = rf"@requiere_rol.*\ndef {vista}\("
                
                if not re.search(decorador_patron, contenido, re.MULTILINE | re.DOTALL):
                    # Agregar el decorador
                    decorator_line = get_decorator_line(roles)
                    contenido = re.sub(
                        patron,
                        f"{decorator_line}def {vista}(",
                        contenido,
                        flags=re.MULTILINE
                    )
                    
                    roles_str = ', '.join(roles)
                    print(f"  ✅ {vista}: {roles_str}")
                    modificado = True
                else:
                    print(f"  ℹ️  {vista}: Ya tiene decorador")
            else:
                print(f"  ❌ {vista}: No encontrada")
        
        if modificado:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(contenido)
            print(f"\n  📝 {archivo} actualizado")
    
    print("\n" + "="*70)
    print("✨ Decoradores aplicados correctamente")
    print("="*70 + "\n")

if __name__ == '__main__':
    apply_decorators()
