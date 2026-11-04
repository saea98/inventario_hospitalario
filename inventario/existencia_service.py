"""
Existencia neta canónica del sistema.

Regla única (misma que reportes de inventario detallado / transferencias):

    fisico     = Lote.cantidad_disponible
    reservado  = suma LoteAsignado.cantidad_asignada con surtido=False
    neto       = max(0, fisico − reservado)

Cualquier API o reporte de disponibilidad debe pasar por aquí.
No usar el campo denormalizado Lote.cantidad_reservada como fuente de verdad.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from django.db.models import Case, F, IntegerField, OuterRef, QuerySet, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce

from .pedidos_models import LoteAsignado
from .propuesta_utils import totales_reserva_activa_por_lote_ids


def annotate_existencia_neta(queryset: QuerySet) -> QuerySet:
    """Anota `_fisico_lote`, `_sum_res` y `_inventario_disponible_neto` sobre un QS de Lote."""
    la_total = (
        LoteAsignado.objects.filter(lote_ubicacion__lote_id=OuterRef('pk'), surtido=False)
        .order_by()
        .values('lote_ubicacion__lote_id')
        .annotate(t=Sum('cantidad_asignada'))
        .values('t')[:1]
    )
    return (
        queryset.annotate(
            _sum_res=Coalesce(Subquery(la_total, output_field=IntegerField()), Value(0)),
        )
        .annotate(
            _fisico_lote=Coalesce(F('cantidad_disponible'), Value(0), output_field=IntegerField()),
        )
        .annotate(
            _inventario_disponible_neto=Case(
                When(_fisico_lote__lte=F('_sum_res'), then=Value(0)),
                default=F('_fisico_lote') - F('_sum_res'),
                output_field=IntegerField(),
            ),
        )
    )


def fisico_lote(lote) -> int:
    return int(getattr(lote, 'cantidad_disponible', 0) or 0)


def existencia_desglose_lote(lote, reservado: Optional[int] = None) -> Dict[str, int]:
    """Desglose fisico / reservado / neto para un Lote (objeto o anotado)."""
    fisico = fisico_lote(lote)
    if reservado is None:
        if hasattr(lote, '_sum_res'):
            reservado = int(lote._sum_res or 0)
        elif hasattr(lote, '_inventario_disponible_neto'):
            # reconstruir desde anotación si falta _sum_res
            neto = int(lote._inventario_disponible_neto or 0)
            reservado = max(0, fisico - neto)
        else:
            reservado = int(
                totales_reserva_activa_por_lote_ids([lote.id]).get(lote.id, 0)
            )
    reservado = int(reservado or 0)
    return {
        'fisico': fisico,
        'reservado': reservado,
        'disponible_neto': max(0, fisico - reservado),
    }


def desgloses_por_lote_ids(lote_ids: Iterable[int]) -> Dict[int, Dict[str, int]]:
    """Mapa lote_id → desglose; útil cuando ya se tienen ids."""
    ids = list({int(i) for i in lote_ids if i is not None})
    if not ids:
        return {}
    from .models import Lote

    reservas = totales_reserva_activa_por_lote_ids(ids)
    out = {}
    for lote in Lote.objects.filter(id__in=ids).only('id', 'cantidad_disponible'):
        out[lote.id] = existencia_desglose_lote(lote, reservado=reservas.get(lote.id, 0))
    return out


def variantes_clave_cnis(clave: str) -> List[str]:
    """Acepta clave con/sin sufijo .00 (mismo criterio que transferencias)."""
    c = (clave or '').strip().upper().replace(' ', '')
    if not c:
        return []
    out = [c]
    if c.endswith('.00'):
        out.append(c[:-3])
    else:
        out.append(c + '.00')
    return list(dict.fromkeys(out))
