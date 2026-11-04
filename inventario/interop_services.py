"""
Consultas de lectura para la API de interoperabilidad.
Siempre exponen fisico / reservado / disponible_neto vía existencia_service.

Política interop: nunca devolver lotes caducados (estado Caducado o fecha vencida).
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from django.db.models import Q, QuerySet

from .existencia_service import (
    annotate_existencia_neta,
    existencia_desglose_lote,
    variantes_clave_cnis,
)
from .models import Almacen, Lote, Producto

ESTADO_CADUCADO = 6


def _excluir_caducados(qs: QuerySet) -> QuerySet:
    """
    Quita ruido de caducados: estado=6 o fecha_caducidad < hoy.
    (Si no hay fecha de caducidad, solo aplica el estado.)
    """
    hoy = date.today()
    return qs.exclude(estado=ESTADO_CADUCADO).exclude(
        fecha_caducidad__isnull=False,
        fecha_caducidad__lt=hoy,
    )


def _filtro_institucion(qs, institucion_id: Optional[int]):
    if institucion_id:
        return qs.filter(institucion_id=institucion_id)
    return qs


def _aplicar_filtros_lote(
    qs: QuerySet,
    *,
    clave_cnis: Optional[str] = None,
    numero_lote: Optional[str] = None,
    lote_id: Optional[int] = None,
    uuid: Optional[str] = None,
    almacen_id: Optional[int] = None,
    institucion_id: Optional[int] = None,
) -> QuerySet:
    qs = _filtro_institucion(qs, institucion_id)
    qs = _excluir_caducados(qs)
    if lote_id:
        qs = qs.filter(pk=lote_id)
    if uuid:
        qs = qs.filter(uuid=uuid.strip())
    if almacen_id:
        qs = qs.filter(almacen_id=almacen_id)
    if clave_cnis:
        variantes = variantes_clave_cnis(clave_cnis)
        q = Q()
        for v in variantes:
            q |= Q(producto__clave_cnis__iexact=v)
        qs = qs.filter(q)
    if numero_lote:
        term = numero_lote.strip()
        # exacto si parece completo; si no, contiene
        if len(term) >= 3:
            qs = qs.filter(numero_lote__icontains=term)
        else:
            qs = qs.filter(numero_lote__iexact=term)
    return qs


def _lote_payload(lote) -> Dict[str, Any]:
    desglose = existencia_desglose_lote(lote)
    prod = lote.producto
    return {
        'lote_id': lote.id,
        'uuid': str(lote.uuid),
        'numero_lote': lote.numero_lote,
        'clave_cnis': prod.clave_cnis if prod else None,
        'descripcion': prod.descripcion if prod else None,
        'estado': lote.estado,
        'estado_label': lote.get_estado_display() if hasattr(lote, 'get_estado_display') else str(lote.estado),
        'fecha_caducidad': lote.fecha_caducidad.isoformat() if lote.fecha_caducidad else None,
        'fecha_recepcion': lote.fecha_recepcion.isoformat() if lote.fecha_recepcion else None,
        'almacen_id': lote.almacen_id,
        'almacen': lote.almacen.nombre if lote.almacen_id and lote.almacen else None,
        'institucion_id': lote.institucion_id,
        'institucion': lote.institucion.denominacion if lote.institucion_id and lote.institucion else None,
        'existencia': desglose,
    }


def consultar_existencias(
    *,
    clave_cnis: Optional[str] = None,
    numero_lote: Optional[str] = None,
    lote_id: Optional[int] = None,
    uuid: Optional[str] = None,
    almacen_id: Optional[int] = None,
    institucion_id: Optional[int] = None,
    solo_con_neto: bool = True,
    limite_lotes: int = 500,
) -> Dict[str, Any]:
    """
    Existencias por clave (agregado) y detalle de lotes.
    Siempre excluye caducados. Combina filtros (p.ej. clave_cnis + numero_lote).
    """
    qs = Lote.objects.select_related('producto', 'almacen', 'institucion')
    qs = _aplicar_filtros_lote(
        qs,
        clave_cnis=clave_cnis,
        numero_lote=numero_lote,
        lote_id=lote_id,
        uuid=uuid,
        almacen_id=almacen_id,
        institucion_id=institucion_id,
    )

    qs = annotate_existencia_neta(qs)
    if solo_con_neto:
        qs = qs.filter(_inventario_disponible_neto__gt=0)
    else:
        qs = qs.filter(cantidad_disponible__gt=0)

    qs = qs.order_by('producto__clave_cnis', 'fecha_caducidad', 'numero_lote')
    lotes = list(qs[: max(1, min(limite_lotes, 2000))])

    por_clave: Dict[str, Dict[str, Any]] = {}
    detalle = []
    for lote in lotes:
        payload = _lote_payload(lote)
        detalle.append(payload)
        clave = payload['clave_cnis'] or ''
        agg = por_clave.setdefault(
            clave,
            {
                'clave_cnis': clave,
                'descripcion': payload['descripcion'],
                'fisico': 0,
                'reservado': 0,
                'disponible_neto': 0,
                'lotes': 0,
            },
        )
        e = payload['existencia']
        agg['fisico'] += e['fisico']
        agg['reservado'] += e['reservado']
        agg['disponible_neto'] += e['disponible_neto']
        agg['lotes'] += 1

    return {
        'regla': (
            'disponible_neto = max(0, cantidad_disponible − suma(LoteAsignado.cantidad_asignada '
            'donde surtido=False); caducados excluidos'
        ),
        'filtros': {
            'clave_cnis': clave_cnis,
            'numero_lote': numero_lote,
            'lote_id': lote_id,
            'uuid': uuid,
            'almacen_id': almacen_id,
            'institucion_id': institucion_id,
            'solo_con_neto': solo_con_neto,
            'limite_lotes': limite_lotes,
            'excluye_caducados': True,
        },
        'totales_por_clave': list(por_clave.values()),
        'lotes': detalle,
        'count_lotes': len(detalle),
        'truncated': len(detalle) >= limite_lotes,
    }


def obtener_lote(
    lote_id: int,
    institucion_id: Optional[int] = None,
    *,
    numero_lote: Optional[str] = None,
    clave_cnis: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Detalle de lote; None si no existe, no aplica filtros o está caducado."""
    qs = Lote.objects.select_related('producto', 'almacen', 'institucion').filter(pk=lote_id)
    qs = _aplicar_filtros_lote(
        qs,
        clave_cnis=clave_cnis,
        numero_lote=numero_lote,
        institucion_id=institucion_id,
    )
    lote = annotate_existencia_neta(qs).first()
    if not lote:
        return None
    return _lote_payload(lote)


