from django import template

register = template.Library()

@register.filter
def calcular_diferencia(cantidad_nueva, cantidad_anterior):
    """Calcula la diferencia: cantidad_nueva - cantidad_anterior"""
    try:
        return int(cantidad_nueva) - int(cantidad_anterior)
    except (ValueError, TypeError):
        return 0
