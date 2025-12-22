# inventario/templatetags/role_filters.py
from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_role')
def has_role(user, role_name):
    """Verifica si el usuario pertenece a un grupo/rol específico"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=role_name).exists()

@register.filter(name='has_any_role')
def has_any_role(user, roles):
    """Verifica si el usuario tiene cualquiera de los roles especificados"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role_list = [r.strip() for r in roles.split(',')]
    return user.groups.filter(name__in=role_list).exists()
