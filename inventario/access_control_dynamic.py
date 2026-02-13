"""
Sistema de control de acceso dinámico basado en MenuItemRol
Sincroniza el acceso a vistas con la configuración de MenuItemRol
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import resolve
import logging

logger = logging.getLogger(__name__)


def requiere_acceso_menuitem(view_func):
    """
    Decorador que valida acceso a una vista contra MenuItemRol.
    
    Funciona de la siguiente manera:
    1. Obtiene el nombre de la URL actual
    2. Busca en MenuItemRol si existe configuración para esa URL
    3. Valida que el usuario tenga uno de los roles permitidos
    4. Si no hay configuración en MenuItemRol, permite acceso (para compatibilidad)
    
    IMPORTANTE: Usar SOLO este decorador, sin @login_required adicional.
    
    Uso:
        @requiere_acceso_menuitem
        def mi_vista(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from inventario.models import MenuItemRol
        
        # Verificar autenticación
        if not request.user.is_authenticated:
            logger.info(f"Usuario no autenticado intentando acceder a {view_func.__name__}")
            return redirect('login')
        
        # Si es superusuario, permitir acceso
        if request.user.is_superuser:
            logger.info(f"Superusuario {request.user.username} accediendo a {view_func.__name__}")
            return view_func(request, *args, **kwargs)
        
        # Obtener el nombre de la URL actual
        try:
            url_name = resolve(request.path_info).url_name
        except:
            url_name = None
        
        if not url_name:
            logger.warning(f"No se pudo resolver URL para {request.path_info}")
            return view_func(request, *args, **kwargs)
        
        # Buscar en MenuItemRol (first() evita MultipleObjectsReturned si hay duplicados)
        menu_item = MenuItemRol.objects.filter(url_name=url_name, activo=True).first()
        if menu_item:
            # Obtener roles del usuario
            user_groups = set(request.user.groups.values_list('name', flat=True))
            roles_permitidos = set(menu_item.roles_permitidos.values_list('name', flat=True))
            
            logger.debug(f"Usuario: {request.user.username}, Grupos: {user_groups}, Roles permitidos: {roles_permitidos}")
            
            # Validar acceso
            if not user_groups.intersection(roles_permitidos):
                mensaje = (
                    f"No tienes permiso para acceder a '{menu_item.nombre_mostrado}'. "
                    f"Se requiere uno de los siguientes roles: {', '.join(roles_permitidos)}"
                )
                logger.warning(f"Acceso denegado a {request.user.username} en {url_name}. "
                             f"Grupos: {user_groups}, Requeridos: {roles_permitidos}")
                messages.error(request, mensaje)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': mensaje}, status=403)
                
                return redirect('dashboard')
            
            logger.info(f"Acceso permitido a {request.user.username} en {url_name}")
        else:
            # Si no hay configuración en MenuItemRol, permitir acceso
            logger.debug(f"No hay configuración de MenuItemRol para {url_name}, permitiendo acceso")
            pass
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def requiere_rol_menuitem(*roles):
    """
    Decorador alternativo que valida roles específicos contra MenuItemRol.
    
    Si los roles especificados no coinciden con MenuItemRol, muestra una advertencia en logs.
    
    Uso:
        @requiere_rol_menuitem('Almacenero', 'Administrador')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from inventario.models import MenuItemRol
            
            # Verificar autenticación
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Si es superusuario, permitir acceso
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Obtener el nombre de la URL actual
            try:
                url_name = resolve(request.path_info).url_name
            except:
                url_name = None
            
            # Obtener roles del usuario
            user_groups = set(request.user.groups.values_list('name', flat=True))
            roles_requeridos = set(roles)
            
            # Validar contra roles especificados
            if not user_groups.intersection(roles_requeridos):
                mensaje = (
                    f"No tienes permiso para acceder a esta sección. "
                    f"Se requiere uno de los siguientes roles: {', '.join(roles)}"
                )
                logger.warning(f"Acceso denegado a {request.user.username}. "
                             f"Grupos: {user_groups}, Requeridos: {roles_requeridos}")
                messages.error(request, mensaje)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': mensaje}, status=403)
                
                return redirect('dashboard')
            
            # Verificar si hay configuración en MenuItemRol y si coincide
            if url_name:
                menu_item = MenuItemRol.objects.filter(url_name=url_name, activo=True).first()
                if menu_item:
                    roles_menuitem = set(menu_item.roles_permitidos.values_list('name', flat=True))
                    if roles_requeridos != roles_menuitem:
                        logger.warning(
                            f"DESAJUSTE en {url_name}: "
                            f"Decorador especifica {roles_requeridos}, "
                            f"MenuItemRol especifica {roles_menuitem}"
                        )
                else:
                    logger.debug(f"No hay configuración de MenuItemRol para {url_name}")
            
            logger.info(f"Acceso permitido a {request.user.username}")
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def obtener_roles_permitidos_url(url_name):
    """
    Obtiene los roles permitidos para una URL específica desde MenuItemRol.
    
    Uso:
        roles = obtener_roles_permitidos_url('lista_lotes')
        # Retorna: {'Almacenero', 'Administrador', ...}
    """
    from inventario.models import MenuItemRol
    
    menu_item = MenuItemRol.objects.filter(url_name=url_name, activo=True).first()
    if menu_item:
        return set(menu_item.roles_permitidos.values_list('name', flat=True))
    return set()


def usuario_puede_acceder_url(usuario, url_name):
    """
    Verifica si un usuario puede acceder a una URL específica según MenuItemRol.
    
    Uso:
        if usuario_puede_acceder_url(request.user, 'lista_lotes'):
            # Usuario puede acceder
    """
    if usuario.is_superuser:
        return True
    
    roles_permitidos = obtener_roles_permitidos_url(url_name)
    user_groups = set(usuario.groups.values_list('name', flat=True))
    
    return bool(user_groups.intersection(roles_permitidos))


def obtener_urls_accesibles_usuario(usuario):
    """
    Obtiene todas las URLs que un usuario puede acceder según MenuItemRol.
    
    Uso:
        urls = obtener_urls_accesibles_usuario(request.user)
        # Retorna: ['dashboard', 'lista_lotes', 'lista_productos', ...]
    """
    from inventario.models import MenuItemRol
    
    if usuario.is_superuser:
        return list(MenuItemRol.objects.filter(activo=True).values_list('url_name', flat=True))
    
    user_groups = set(usuario.groups.values_list('name', flat=True))
    
    # Obtener todos los items de menú donde el usuario tiene al menos un rol
    menu_items = MenuItemRol.objects.filter(
        activo=True,
        roles_permitidos__name__in=user_groups
    ).distinct().values_list('url_name', flat=True)
    
    return list(menu_items)
