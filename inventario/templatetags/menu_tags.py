"""
Template tags para renderizar menús dinámicos basados en MenuItemRol
Soporta jerarquía de menús con submenús
"""

from django import template
from inventario.models import MenuItemRol

register = template.Library()


@register.simple_tag
def obtener_items_menu_principales(user):
    """
    Obtiene los items del menú principal (sin padre) que el usuario puede ver
    basado en sus roles. Soporta jerarquía de menús.
    """
    
    if not user.is_authenticated:
        return []
    
    # Si es superusuario, mostrar todo
    if user.is_superuser:
        return MenuItemRol.objects.filter(
            activo=True, 
            menu_padre__isnull=True
        ).order_by('orden')
    
    # Obtener grupos del usuario
    user_groups = user.groups.all()
    
    # Obtener items que el usuario puede ver (solo items sin padre)
    items = MenuItemRol.objects.filter(
        activo=True,
        menu_padre__isnull=True,
        roles_permitidos__in=user_groups
    ).distinct().order_by('orden')
    
    return items


@register.simple_tag
def obtener_submenus(menu_padre, user):
    """
    Obtiene los submenús de un menú padre que el usuario puede ver
    """
    
    if not user.is_authenticated:
        return []
    
    # Si es superusuario, mostrar todo
    if user.is_superuser:
        return MenuItemRol.objects.filter(
            activo=True,
            menu_padre=menu_padre
        ).order_by('orden')
    
    # Obtener grupos del usuario
    user_groups = user.groups.all()
    
    # Obtener submenús que el usuario puede ver
    submenus = MenuItemRol.objects.filter(
        activo=True,
        menu_padre=menu_padre,
        roles_permitidos__in=user_groups
    ).distinct().order_by('orden')
    
    return submenus


@register.filter
def tiene_submenus(menu_item, user):
    """
    Verifica si un menú tiene submenús que el usuario puede ver
    """
    
    if not user.is_authenticated:
        return False
    
    # Si es superusuario
    if user.is_superuser:
        return MenuItemRol.objects.filter(
            activo=True,
            menu_padre=menu_item
        ).exists()
    
    # Obtener grupos del usuario
    user_groups = user.groups.all()
    
    # Verificar si hay submenús
    return MenuItemRol.objects.filter(
        activo=True,
        menu_padre=menu_item,
        roles_permitidos__in=user_groups
    ).distinct().exists()


@register.filter
def contar_submenus(menu_item, user):
    """
    Cuenta cuántos submenús tiene un menú que el usuario puede ver
    """
    
    if not user.is_authenticated:
        return 0
    
    # Si es superusuario
    if user.is_superuser:
        return MenuItemRol.objects.filter(
            activo=True,
            menu_padre=menu_item
        ).count()
    
    # Obtener grupos del usuario
    user_groups = user.groups.all()
    
    # Contar submenús
    return MenuItemRol.objects.filter(
        activo=True,
        menu_padre=menu_item,
        roles_permitidos__in=user_groups
    ).distinct().count()


@register.filter
def puede_acceder_url(usuario, url_name):
    """
    Filtro para verificar si un usuario puede acceder a una URL específica.
    """
    if usuario.is_superuser:
        return True
    
    try:
        menu_item = MenuItemRol.objects.get(url_name=url_name, activo=True)
        user_groups = usuario.groups.all()
        return menu_item.roles_permitidos.filter(id__in=user_groups).exists()
    except MenuItemRol.DoesNotExist:
        return False


@register.simple_tag
def obtener_roles_url(url_name):
    """
    Template tag que retorna los roles permitidos para una URL.
    """
    try:
        menu_item = MenuItemRol.objects.get(url_name=url_name, activo=True)
        return menu_item.roles_permitidos.all()
    except MenuItemRol.DoesNotExist:
        return []
