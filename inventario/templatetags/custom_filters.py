from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    return value - arg

@register.filter
def abs(value):
    """Devuelve el valor absoluto"""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value