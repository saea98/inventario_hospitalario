"""
Context Processor para pasar permisos al template
Ubicación: ./inventario/inventario_hospitalario/inventario/context_processors.py

Uso en settings.py:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [...],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    ...
                    'inventario.context_processors.permisos_usuario',  # ← AGREGAR ESTA LÍNEA
                ],
            },
        },
    ]
"""

def permisos_usuario(request):
    """
    Context processor que agrega los permisos del usuario al contexto
    
    Disponible en templates como:
        - {{ permisos.puede_crear_entrada }}
        - {{ permisos.puede_crear_salida }}
        - {{ permisos.es_administrador }}
        - {{ user.groups.all }} (para obtener todos los grupos)
    """
    
    permisos = {
        # ENTRADA AL ALMACÉN
        'puede_crear_entrada': False,
        'puede_ver_entrada': False,
        
        # PROVEEDURÍA
        'puede_crear_salida': False,
        'puede_ver_salida': False,
        
        # LOTES
        'puede_ver_lotes': False,
        'puede_editar_lotes': False,
        
        # MOVIMIENTOS
        'puede_ver_movimientos': False,
        
        # ROLES
        'es_almacenero': False,
        'es_responsable_proveeduria': False,
        'es_administrador': False,
    }
    
    if request.user.is_authenticated:
        # Obtener grupos del usuario
        grupos = request.user.groups.values_list('name', flat=True)
        
        # Verificar permisos específicos
        permisos['puede_crear_entrada'] = request.user.has_perm('inventario.add_lote')
        permisos['puede_ver_entrada'] = request.user.has_perm('inventario.view_lote')
        
        permisos['puede_crear_salida'] = request.user.has_perm('inventario.add_movimientoinventario')
        permisos['puede_ver_salida'] = request.user.has_perm('inventario.view_movimientoinventario')
        
        permisos['puede_ver_lotes'] = request.user.has_perm('inventario.view_lote')
        permisos['puede_editar_lotes'] = request.user.has_perm('inventario.change_lote')
        
        permisos['puede_ver_movimientos'] = request.user.has_perm('inventario.view_movimientoinventario')
        
        # Verificar roles (grupos)
        permisos['es_almacenero'] = 'Almacenero' in grupos
        permisos['es_responsable_proveeduria'] = 'Responsable Proveeduría' in grupos
        permisos['es_administrador'] = 'Administrador' in grupos or request.user.is_staff
    
    return {'permisos': permisos}
