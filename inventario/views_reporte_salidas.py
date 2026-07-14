"""
Reporte de Salidas al Inventario (Inventario de Salidas)

Para auditorías: muestra todas las salidas (MovimientoInventario tipo SALIDA)
con el layout oficial: Clave CNIS, Producto, LOTE, CANTIDAD SURTIDA,
CLUES DEL ALMACÉN, ALMACÉN, P.P., RFC, Proveedor, FOLIO DE SALIDA, FECHA DE ENTREGA, UNIDAD HOSPITALARIA,
CLUES DESTINO SSA/IMB, CONTRATO, REMISIÓN, ORDEN DE SUMINISTRO, LICITACIÓN, Precio, Importe.
"""

from datetime import datetime, timedelta, time as dt_time
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Min, Sum, Count, F, Value, DecimalField
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook

from .models import MovimientoInventario, Institucion, Almacen
from .propuesta_utils import enriquecer_movimientos_folio_observaciones_surtimiento

# Layout del reporte de salidas para auditorías
SALIDAS_LAYOUT_HEADERS = [
    'Clave CNIS',
    'Producto',
    'UNIDAD DE MEDIDA',
    'LOTE',
    'CADUCIDAD',
    'CANTIDAD SURTIDA',
    'CLUES DEL ALMACÉN',
    'ALMACÉN',
    'P.P.',
    'RFC',
    'Proveedor',
    'FOLIO DE SALIDA',
    'FOLIO DE PEDIDO',
    'FECHA DE ENTREGA',
    'UNIDAD HOSPITALARIA',
    'CLUES DESTINO SSA',
    'CLUES DESTINO IMB',
    'CONTRATO',
    'REMISION',
    'ORDEN DE SUMINISTRO',
    'LICITACIÓN/PROCEDIMIENTO',
    'Precio',
    'Importe',
    'USUARIO MOVIMIENTO',
]

REPORTE_SALIDAS_MAX_EXCEL_ROWS = 50000
REPORTE_SALIDAS_DIAS_DEFAULT = 30


def _valor(o, default=''):
    if o is None:
        return default
    return o


def _fecha(d, fmt='%d/%m/%Y'):
    if not d:
        return ''
    if hasattr(d, 'strftime'):
        return d.strftime(fmt)
    return str(d)


def _decimal(d, default=''):
    if d is None:
        return default
    if isinstance(d, Decimal):
        return float(d)
    return d


def _hay_filtros_reporte_salidas(data):
    """Al menos un criterio para ejecutar el reporte (evita escanear todas las salidas)."""
    return any(
        [
            (data.get('fecha_desde') or '').strip(),
            (data.get('fecha_hasta') or '').strip(),
            (data.get('clave') or '').strip(),
            (data.get('lote') or '').strip(),
            (data.get('almacen') or '').strip(),
            (data.get('destino') or '').strip(),
            (data.get('folio') or '').strip(),
        ]
    )


def _parse_fecha(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        return None


def _rango_datetime(fecha_ini, fecha_fin):
    tz = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(fecha_ini, dt_time.min), tz) if fecha_ini else None
    fin_exclusivo = None
    if fecha_fin:
        fin_exclusivo = timezone.make_aware(
            datetime.combine(fecha_fin + timedelta(days=1), dt_time.min),
            tz,
        )
    return inicio, fin_exclusivo


