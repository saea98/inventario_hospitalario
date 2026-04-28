from django import template
from django.db.models import Sum

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
    Cantidad realmente disponible en una ubicación de lote:
    cantidad física - reserva activa real (suma de LoteAsignado con surtido=False).

    Se evita usar `cantidad_reservada` persistida porque puede estar desfasada.
    """
    if lote_ubicacion is None:
        return 0
    try:
        from inventario.pedidos_models import LoteAsignado

        reservada_activa = (
            LoteAsignado.objects.filter(lote_ubicacion=lote_ubicacion, surtido=False)
            .aggregate(total=Sum('cantidad_asignada'))
            .get('total')
            or 0
        )
        return max(0, int(lote_ubicacion.cantidad or 0) - int(reservada_activa))
    except (TypeError, AttributeError):
        return 0