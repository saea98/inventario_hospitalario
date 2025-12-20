"""
Template tags para renderizar el menú dinámicamente según los roles del usuario
"""

from django import template
from inventario.models import MenuItemRol

register = template.Library()


@register.inclusion_tag('menu/menu_dinamico.html')
def menu_dinamico(usuario):
    """
    Template tag que renderiza el menú dinámicamente según los roles del usuario.
    
    Uso en template:
    {% load menu_tags %}
    {% menu_dinamico user %}
    """
    
    # Si el usuario es superusuario, mostrar todos los items
    if usuario.is_superuser:
        items = MenuItemRol.objects.filter(activo=True).order_by('orden')
    else:
        # Obtener los roles del usuario
        roles_usuario = usuario.groups.all()
        
        # Obtener los items de menú que el usuario puede ver
        items = MenuItemRol.objects.filter(
            activo=True,
            roles_permitidos__in=roles_usuario
        ).distinct().order_by('orden')
    
    # Separar items principales de submenús
    items_principales = items.filter(es_submenu=False)
    
    return {
        'items': items_principales,
        'usuario': usuario,
    }


@register.filter
def puede_ver_menu(usuario, menu_item_id):
    """
    Filtro para verificar si un usuario puede ver un item de menú específico.
    
    Uso en template:
    {% if user|puede_ver_menu:menu_item.id %}
        <!-- mostrar item -->
    {% endif %}
    """
    try:
        menu_item = MenuItemRol.objects.get(id=menu_item_id)
        return menu_item.puede_ver_usuario(usuario)
    except MenuItemRol.DoesNotExist:
        return False


@register.simple_tag
def obtener_items_menu(usuario):
    """
    Template tag que retorna los items de menú que el usuario puede ver.
    
    Uso en template:
    {% obtener_items_menu user as menu_items %}
    {% for item in menu_items %}
        ...
    {% endfor %}
    """
    
    if usuario.is_superuser:
        return MenuItemRol.objects.filter(activo=True).order_by('orden')
    else:
        roles_usuario = usuario.groups.all()
        return MenuItemRol.objects.filter(
            activo=True,
            roles_permitidos__in=roles_usuario
        ).distinct().order_by('orden')
