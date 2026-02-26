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


@register.filter
def disponible_real(lote_ubicacion):
    """
    Cantidad realmente disponible en una ubicación de lote (cantidad - cantidad_reservada).
    Útil para mostrar y validar tope al asignar en propuestas.
    """
    if lote_ubicacion is None:
        return 0
    try:
        return max(0, lote_ubicacion.cantidad - getattr(lote_ubicacion, 'cantidad_reservada', 0))
    except (TypeError, AttributeError):
        return 0