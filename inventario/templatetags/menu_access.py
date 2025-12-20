"""
Template tags para verificar acceso a opciones de menú basado en roles
"""

from django import template
from django.core.cache import cache
from inventario.models import MenuItemRol

register = template.Library()

@register.filter
def puede_ver_menu(user, menu_item_key):
    """
    Verifica si un usuario puede ver una opción de menú específica
    Uso: {% if user|puede_ver_menu:"dashboard" %}...{% endif %}
    """
    if user.is_superuser:
        return True
    
    if not user.is_authenticated:
        return False
    
    # Intentar obtener del caché primero
    cache_key = f"menu_access_{user.id}_{menu_item_key}"
    resultado = cache.get(cache_key)
    
    if resultado is not None:
        return resultado
    
    try:
        menu_item = MenuItemRol.objects.get(menu_item=menu_item_key)
        
        # Verificar si está activo
        if not menu_item.activo:
            cache.set(cache_key, False, 3600)
            return False
        
        # Verificar si el usuario tiene alguno de los roles permitidos
        user_roles = user.groups.all()
        tiene_acceso = menu_item.roles_permitidos.filter(id__in=user_roles).exists()
        
        # Cachear el resultado por 1 hora
        cache.set(cache_key, tiene_acceso, 3600)
        
        return tiene_acceso
    except MenuItemRol.DoesNotExist:
        # Si no existe el item de menú, permitir acceso por defecto
        cache.set(cache_key, True, 3600)
        return True

@register.filter
def usuario_tiene_rol(user, rol_name):
    """
    Verifica si un usuario tiene un rol específico
    Uso: {% if user|usuario_tiene_rol:"Administrador" %}...{% endif %}
    """
    if user.is_superuser:
        return True
    
    if not user.is_authenticated:
        return False
    
    return user.groups.filter(name=rol_name).exists()

@register.filter
def usuario_tiene_alguno_de_estos_roles(user, roles_str):
    """
    Verifica si un usuario tiene alguno de los roles especificados
    Uso: {% if user|usuario_tiene_alguno_de_estos_roles:"Admin,Editor,Viewer" %}...{% endif %}
    """
    if user.is_superuser:
        return True
    
    if not user.is_authenticated:
        return False
    
    roles = [rol.strip() for rol in roles_str.split(',')]
    return user.groups.filter(name__in=roles).exists()

@register.filter
def usuario_tiene_todos_estos_roles(user, roles_str):
    """
    Verifica si un usuario tiene todos los roles especificados
    Uso: {% if user|usuario_tiene_todos_estos_roles:"Admin,Editor" %}...{% endif %}
    """
    if not user.is_authenticated:
        return False
    
    roles = [rol.strip() for rol in roles_str.split(',')]
    user_roles = user.groups.values_list('name', flat=True)
    
    return all(rol in user_roles for rol in roles)

@register.simple_tag
def obtener_roles_usuario(user):
    """
    Obtiene una lista de los roles del usuario
    Uso: {% obtener_roles_usuario user as roles %}
    """
    if not user.is_authenticated:
        return []
    
    return list(user.groups.values_list('name', flat=True))

@register.simple_tag
def obtener_opciones_menu_visibles(user):
    """
    Obtiene todas las opciones de menú visibles para el usuario
    Uso: {% obtener_opciones_menu_visibles user as menu_items %}
    """
    if not user.is_authenticated:
        return MenuItemRol.objects.none()
    
    if user.is_superuser:
        return MenuItemRol.objects.filter(activo=True).order_by('orden')
    
    # Obtener opciones de menú para los roles del usuario
    return MenuItemRol.objects.filter(
        activo=True,
        roles_permitidos__in=user.groups.all()
    ).distinct().order_by('orden')