def _extraer_filtros(request):
    """Lee filtros GET y aplica ventana de 30 días si no hay fechas ni búsqueda puntual."""
    filtro_fecha_desde = (request.GET.get('fecha_desde') or '').strip()
    filtro_fecha_hasta = (request.GET.get('fecha_hasta') or '').strip()
    filtro_clave = (request.GET.get('clave') or '').strip()
    filtro_lote = (request.GET.get('lote') or '').strip()
    filtro_almacen = (request.GET.get('almacen') or '').strip()
    filtro_destino = (request.GET.get('destino') or '').strip()
    filtro_folio = (request.GET.get('folio') or '').strip()

    fechas_por_defecto = False
    f_desde = _parse_fecha(filtro_fecha_desde)
    f_hasta = _parse_fecha(filtro_fecha_hasta)

    # Folio/clave/lote suelen ser selectivos; sin eso, exigir ventana corta
    if not f_desde and not f_hasta and not filtro_folio and not filtro_clave and not filtro_lote:
        f_hasta = timezone.localdate()
        f_desde = f_hasta - timedelta(days=REPORTE_SALIDAS_DIAS_DEFAULT)
        filtro_fecha_desde = f_desde.isoformat()
        filtro_fecha_hasta = f_hasta.isoformat()
        fechas_por_defecto = True

    return {
        'fecha_desde': filtro_fecha_desde,
        'fecha_hasta': filtro_fecha_hasta,
        'f_desde': f_desde,
        'f_hasta': f_hasta,
        'clave': filtro_clave,
        'lote': filtro_lote,
        'almacen': filtro_almacen,
        'destino': filtro_destino,
        'folio': filtro_folio,
        'fechas_por_defecto': fechas_por_defecto,
    }


def _apply_filtros_salidas(qs, filtros):
    dt_inicio, dt_fin_excl = _rango_datetime(filtros['f_desde'], filtros['f_hasta'])
    if dt_inicio:
        qs = qs.filter(fecha_movimiento__gte=dt_inicio)
    if dt_fin_excl:
        qs = qs.filter(fecha_movimiento__lt=dt_fin_excl)
    if filtros['clave']:
        qs = qs.filter(lote__producto__clave_cnis__icontains=filtros['clave'])
    if filtros['lote']:
        qs = qs.filter(lote__numero_lote__icontains=filtros['lote'])
    if filtros['almacen']:
        qs = qs.filter(lote__almacen__nombre=filtros['almacen'])
    if filtros['destino']:
        qs = qs.filter(
            Q(institucion_destino__denominacion__icontains=filtros['destino'])
            | Q(institucion_destino__clue__icontains=filtros['destino'])
        )
    if filtros['folio']:
        qs = qs.filter(folio__icontains=filtros['folio'])
    return qs


def _queryset_base_salidas(filtros):
    qs = MovimientoInventario.objects.filter(tipo_movimiento='SALIDA', anulado=False)
    return _apply_filtros_salidas(qs, filtros)


def _ids_movimientos_unicos(qs):
    """
    Deduplicación en BD: conserva el menor id por huella
    (lote, folio, cantidades, fecha, motivo). Evita list() de todos los objetos.
    """
    return (
        qs.values(
            'lote_id',
            'folio',
            'cantidad',
            'cantidad_anterior',
            'cantidad_nueva',
            'fecha_movimiento',
            'motivo',
        )
        .annotate(keep_id=Min('id'))
        .values('keep_id')
    )


def _queryset_salidas_unicas(filtros):
    """Queryset de MovimientoInventario ya deduplicado, listo para paginar/exportar."""
    base = _queryset_base_salidas(filtros)
    keep = _ids_movimientos_unicos(base)
    return (
        MovimientoInventario.objects.filter(id__in=keep)
        .select_related(
            'lote',
            'lote__producto',
            'lote__almacen',
            'lote__almacen__institucion',
            'lote__orden_suministro',
            'lote__orden_suministro__proveedor',
            'institucion_destino',
            'usuario',
        )
        .order_by('-fecha_movimiento', 'id')
    )


def _totales_salidas(qs):
    """Totales sin materializar filas (importe ≈ importe_total o cantidad * precio)."""
    importe_expr = Coalesce(
        F('importe_total'),
        F('cantidad') * Coalesce(F('lote__precio_unitario'), Value(0)),
        output_field=DecimalField(max_digits=18, decimal_places=2),
    )
    agg = qs.aggregate(
        total_registros=Count('id'),
        total_cantidad=Coalesce(Sum('cantidad'), Value(0)),
        total_importe=Coalesce(Sum(importe_expr), Value(0), output_field=DecimalField(max_digits=18, decimal_places=2)),
    )
    return {
        'total_registros': agg['total_registros'] or 0,
        'total_cantidad': agg['total_cantidad'] or 0,
        'total_importe': float(agg['total_importe'] or 0),
    }