def buscar_lotes(
    *,
    clave_cnis: Optional[str] = None,
    numero_lote: Optional[str] = None,
    almacen_id: Optional[int] = None,
    institucion_id: Optional[int] = None,
    solo_con_neto: bool = True,
    limite: int = 100,
) -> Dict[str, Any]:
    """Búsqueda directa de lotes (p.ej. CNIS + número de lote). Sin caducados."""
    return consultar_existencias(
        clave_cnis=clave_cnis,
        numero_lote=numero_lote,
        almacen_id=almacen_id,
        institucion_id=institucion_id,
        solo_con_neto=solo_con_neto,
        limite_lotes=limite,
    )


def listar_almacenes(
    *,
    institucion_id: Optional[int] = None,
    q: Optional[str] = None,
    solo_activos: bool = True,
) -> Dict[str, Any]:
    """Catálogo de almacenes para armar filtros en existencias/lotes."""
    qs = Almacen.objects.select_related('institucion').order_by('nombre')
    if solo_activos:
        qs = qs.filter(activo=True)
    if institucion_id:
        qs = qs.filter(institucion_id=institucion_id)
    if q:
        term = q.strip()
        qs = qs.filter(
            Q(nombre__icontains=term)
            | Q(codigo__icontains=term)
            | Q(institucion__denominacion__icontains=term)
            | Q(institucion__clue__icontains=term)
        )
    results = [
        {
            'id': a.id,
            'codigo': a.codigo,
            'nombre': a.nombre,
            'activo': a.activo,
            'institucion_id': a.institucion_id,
            'institucion': a.institucion.denominacion if a.institucion_id else None,
            'clue': a.institucion.clue if a.institucion_id else None,
        }
        for a in qs[:500]
    ]
    return {
        'count': len(results),
        'filtros': {
            'institucion_id': institucion_id,
            'q': q,
            'solo_activos': solo_activos,
        },
        'results': results,
    }


def buscar_productos(
    *,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Dict[str, Any]:
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    qs = Producto.objects.filter(activo=True).order_by('clave_cnis')
    if q:
        term = q.strip()
        qs = qs.filter(Q(clave_cnis__icontains=term) | Q(descripcion__icontains=term))
    total = qs.count()
    start = (page - 1) * page_size
    items = [
        {
            'id': p.id,
            'clave_cnis': p.clave_cnis,
            'descripcion': p.descripcion,
            'unidad_medida': p.unidad_medida,
            'clave_saica': p.clave_saica,
            'activo': p.activo,
        }
        for p in qs[start : start + page_size]
    ]
    return {
        'count': total,
        'page': page,
        'page_size': page_size,
        'results': items,
    }


def resumen_existencia_clave(
    clave_cnis: str,
    *,
    numero_lote: Optional[str] = None,
    institucion_id: Optional[int] = None,
    almacen_id: Optional[int] = None,
) -> Dict[str, Any]:
    data = consultar_existencias(
        clave_cnis=clave_cnis,
        numero_lote=numero_lote,
        institucion_id=institucion_id,
        almacen_id=almacen_id,
        solo_con_neto=True,
        limite_lotes=2000,
    )
    totales = data['totales_por_clave'][0] if data['totales_por_clave'] else {
        'clave_cnis': clave_cnis.strip().upper(),
        'descripcion': None,
        'fisico': 0,
        'reservado': 0,
        'disponible_neto': 0,
        'lotes': 0,
    }
    return {
        'regla': data['regla'],
        'clave_cnis': clave_cnis,
        'numero_lote': numero_lote,
        'resumen': totales,
        'lotes': data['lotes'],
        'count_lotes': data['count_lotes'],
        'excluye_caducados': True,
    }
