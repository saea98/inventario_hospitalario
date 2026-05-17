"""
Utilidades para comparar inventario entre dos fechas (corte al cierre del día).

Existencia histórica por lote: último ``MovimientoInventario`` no anulado con
``fecha_movimiento`` <= fecha; si no hay movimiento, ``cantidad_inicial`` si el lote
ya existía (``fecha_recepcion`` <= fecha).

Inventario disponible neto (fecha B = hoy): ``cantidad_disponible`` − reservas activas,
alineado al reporte de inventario detallado.
"""

from collections import defaultdict
from datetime import date

from django.db.models import (
    Case,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Lote, MovimientoInventario
from .pedidos_models import LoteAsignado

TIPOS_INCREMENTAN = frozenset(
    {'ENTRADA', 'AJUSTE_POSITIVO', 'TRANSFERENCIA_ENTRADA'}
)
TIPOS_DECREMENTAN = frozenset(
    {'SALIDA', 'AJUSTE_NEGATIVO', 'TRANSFERENCIA_SALIDA', 'CADUCIDAD', 'DETERIORO'}
)

AGRUPACIONES = {
    'clave': ('producto__clave_cnis',),
    'clave_clues': ('producto__clave_cnis', 'institucion__clue'),
    'clave_clues_almacen': (
        'producto__clave_cnis',
        'institucion__clue',
        'almacen__nombre',
    ),
    'lote': (
        'producto__clave_cnis',
        'numero_lote',
        'institucion__clue',
    ),
}


def _subquery_existencia_fisica_en_fecha(fecha):
    return (
        MovimientoInventario.objects.filter(
            lote_id=OuterRef('pk'),
            anulado=False,
            fecha_movimiento__date__lte=fecha,
        )
        .exclude(tipo_movimiento='AJUSTE_DATOS_LOTE')
        .order_by('-fecha_movimiento', '-id')
        .values('cantidad_nueva')[:1]
    )


def _subquery_reserva_activa():
    return (
        LoteAsignado.objects.filter(
            lote_ubicacion__lote_id=OuterRef('pk'),
            surtido=False,
        )
        .order_by()
        .values('lote_ubicacion__lote_id')
        .annotate(t=Sum('cantidad_asignada'))
        .values('t')[:1]
    )


def annotar_existencias_comparativo(lotes_qs, fecha_a, fecha_b):
    """
    Anota por lote: existencia física en A y B (historial), disponible neto actual
  y delta físico.
    """
    subq_a = _subquery_existencia_fisica_en_fecha(fecha_a)
    subq_b = _subquery_existencia_fisica_en_fecha(fecha_b)
    reserva = _subquery_reserva_activa()

    existencia_si_recepcion = lambda f: Case(
        When(fecha_recepcion__lte=f, then=F('cantidad_inicial')),
        default=Value(0),
        output_field=IntegerField(),
    )

    qs = lotes_qs.annotate(
        _reserva=Coalesce(Subquery(reserva, output_field=IntegerField()), Value(0)),
        exist_a=Coalesce(
            Subquery(subq_a, output_field=IntegerField()),
            existencia_si_recepcion(fecha_a),
            output_field=IntegerField(),
        ),
        exist_b_fisica=Coalesce(
            Subquery(subq_b, output_field=IntegerField()),
            existencia_si_recepcion(fecha_b),
            output_field=IntegerField(),
        ),
    ).annotate(
        exist_b_neto=Case(
            When(
                cantidad_disponible__lte=F('_reserva'),
                then=Value(0),
            ),
            default=F('cantidad_disponible') - F('_reserva'),
            output_field=IntegerField(),
        ),
        delta_fisica=F('exist_b_fisica') - F('exist_a'),
    )
    return qs


def _campos_agrupacion(agrupacion):
    return AGRUPACIONES.get(agrupacion, AGRUPACIONES['clave'])


def _etiqueta_grupo(row, agrupacion):
    clave = row.get('producto__clave_cnis') or ''
    if agrupacion == 'clave':
        return clave
    clues = row.get('institucion__clue') or ''
    if agrupacion == 'clave_clues':
        return f'{clave} | {clues}'
    almacen = row.get('almacen__nombre') or ''
    if agrupacion == 'clave_clues_almacen':
        return f'{clave} | {clues} | {almacen}'
    lote = row.get('numero_lote') or ''
    return f'{clave} | {lote} | {clues}'


def agregar_diferencias_por_grupo(
    lotes_qs, fecha_a, fecha_b, agrupacion='clave', top_n=200, metrica='disponible'
):
    """
    Devuelve lista de dicts ordenada por |delta| descendente.

    metrica:
      - ``fisica``: ambas fechas con existencia física (historial de movimientos).
      - ``disponible``: fecha B con inventario neto actual si B es hoy; si no, física.
    """
    hoy = timezone.localdate()
    usar_neto_b = metrica == 'disponible' and fecha_b >= hoy
    campos = list(_campos_agrupacion(agrupacion))

    lotes = annotar_existencias_comparativo(lotes_qs, fecha_a, fecha_b)
    valores = ['exist_a']
    if usar_neto_b:
        valores.append('exist_b_neto')
    else:
        valores.append('exist_b_fisica')

    agg = (
        lotes.values(*campos)
        .annotate(
            total_a=Sum('exist_a'),
            total_b_fisica=Sum('exist_b_fisica'),
            total_b_neto=Sum('exist_b_neto'),
        )
        .order_by()
    )

    filas = []
    for row in agg:
        total_a = int(row['total_a'] or 0)
        total_b = int(
            (row['total_b_neto'] if usar_neto_b else row['total_b_fisica']) or 0
        )
        delta = total_b - total_a
        filas.append(
            {
                'grupo': _etiqueta_grupo(row, agrupacion),
                'clave_cnis': row.get('producto__clave_cnis') or '',
                'clues': row.get('institucion__clue') or '',
                'almacen': row.get('almacen__nombre') or '',
                'numero_lote': row.get('numero_lote') or '',
                'total_a': total_a,
                'total_b': total_b,
                'delta': delta,
                'delta_abs': abs(delta),
                'metrica_b': 'disponible_neto' if usar_neto_b else 'fisica_historica',
            }
        )

    filas.sort(key=lambda x: x['delta_abs'], reverse=True)
    return filas[:top_n], usar_neto_b


def signo_movimiento(tipo):
    if tipo in TIPOS_INCREMENTAN:
        return 1
    if tipo in TIPOS_DECREMENTAN:
        return -1
    return 0


_signo_movimiento = signo_movimiento


def movimientos_en_periodo(lotes_qs, fecha_a, fecha_b, clave_cnis=None, limite=500):
    """
    Movimientos entre fecha_a (excl.) y fecha_b (incl.) para lotes del queryset.
    """
    lote_ids = list(lotes_qs.values_list('id', flat=True))
    if not lote_ids:
        return []

    movs = (
        MovimientoInventario.objects.filter(
            lote_id__in=lote_ids,
            anulado=False,
            fecha_movimiento__date__gt=fecha_a,
            fecha_movimiento__date__lte=fecha_b,
        )
        .exclude(tipo_movimiento='AJUSTE_DATOS_LOTE')
        .select_related(
            'lote',
            'lote__producto',
            'lote__institucion',
            'lote__almacen',
            'usuario',
            'institucion_destino',
        )
        .order_by('-fecha_movimiento', '-id')
    )
    if clave_cnis:
        movs = movs.filter(lote__producto__clave_cnis=clave_cnis)

    out = []
    for m in movs[:limite]:
        signo = _signo_movimiento(m.tipo_movimiento)
        efecto = signo * int(m.cantidad or 0)
        out.append(
            {
                'fecha': m.fecha_movimiento,
                'clave_cnis': m.lote.producto.clave_cnis if m.lote.producto else '',
                'numero_lote': m.lote.numero_lote,
                'clues': m.lote.institucion.clue if m.lote.institucion else '',
                'almacen': m.lote.almacen.nombre if m.lote.almacen else '',
                'tipo': m.tipo_movimiento,
                'cantidad': m.cantidad,
                'efecto': efecto,
                'cantidad_anterior': m.cantidad_anterior,
                'cantidad_nueva': m.cantidad_nueva,
                'motivo': (m.motivo or '')[:200],
                'documento': m.documento_referencia or '',
                'folio': m.folio or '',
                'usuario': (
                    m.usuario.get_full_name() or m.usuario.username
                    if m.usuario
                    else ''
                ),
            }
        )
    return out


def resumen_movimientos_por_clave(lotes_qs, fecha_a, fecha_b, claves=None):
    """
    Suma del efecto neto de movimientos por clave CNIS en el periodo.
    """
    lote_ids = list(lotes_qs.values_list('id', flat=True))
    if not lote_ids:
        return {}

    movs = (
        MovimientoInventario.objects.filter(
            lote_id__in=lote_ids,
            anulado=False,
            fecha_movimiento__date__gt=fecha_a,
            fecha_movimiento__date__lte=fecha_b,
        )
        .exclude(tipo_movimiento='AJUSTE_DATOS_LOTE')
        .values('lote__producto__clave_cnis', 'tipo_movimiento')
        .annotate(total_qty=Sum('cantidad'))
    )

    por_clave = defaultdict(lambda: {'entradas': 0, 'salidas': 0, 'neto_mov': 0})
    for row in movs:
        clave = row['lote__producto__clave_cnis'] or ''
        if claves is not None and clave not in claves:
            continue
        tipo = row['tipo_movimiento']
        qty = int(row['total_qty'] or 0)
        signo = _signo_movimiento(tipo)
        if signo > 0:
            por_clave[clave]['entradas'] += qty
        elif signo < 0:
            por_clave[clave]['salidas'] += qty
        por_clave[clave]['neto_mov'] += signo * qty

    return dict(por_clave)


def totales_globales(lotes_qs, fecha_a, fecha_b, usar_neto_b, metrica='disponible'):
    hoy = timezone.localdate()
    if metrica == 'fisica':
        usar_neto_b = False
    elif metrica == 'disponible' and fecha_b >= hoy:
        usar_neto_b = True
    """Totales de inventario en todo el queryset filtrado (no solo top N)."""
    agg = annotar_existencias_comparativo(lotes_qs, fecha_a, fecha_b).aggregate(
        total_a=Sum('exist_a'),
        total_b_fisica=Sum('exist_b_fisica'),
        total_b_neto=Sum('exist_b_neto'),
    )
    total_a = int(agg['total_a'] or 0)
    total_b = int(
        (agg['total_b_neto'] if usar_neto_b else agg['total_b_fisica']) or 0
    )
    return {
        'total_a': total_a,
        'total_b': total_b,
        'delta': total_b - total_a,
        'delta_abs': abs(total_b - total_a),
    }


def enriquecer_filas_con_movimientos(filas, mov_por_clave):
    for f in filas:
        m = mov_por_clave.get(f['clave_cnis'], {})
        f['mov_neto'] = m.get('neto_mov', 0)
        f['mov_entradas'] = m.get('entradas', 0)
        f['mov_salidas'] = m.get('salidas', 0)
        f['diff_vs_movimientos'] = f['delta'] - f['mov_neto']
    return filas