def _construir_fila_salida(m):
    """Construye la fila para un MovimientoInventario SALIDA."""
    lote = m.lote
    prod = lote.producto if lote else None
    os = lote.orden_suministro if lote else None
    prov = os.proveedor if os else None
    almacen = lote.almacen if lote else None
    inst_origen = almacen.institucion if almacen else None
    inst_destino = m.institucion_destino

    precio = (lote and lote.precio_unitario) or Decimal('0')
    importe_val = (m.importe_total or (lote and lote.importe_total))
    if importe_val is None:
        importe_val = m.cantidad * precio

    partida_presupuestal = (lote and lote.partida) or (os and os.partida_presupuestal)
    rfc = _valor(prov and prov.rfc or (lote and getattr(lote, 'rfc_proveedor', None)))
    proveedor_nombre = _valor(prov and prov.razon_social or (lote and getattr(lote, 'proveedor', None)))

    return [
        _valor(prod and prod.clave_cnis),
        _valor(prod and prod.descripcion),
        _valor(prod and prod.unidad_medida) or 'PIEZA',
        _valor(lote and lote.numero_lote),
        _fecha(lote and lote.fecha_caducidad),
        m.cantidad,
        _valor(inst_origen and inst_origen.clue),
        _valor(almacen and almacen.nombre),
        _valor(partida_presupuestal),
        rfc,
        proveedor_nombre,
        _valor(m.folio),
        _valor(getattr(m, '_folio_obs_solicitud', None) or (lote and lote.observaciones)),
        _fecha(m.fecha_movimiento, '%d/%m/%Y %H:%M') if m.fecha_movimiento else '',
        _valor(inst_destino and inst_destino.denominacion),
        _valor(inst_destino and inst_destino.clue),
        _valor(inst_destino and inst_destino.ib_clue),
        _valor(m.contrato or (lote and lote.contrato)),
        _valor(m.remision or (lote and lote.remision)),
        _valor(os and os.numero_orden),
        _valor(m.licitacion or (lote and lote.licitacion)),
        _decimal(precio),
        _decimal(importe_val),
        _valor((m.usuario.get_full_name() or m.usuario.username) if getattr(m, 'usuario', None) else ''),
    ]


@login_required
def reporte_salidas(request):
    """
    Reporte de salidas al inventario (Inventario de Salidas) para auditorías.
    Sin filtros no se consulta la BD. Con filtros: dedupe en SQL + paginación en BD.
    """
    requiere_filtros = not _hay_filtros_reporte_salidas(request.GET)
    filtros = _extraer_filtros(request) if not requiere_filtros else {
        'fecha_desde': (request.GET.get('fecha_desde') or '').strip(),
        'fecha_hasta': (request.GET.get('fecha_hasta') or '').strip(),
        'clave': (request.GET.get('clave') or '').strip(),
        'lote': (request.GET.get('lote') or '').strip(),
        'almacen': (request.GET.get('almacen') or '').strip(),
        'destino': (request.GET.get('destino') or '').strip(),
        'folio': (request.GET.get('folio') or '').strip(),
        'fechas_por_defecto': False,
        'f_desde': None,
        'f_hasta': None,
    }

    salidas_page = []
    totales = {'total_registros': 0, 'total_cantidad': 0, 'total_importe': 0.0}
    page_obj = None

    if not requiere_filtros:
        qs = _queryset_salidas_unicas(filtros)
        totales = _totales_salidas(qs)

        paginator = Paginator(qs, 25)
        page_obj = paginator.get_page(request.GET.get('page'))
        movimientos_pagina = list(page_obj.object_list)
        enriquecer_movimientos_folio_observaciones_surtimiento(movimientos_pagina)
        salidas_page = [{'row': _construir_fila_salida(m), 'id': m.id} for m in movimientos_pagina]

        # Sustituir object_list para que el template itere filas ya armadas
        page_obj.object_list = salidas_page

    instituciones = Institucion.objects.all().order_by('denominacion')
    almacenes = Almacen.objects.all().order_by('nombre')

    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    if filtros.get('fechas_por_defecto'):
        params['fecha_desde'] = filtros['fecha_desde']
        params['fecha_hasta'] = filtros['fecha_hasta']
    query_string = params.urlencode()

    if page_obj is None:
        page_obj = Paginator([], 25).get_page(1)

    context = {
        'page_obj': page_obj,
        'headers': SALIDAS_LAYOUT_HEADERS,
        'total_registros': totales['total_registros'],
        'total_cantidad': totales['total_cantidad'],
        'total_importe': totales['total_importe'],
        'almacenes': almacenes,
        'instituciones': instituciones,
        'filtro_fecha_desde': filtros['fecha_desde'],
        'filtro_fecha_hasta': filtros['fecha_hasta'],
        'filtro_clave': filtros['clave'],
        'filtro_lote': filtros['lote'],
        'filtro_almacen': filtros['almacen'],
        'filtro_destino': filtros['destino'],
        'filtro_folio': filtros['folio'],
        'requiere_filtros': requiere_filtros,
        'fechas_por_defecto': filtros.get('fechas_por_defecto', False),
        'query_string': query_string,
    }
    return render(request, 'inventario/reporte_salidas.html', context)


@login_required
def exportar_salidas_excel(request):
    """Exporta el reporte de salidas a Excel (write_only + iterator por lotes)."""
    if not _hay_filtros_reporte_salidas(request.GET):
        messages.warning(
            request,
            'Para exportar debe indicar al menos un filtro (fechas, clave CNIS, lote, '
            'almacén origen, destino o folio de salida).',
        )
        return redirect('reporte_salidas')

    filtros = _extraer_filtros(request)
    qs = _queryset_salidas_unicas(filtros)

    total = qs.count()
    if total > REPORTE_SALIDAS_MAX_EXCEL_ROWS:
        messages.error(
            request,
            f'El resultado tiene {total:,} filas (máximo {REPORTE_SALIDAS_MAX_EXCEL_ROWS:,}). '
            'Reduce el rango de fechas u otros filtros e inténtalo de nuevo.',
        )
        return redirect(f"{reverse('reporte_salidas')}?{request.GET.urlencode()}")

    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title='Salidas')
    ws.append(list(SALIDAS_LAYOUT_HEADERS))

    total_cantidad = 0
    total_importe_val = 0.0
    chunk = 1500

    # Solo IDs en memoria (liviano); objetos + select_related por lotes
    ids = list(qs.values_list('id', flat=True))
    for i in range(0, len(ids), chunk):
        batch_ids = ids[i:i + chunk]
        by_id = {
            m.id: m
            for m in MovimientoInventario.objects.filter(id__in=batch_ids).select_related(
                'lote',
                'lote__producto',
                'lote__almacen',
                'lote__almacen__institucion',
                'lote__orden_suministro',
                'lote__orden_suministro__proveedor',
                'institucion_destino',
                'usuario',
            )
        }
        batch = [by_id[pk] for pk in batch_ids if pk in by_id]
        enriquecer_movimientos_folio_observaciones_surtimiento(batch)
        for mov in batch:
            fila = _construir_fila_salida(mov)
            ws.append(fila)
            total_cantidad += fila[5] or 0
            total_importe_val += float(fila[22] or 0)

    total_row = ['TOTALES'] + [''] * (len(SALIDAS_LAYOUT_HEADERS) - 1)
    total_row[5] = total_cantidad
    total_row[22] = total_importe_val
    ws.append(total_row)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="reporte_salidas.xlsx"'
    wb.save(response)
    return response
