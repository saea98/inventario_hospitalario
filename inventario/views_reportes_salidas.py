"""
Vistas para Reportes de Salidas y Análisis
Basados en MovimientoInventario generados por Fase 5
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q, F, DecimalField, Exists, OuterRef, CharField
from django.db.models.functions import Cast
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta, datetime, time as dt_time
import json
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from .models import (
    MovimientoInventario, Lote, Institucion, Almacen, Producto, LoteUbicacion
)
from .pedidos_models import PropuestaPedido, ItemPropuesta, LoteAsignado, SolicitudPedido
from .decorators_roles import requiere_rol
from .propuesta_utils import liberar_cantidad_lote
from django.db import transaction

logger = logging.getLogger(__name__)


# ============================================================
# REPORTE GENERAL DE SALIDAS
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista')
def reporte_general_salidas(request):
    """Reporte general de salidas basado en MovimientoInventario"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Consulta base: Movimientos de tipo SALIDA de la institución
    movimientos = MovimientoInventario.objects.filter(
        tipo_movimiento='SALIDA',
        lote__institucion=institucion
    )
    
    # Aplicar filtros de fecha
    if fecha_inicio:
        movimientos = movimientos.filter(fecha_movimiento__gte=fecha_inicio)
    if fecha_fin:
        movimientos = movimientos.filter(fecha_movimiento__lte=fecha_fin)
    
    # Estadísticas
    total_salidas = movimientos.count()
    total_cantidad = movimientos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    total_monto = movimientos.aggregate(
        total=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    )['total'] or 0
    
    # Salidas por almacén
    salidas_por_almacen = movimientos.values('lote__almacen__nombre').annotate(
        cantidad_movimientos=Count('id'),
        total_cantidad=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    ).order_by('-total_cantidad')
    
    # Top 10 productos más salidos
    top_productos = movimientos.values('lote__producto__descripcion').annotate(
        total_cantidad=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField()),
        cantidad_movimientos=Count('id')
    ).order_by('-total_cantidad')[:10]
    
    context = {
        'total_salidas': total_salidas,
        'total_cantidad': total_cantidad,
        'total_monto': total_monto,
        'promedio_cantidad': total_cantidad / total_salidas if total_salidas > 0 else 0,
        'salidas_por_almacen': salidas_por_almacen,
        'top_productos': top_productos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'inventario/reportes_salidas/reporte_general.html', context)


# ============================================================
# ANÁLISIS DE DISTRIBUCIONES
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista')
def analisis_distribuciones(request):
    """Análisis de distribuciones basado en MovimientoInventario"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Consulta base
    movimientos = MovimientoInventario.objects.filter(
        tipo_movimiento='SALIDA',
        lote__institucion=institucion
    )
    
    # Aplicar filtros de fecha
    if fecha_inicio:
        movimientos = movimientos.filter(fecha_movimiento__gte=fecha_inicio)
    if fecha_fin:
        movimientos = movimientos.filter(fecha_movimiento__lte=fecha_fin)
    
    # Estadísticas
    total_movimientos = movimientos.count()
    total_cantidad = movimientos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    total_monto = movimientos.aggregate(
        total=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    )['total'] or 0
    
    # Distribuciones por almacén origen
    distribuciones_almacen = movimientos.values('lote__almacen__nombre').annotate(
        cantidad_movimientos=Count('id'),
        total_cantidad=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    ).order_by('-total_cantidad')
    
    # Análisis por motivo (propuesta)
    distribuciones_propuesta = movimientos.values('motivo').annotate(
        cantidad_movimientos=Count('id'),
        total_cantidad=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    ).order_by('-total_cantidad')[:10]
    
    context = {
        'total_movimientos': total_movimientos,
        'total_cantidad': total_cantidad,
        'total_monto': total_monto,
        'distribuciones_almacen': distribuciones_almacen,
        'distribuciones_propuesta': distribuciones_propuesta,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'inventario/reportes_salidas/analisis_distribuciones.html', context)


# ============================================================
# ANÁLISIS TEMPORAL
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista')
def analisis_temporal(request):
    """Análisis temporal de salidas (últimos 30 días)"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Últimos 30 días
    fecha_inicio = timezone.now() - timedelta(days=30)
    
    # Consulta base
    movimientos = MovimientoInventario.objects.filter(
        tipo_movimiento='SALIDA',
        lote__institucion=institucion,
        fecha_movimiento__gte=fecha_inicio
    )
    
    # Datos temporales por día
    datos_temporales = []
    for i in range(30, -1, -1):
        fecha = timezone.now() - timedelta(days=i)
        fecha_inicio_dia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_dia = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        movimientos_dia = movimientos.filter(
            fecha_movimiento__gte=fecha_inicio_dia,
            fecha_movimiento__lte=fecha_fin_dia
        )
        
        cantidad_movimientos = movimientos_dia.count()
        total_cantidad = movimientos_dia.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        total_monto = movimientos_dia.aggregate(
            total=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
        )['total'] or 0
        
        if cantidad_movimientos > 0:
            datos_temporales.append({
                'fecha': fecha.strftime('%d/%m/%Y'),
                'cantidad': cantidad_movimientos,
                'items': total_cantidad,
                'monto': float(total_monto) if total_monto else 0
            })
    
    # Estadísticas generales
    total_movimientos = movimientos.count()
    total_cantidad = movimientos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    total_monto = movimientos.aggregate(
        total=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    )['total'] or 0
    
    context = {
        'datos_temporales': datos_temporales,
        'total_movimientos': total_movimientos,
        'total_cantidad': total_cantidad,
        'total_monto': total_monto,
        'promedio_diario': total_movimientos / 30 if total_movimientos > 0 else 0,
    }
    
    return render(request, 'inventario/reportes_salidas/analisis_temporal.html', context)


# ============================================================
# REPORTE DE SALIDAS - ÓRDENES DE SURTIMIENTO SURTIDAS
# ============================================================

SURTIDAS_DIAS_DEFAULT = 30
SURTIDAS_MAX_EXCEL_ROWS = 50000


def _parse_fecha_surtidas(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        return None


def _subquery_tiene_movimiento_salida():
    """Exists: hay MovimientoInventario SALIDA con folio=UUID propuesta y mismo lote."""
    return MovimientoInventario.objects.filter(
        tipo_movimiento='SALIDA',
        lote_id=OuterRef('lote_ubicacion__lote_id'),
        folio=Cast(OuterRef('item_propuesta__propuesta_id'), CharField()),
    )


def _extraer_filtros_surtidas(request):
    """Lee filtros GET; aplica últimos N días si no hay fechas ni búsqueda puntual."""
    fecha_inicio = (request.GET.get('fecha_inicio') or '').strip()
    fecha_fin = (request.GET.get('fecha_fin') or '').strip()
    folio = (request.GET.get('folio') or '').strip()
    clave_cnis = (request.GET.get('clave_cnis') or '').strip()
    filtro_lote = (request.GET.get('lote') or '').strip()
    institucion_id = (request.GET.get('institucion') or '').strip()
    estatus_movimiento = (request.GET.get('estatus_movimiento') or '').strip()

    f_ini = _parse_fecha_surtidas(fecha_inicio)
    f_fin = _parse_fecha_surtidas(fecha_fin)
    fechas_por_defecto = False

    if not f_ini and not f_fin and not folio and not clave_cnis and not filtro_lote:
        f_fin = timezone.localdate()
        f_ini = f_fin - timedelta(days=SURTIDAS_DIAS_DEFAULT)
        fecha_inicio = f_ini.isoformat()
        fecha_fin = f_fin.isoformat()
        fechas_por_defecto = True

    return {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'f_ini': f_ini,
        'f_fin': f_fin,
        'folio': folio,
        'clave_cnis': clave_cnis,
        'filtro_lote': filtro_lote,
        'institucion_id': institucion_id,
        'estatus_movimiento': estatus_movimiento,
        'fechas_por_defecto': fechas_por_defecto,
    }


def _queryset_lotes_asignados_surtidos(filtros, anotar_movimiento=True):
    """
    Una fila del reporte = LoteAsignado surtido de propuesta SURTIDA.
    Evita materializar propuestas + prefetch masivo.
    """
    qs = (
        LoteAsignado.objects.filter(
            surtido=True,
            item_propuesta__propuesta__estado='SURTIDA',
            item_propuesta__propuesta__fecha_surtimiento__isnull=False,
        )
        .select_related(
            'item_propuesta__producto',
            'item_propuesta__propuesta__solicitud__institucion_solicitante',
            'item_propuesta__propuesta__solicitud__almacen_destino__institucion',
            'item_propuesta__propuesta__usuario_surtimiento',
            'lote_ubicacion__lote__orden_suministro',
            'lote_ubicacion__ubicacion',
        )
        .order_by(
            '-item_propuesta__propuesta__fecha_surtimiento',
            'item_propuesta__propuesta__solicitud__folio',
            'id',
        )
    )

    tz = timezone.get_current_timezone()
    if filtros['f_ini']:
        qs = qs.filter(
            item_propuesta__propuesta__fecha_surtimiento__gte=timezone.make_aware(
                datetime.combine(filtros['f_ini'], dt_time.min), tz
            )
        )
    if filtros['f_fin']:
        qs = qs.filter(
            item_propuesta__propuesta__fecha_surtimiento__lte=timezone.make_aware(
                datetime.combine(filtros['f_fin'], dt_time.max), tz
            )
        )
    if filtros['folio']:
        qs = qs.filter(
            Q(item_propuesta__propuesta__solicitud__folio__icontains=filtros['folio'])
            | Q(item_propuesta__propuesta__solicitud__observaciones_solicitud__icontains=filtros['folio'])
        )
    if filtros['clave_cnis']:
        qs = qs.filter(item_propuesta__producto__clave_cnis__icontains=filtros['clave_cnis'])
    if filtros['filtro_lote']:
        qs = qs.filter(
            lote_ubicacion__lote__numero_lote__icontains=filtros['filtro_lote']
        )
    if filtros['institucion_id']:
        try:
            qs = qs.filter(
                item_propuesta__propuesta__solicitud__institucion_solicitante_id=int(
                    filtros['institucion_id']
                )
            )
        except (ValueError, TypeError):
            pass

    if anotar_movimiento:
        qs = qs.annotate(_tiene_mov=Exists(_subquery_tiene_movimiento_salida()))
        estatus = filtros.get('estatus_movimiento') or ''
        if estatus == 'sin_movimiento':
            qs = qs.filter(_tiene_mov=False)
        elif estatus == 'con_movimiento':
            qs = qs.filter(_tiene_mov=True)

    return qs


def _mapear_movimientos_salida(propuesta_ids):
    """Dicts de lookup para remisión / tiene_movimiento de una página o lote Excel."""
    movimientos_por_clave = {}
    movimientos_fallback = {}
    if not propuesta_ids:
        return movimientos_por_clave, movimientos_fallback
    folios_str = [str(pid) for pid in propuesta_ids]
    for m in MovimientoInventario.objects.filter(
        tipo_movimiento='SALIDA', folio__in=folios_str
    ).only('id', 'lote_id', 'folio', 'cantidad', 'remision'):
        movimientos_por_clave[(m.lote_id, m.folio or '', m.cantidad)] = m
        k = (m.lote_id, m.folio or '')
        if k not in movimientos_fallback:
            movimientos_fallback[k] = m
    return movimientos_por_clave, movimientos_fallback


def _fila_desde_lote_asignado(la, partida, movimiento=None):
    """Arma el dict de fila para vista/Excel a partir de un LoteAsignado."""
    item = la.item_propuesta
    propuesta = item.propuesta
    solicitud = propuesta.solicitud
    producto = item.producto
    lote_ubicacion = la.lote_ubicacion
    lote = lote_ubicacion.lote
    ubicacion = lote_ubicacion.ubicacion

    cantidad_surtida = la.cantidad_asignada
    cantidad_disponible_lote = getattr(lote, 'cantidad_disponible', None) or 0
    cantidad_previa = cantidad_disponible_lote + cantidad_surtida
    orden_reposicion = lote.orden_suministro.numero_orden if lote.orden_suministro else ''
    dias_caducidad = (
        (lote.fecha_caducidad - timezone.now().date()).days if lote.fecha_caducidad else None
    )
    tiene_movimiento = movimiento is not None
    if hasattr(la, '_tiene_mov') and movimiento is None:
        tiene_movimiento = bool(la._tiene_mov)

    usuario = ''
    if propuesta.usuario_surtimiento:
        usuario = (
            propuesta.usuario_surtimiento.get_full_name()
            or propuesta.usuario_surtimiento.username
        )

    destino = ''
    if solicitud.almacen_destino and solicitud.almacen_destino.institucion:
        inst = solicitud.almacen_destino.institucion
        destino = inst.nombre or inst.denominacion or ''

    return {
        'partida': partida,
        'clave_cnis': producto.clave_cnis if producto else '',
        'descripcion': producto.descripcion if producto else '',
        'unidad_medida': (producto.unidad_medida if producto and producto.unidad_medida else ''),
        'lote': lote.numero_lote,
        'lote_id': lote.pk,
        'lote_ubicacion_id': lote_ubicacion.pk,
        'propuesta_id': propuesta.id,
        'caducidad': lote.fecha_caducidad.strftime('%d/%m/%Y') if lote.fecha_caducidad else '',
        'dias_caducidad': dias_caducidad,
        'cantidad_solicitada': item.cantidad_solicitada,
        'cantidad_disponible': cantidad_disponible_lote,
        'cantidad_previa': cantidad_previa,
        'cantidad_surtida': cantidad_surtida,
        'observaciones': solicitud.observaciones_solicitud or '',
        'recurso': (
            solicitud.institucion_solicitante.nombre
            if solicitud.institucion_solicitante else ''
        ),
        'destino': destino,
        'ubicacion': ubicacion.codigo if ubicacion else '',
        'fecha_captura': (
            solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M')
            if solicitud.fecha_solicitud else ''
        ),
        # Fecha que usa el filtro de rango (propuesta); fallback al lote asignado
        'fecha_surtimiento': (
            (propuesta.fecha_surtimiento or la.fecha_surtimiento).strftime('%d/%m/%Y %H:%M')
            if (propuesta.fecha_surtimiento or la.fecha_surtimiento) else ''
        ),
        'folio': solicitud.observaciones_solicitud or solicitud.folio,
        'fecha_entrega_programada': (
            solicitud.fecha_entrega_programada.strftime('%d/%m/%Y')
            if solicitud.fecha_entrega_programada else ''
        ),
        'status': propuesta.get_estado_display(),
        'tiene_movimiento': tiene_movimiento,
        'estatus_movimiento': (
            'Con movimiento' if tiene_movimiento else 'Sin movimiento - Revisar'
        ),
        'remision_ingreso': movimiento.remision if movimiento else '',
        'orden_reposicion': orden_reposicion,
        'usuario': usuario,
    }


@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista', 'Supervisor')
def reporte_salidas_surtidas(request):
    """
    Reporte detallado de órdenes de surtimiento ya surtidas.
    Una fila por LoteAsignado; paginación en BD (sin prefetch masivo).
    """
    filtros = _extraer_filtros_surtidas(request)
    qs = _queryset_lotes_asignados_surtidos(filtros, anotar_movimiento=True)

    # Contador "sin movimiento" sobre el universo filtrado (antes del filtro de estatus)
    if filtros['estatus_movimiento'] in ('sin_movimiento', 'con_movimiento'):
        qs_base = _queryset_lotes_asignados_surtidos(
            {**filtros, 'estatus_movimiento': ''}, anotar_movimiento=True
        )
        total_sin_movimiento = qs_base.filter(_tiene_mov=False).count()
    else:
        total_sin_movimiento = qs.filter(_tiene_mov=False).count()

    total_registros = qs.count()
    paginator = Paginator(qs, 50)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    lotes_pagina = list(page_obj.object_list)
    propuesta_ids = {
        la.item_propuesta.propuesta_id for la in lotes_pagina
    }
    mov_por_clave, mov_fallback = _mapear_movimientos_salida(propuesta_ids)

    offset = (page_obj.number - 1) * paginator.per_page
    datos = []
    for i, la in enumerate(lotes_pagina, start=offset + 1):
        folio_prop = str(la.item_propuesta.propuesta_id)
        lote_id = la.lote_ubicacion.lote_id
        movimiento = mov_por_clave.get(
            (lote_id, folio_prop, la.cantidad_asignada)
        ) or mov_fallback.get((lote_id, folio_prop))
        datos.append(_fila_desde_lote_asignado(la, i, movimiento))

    page_obj.object_list = datos

    get_copy = request.GET.copy()
    if 'page' in get_copy:
        get_copy.pop('page')
    if filtros['fechas_por_defecto']:
        get_copy['fecha_inicio'] = filtros['fecha_inicio']
        get_copy['fecha_fin'] = filtros['fecha_fin']
    query_string_sin_page = get_copy.urlencode()

    context = {
        'datos': page_obj,
        'total_registros': total_registros,
        'total_sin_movimiento': total_sin_movimiento,
        'fecha_inicio': filtros['fecha_inicio'],
        'fecha_fin': filtros['fecha_fin'],
        'folio': filtros['folio'],
        'clave_cnis': filtros['clave_cnis'],
        'lote': filtros['filtro_lote'],
        'institucion_id': filtros['institucion_id'],
        'instituciones': Institucion.objects.all().order_by('denominacion'),
        'estatus_movimiento': filtros['estatus_movimiento'],
        'query_string_sin_page': query_string_sin_page,
        'fechas_por_defecto': filtros['fechas_por_defecto'],
    }
    return render(request, 'inventario/reportes_salidas/reporte_salidas_surtidas.html', context)


@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista', 'Supervisor')
@require_http_methods(["GET", "POST"])
def aplicar_salida_surtida(request):
    """
    Aplica la salida para un registro surtido que no tiene movimiento de inventario:
    descontar de cantidad disponible del lote, rebajar cantidad reservada y crear
    MovimientoInventario con motivo "Ajuste por sistema".
    """
    if request.method != 'POST':
        logger.info("aplicar_salida_surtida: método no POST, redirigiendo")
        return redirect(reverse('reportes_salidas:reporte_salidas_surtidas'))

    propuesta_id = request.POST.get('propuesta_id')
    lote_id = request.POST.get('lote_id')
    lote_ubicacion_id = request.POST.get('lote_ubicacion_id')
    cantidad = request.POST.get('cantidad')
    return_url = request.POST.get('return_url', '').strip()

    logger.info(
        "aplicar_salida_surtida: POST recibido | propuesta_id=%s lote_id=%s lote_ubicacion_id=%s cantidad=%s return_url=%s",
        propuesta_id, lote_id, lote_ubicacion_id, cantidad, return_url[:80] if return_url else ""
    )

    if not all([propuesta_id, lote_id, lote_ubicacion_id, cantidad]):
        logger.warning("aplicar_salida_surtida: faltan datos en POST")
        messages.error(request, 'Faltan datos para aplicar la salida (propuesta, lote, ubicación o cantidad).')
        return redirect(return_url or reverse('reportes_salidas:reporte_salidas_surtidas'))

    try:
        cantidad = int(cantidad)
        if cantidad <= 0:
            raise ValueError('La cantidad debe ser mayor que cero.')
    except (ValueError, TypeError) as e:
        logger.warning("aplicar_salida_surtida: cantidad inválida cantidad=%s error=%s", cantidad, e)
        messages.error(request, 'Cantidad inválida.')
        return redirect(return_url or reverse('reportes_salidas:reporte_salidas_surtidas'))

    # Cargar LoteUbicacion con lote, producto (clave) y ubicación para afectar y auditar por (clave, lote, ubicación)
    lote_ubicacion = get_object_or_404(
        LoteUbicacion.objects.select_related('lote__producto', 'ubicacion'),
        pk=lote_ubicacion_id
    )
    lote = lote_ubicacion.lote
    ubicacion = lote_ubicacion.ubicacion
    codigo_ubicacion = ubicacion.codigo if ubicacion else ''
    clave_cnis = (lote.producto.clave_cnis or '') if lote.producto else ''

    logger.info(
        "aplicar_salida_surtida: LoteUbicacion cargado | pk=%s lote_id=%s lote_numero=%s ubicacion=%s clave_cnis=%s "
        "cantidad_actual=%s cantidad_reservada_actual=%s",
        lote_ubicacion.pk, lote.pk, lote.numero_lote, codigo_ubicacion, clave_cnis,
        lote_ubicacion.cantidad, getattr(lote_ubicacion, 'cantidad_reservada', None)
    )
    logger.info(
        "aplicar_salida_surtida: Lote cargado | lote_id=%s cantidad_disponible=%s cantidad_reservada=%s",
        lote.pk, lote.cantidad_disponible, getattr(lote, 'cantidad_reservada', None)
    )

    if str(lote.pk) != str(lote_id):
        logger.warning("aplicar_salida_surtida: lote_id no coincide lote.pk=%s lote_id_POST=%s", lote.pk, lote_id)
        messages.error(request, 'El lote no coincide con la ubicación.')
        return redirect(return_url or reverse('reportes_salidas:reporte_salidas_surtidas'))

    propuesta = get_object_or_404(
        PropuestaPedido.objects.select_related('solicitud'),
        id=propuesta_id
    )
    solicitud = propuesta.solicitud

    with transaction.atomic():
        # Afectación exclusiva de esta ubicación (lote_ubicacion = par lote+ubicación)
        cantidad_anterior_ubicacion = lote_ubicacion.cantidad
        cantidad_nueva_ubicacion = cantidad_anterior_ubicacion - cantidad
        if cantidad_nueva_ubicacion < 0:
            logger.warning(
                "aplicar_salida_surtida: cantidad insuficiente en ubicación | lote=%s ubicacion=%s "
                "cantidad_anterior_ubicacion=%s cantidad_a_descontar=%s",
                lote.numero_lote, codigo_ubicacion, cantidad_anterior_ubicacion, cantidad
            )
            messages.error(
                request,
                f'Cantidad insuficiente en lote {lote.numero_lote}, ubicación {codigo_ubicacion}. '
                f'Disponible en esa ubicación: {cantidad_anterior_ubicacion}, a descontar: {cantidad}.'
            )
            return redirect(return_url or reverse('reportes_salidas:reporte_salidas_surtidas'))

        cantidad_anterior_lote = lote.cantidad_disponible or 0
        cantidad_nueva_lote = cantidad_anterior_lote - cantidad
        if cantidad_nueva_lote < 0:
            logger.warning(
                "aplicar_salida_surtida: cantidad insuficiente a nivel lote | lote_id=%s cantidad_disponible=%s cantidad=%s",
                lote.pk, cantidad_anterior_lote, cantidad
            )
            messages.error(request, f'La cantidad disponible del lote ({cantidad_anterior_lote}) es menor que la cantidad a descontar ({cantidad}).')
            return redirect(return_url or reverse('reportes_salidas:reporte_salidas_surtidas'))

        reserva_antes_ubicacion = lote_ubicacion.cantidad_reservada or 0
        reserva_nueva_ubicacion = max(0, reserva_antes_ubicacion - cantidad)

        # Descontar solo en esta ubicación y rebajar reserva de esta ubicación
        lote_ubicacion.cantidad = cantidad_nueva_ubicacion
        lote_ubicacion.cantidad_reservada = reserva_nueva_ubicacion
        logger.info(
            "aplicar_salida_surtida: ANTES save LoteUbicacion | pk=%s cantidad %s -> %s cantidad_reservada %s -> %s",
            lote_ubicacion.pk, cantidad_anterior_ubicacion, cantidad_nueva_ubicacion, reserva_antes_ubicacion, reserva_nueva_ubicacion
        )
        lote_ubicacion.save(update_fields=['cantidad', 'cantidad_reservada'])
        logger.info("aplicar_salida_surtida: LoteUbicacion guardado pk=%s", lote_ubicacion.pk)

        # Recalcular cantidad disponible del lote y rebajar cantidad reservada a nivel lote
        cantidad_total_ubicaciones = sum(lu.cantidad for lu in lote.ubicaciones_detalle.all())
        reserva_antes_lote = lote.cantidad_reservada or 0
        reserva_nueva_lote = max(0, reserva_antes_lote - cantidad)
        lote.cantidad_disponible = cantidad_total_ubicaciones
        lote.cantidad_reservada = reserva_nueva_lote
        logger.info(
            "aplicar_salida_surtida: ANTES save Lote | lote_id=%s cantidad_disponible %s -> %s (suma_ubicaciones=%s) "
            "cantidad_reservada %s -> %s",
            lote.pk, cantidad_anterior_lote, cantidad_total_ubicaciones, cantidad_total_ubicaciones, reserva_antes_lote, reserva_nueva_lote
        )
        lote.save(update_fields=['cantidad_disponible', 'cantidad_reservada'])
        logger.info("aplicar_salida_surtida: Lote guardado lote_id=%s", lote.pk)

        # Registrar movimiento con leyenda "Ajuste por sistema" y tripleta (clave, lote, ubicación)
        motivo_mov = f"Ajuste por sistema. Clave: {clave_cnis}, Lote: {lote.numero_lote}, Ubicación: {codigo_ubicacion}"
        mov = MovimientoInventario.objects.create(
            lote=lote,
            tipo_movimiento='SALIDA',
            cantidad=cantidad,
            cantidad_anterior=cantidad_anterior_lote,
            cantidad_nueva=cantidad_nueva_lote,
            motivo=motivo_mov,
            documento_referencia=(solicitud.folio or '')[:100] if solicitud.folio else '',
            pedido=(solicitud.folio or '')[:255] if solicitud.folio else '',
            folio=str(propuesta.id),
            institucion_destino=solicitud.institucion_solicitante,
            usuario=request.user
        )
        logger.info(
            "aplicar_salida_surtida: MovimientoInventario creado id=%s lote_id=%s cantidad=%s cantidad_anterior=%s cantidad_nueva=%s motivo=%s",
            mov.id, lote.pk, cantidad, cantidad_anterior_lote, cantidad_nueva_lote, motivo_mov[:80]
        )

    logger.info(
        "aplicar_salida_surtida: OK | afectación aplicada clave=%s lote=%s ubicacion=%s cantidad=%s",
        clave_cnis, lote.numero_lote, codigo_ubicacion, cantidad
    )
    messages.success(
        request,
        f'Salida aplicada correctamente: se descontaron {cantidad} unidades (Clave: {clave_cnis}, Lote: {lote.numero_lote}, Ubicación: {codigo_ubicacion}) y se registró el movimiento con motivo "Ajuste por sistema".'
    )
    if return_url and return_url.startswith('/') and not return_url.startswith('//'):
        return redirect(return_url)
    return redirect(reverse('reportes_salidas:reporte_salidas_surtidas'))


@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista', 'Supervisor')
def movimientos_surtimiento(request):
    """
    Muestra los movimientos de inventario generados por un registro de surtimiento
    (propuesta + lote). Recibe propuesta (uuid) y lote (pk) por GET.
    """
    propuesta_id = request.GET.get('propuesta')
    lote_id = request.GET.get('lote')
    if not propuesta_id or not lote_id:
        messages.warning(request, 'Faltan parámetros (propuesta y lote) para ver los movimientos.')
        return redirect('reportes_salidas:reporte_salidas_surtidas')
    movimientos = MovimientoInventario.objects.filter(
        lote_id=lote_id,
        tipo_movimiento='SALIDA',
        folio=str(propuesta_id)
    ).select_related('lote', 'lote__producto', 'usuario').order_by('-fecha_movimiento')
    # Contexto para el breadcrumb / volver
    try:
        lote_obj = Lote.objects.select_related('producto').get(pk=lote_id)
        lote_numero = lote_obj.numero_lote
        producto_desc = (lote_obj.producto.descripcion or '')[:60] if lote_obj.producto else ''
    except Lote.DoesNotExist:
        lote_numero = ''
        producto_desc = ''
    context = {
        'movimientos': movimientos,
        'propuesta_id': propuesta_id,
        'lote_id': lote_id,
        'lote_numero': lote_numero,
        'producto_desc': producto_desc,
    }
    return render(request, 'inventario/reportes_salidas/movimientos_surtimiento.html', context)


@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista', 'Supervisor')
def exportar_salidas_surtidas_excel(request):
    """Exporta salidas surtidas a Excel (write_only, por lotes)."""
    filtros = _extraer_filtros_surtidas(request)
    qs = _queryset_lotes_asignados_surtidos(filtros, anotar_movimiento=True)

    total = qs.count()
    if total > SURTIDAS_MAX_EXCEL_ROWS:
        messages.error(
            request,
            f'El resultado tiene {total:,} filas (máximo {SURTIDAS_MAX_EXCEL_ROWS:,}). '
            'Reduce el rango de fechas u otros filtros e inténtalo de nuevo.',
        )
        return redirect(
            f"{reverse('reportes_salidas:reporte_salidas_surtidas')}?{request.GET.urlencode()}"
        )

    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title='Salidas Surtidas')
    headers = [
        'PARTIDA', 'CLAVE (CNIS)', 'DESCRIPCION', 'UNIDAD DE MEDIDA', 'LOTE',
        'CADUCIDAD', 'CANTIDAD SOLICITADA', 'CANT. PREVIA AL SURTIMIENTO', 'CANTIDAD SURTIDA',
        'OBSERVACIONES', 'RECURSO', 'DESTINO', 'UBICACIÓN', 'FECHA CAPTURA',
        'FECHA SURTIMIENTO', 'FOLIO',
        'FECHA ENTREGA PROGRAMADA', 'STATUS', 'REMISION DE INGRESO',
        'ORDEN DE REPOSICION', 'USUARIO',
    ]
    ws.append(headers)

    chunk = 1500
    ids = list(qs.values_list('id', flat=True))
    partida = 0
    for i in range(0, len(ids), chunk):
        batch_ids = ids[i:i + chunk]
        by_id = {
            la.id: la
            for la in LoteAsignado.objects.filter(id__in=batch_ids).select_related(
                'item_propuesta__producto',
                'item_propuesta__propuesta__solicitud__institucion_solicitante',
                'item_propuesta__propuesta__solicitud__almacen_destino__institucion',
                'item_propuesta__propuesta__usuario_surtimiento',
                'lote_ubicacion__lote__orden_suministro',
                'lote_ubicacion__ubicacion',
            )
        }
        batch = [by_id[pk] for pk in batch_ids if pk in by_id]
        propuesta_ids = {la.item_propuesta.propuesta_id for la in batch}
        mov_por_clave, mov_fallback = _mapear_movimientos_salida(propuesta_ids)

        for la in batch:
            partida += 1
            folio_prop = str(la.item_propuesta.propuesta_id)
            lote_id = la.lote_ubicacion.lote_id
            movimiento = mov_por_clave.get(
                (lote_id, folio_prop, la.cantidad_asignada)
            ) or mov_fallback.get((lote_id, folio_prop))
            d = _fila_desde_lote_asignado(la, partida, movimiento)
            ws.append([
                d['partida'], d['clave_cnis'], d['descripcion'], d['unidad_medida'],
                d['lote'], d['caducidad'], d['cantidad_solicitada'], d['cantidad_previa'],
                d['cantidad_surtida'], d['observaciones'], d['recurso'], d['destino'],
                d['ubicacion'], d['fecha_captura'], d['fecha_surtimiento'], d['folio'],
                d['fecha_entrega_programada'], d['status'], d['remision_ingreso'],
                d['orden_reposicion'], d['usuario'],
            ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"reporte_salidas_surtidas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


# ============================================================
# REPORTE DE RESERVAS
# ============================================================

def _mapas_totales_reservas_activas():
    """
    Totales por lote y por LoteUbicacion (surtido=False) en solo 2 consultas SQL.
    Mismo criterio que _reserva_real_lote / _reserva_real_lote_ubicacion en propuesta_utils.
    """
    qs = LoteAsignado.objects.filter(surtido=False)
    por_lote = {
        pk: (total or 0)
        for pk, total in qs.values('lote_ubicacion__lote_id').annotate(
            total=Sum('cantidad_asignada')
        ).values_list('lote_ubicacion__lote_id', 'total')
    }
    por_lu = {
        pk: (total or 0)
        for pk, total in qs.values('lote_ubicacion_id').annotate(
            total=Sum('cantidad_asignada')
        ).values_list('lote_ubicacion_id', 'total')
    }
    return por_lote, por_lu


def _totales_reservas_para_ids(lote_ids, lu_ids):
    """
    Mismos totales globales por lote / LoteUbicacion, pero solo para los IDs indicados.
    Dos consultas acotadas (ideal para la página HTML con ~50 filas).
    """
    totales_lote = {}
    if lote_ids:
        totales_lote = {
            pk: (total or 0)
            for pk, total in LoteAsignado.objects.filter(
                surtido=False, lote_ubicacion__lote_id__in=lote_ids
            ).values('lote_ubicacion__lote_id').annotate(
                total=Sum('cantidad_asignada')
            ).values_list('lote_ubicacion__lote_id', 'total')
        }
    totales_lu = {}
    if lu_ids:
        totales_lu = {
            pk: (total or 0)
            for pk, total in LoteAsignado.objects.filter(
                surtido=False, lote_ubicacion_id__in=lu_ids
            ).values('lote_ubicacion_id').annotate(
                total=Sum('cantidad_asignada')
            ).values_list('lote_ubicacion_id', 'total')
        }
    return totales_lote, totales_lu


# Ventana por defecto y máxima para reporte de reservas (reduce carga en BD/CPU).
RESERVAS_REPORTE_DIAS_DEFAULT = 7
RESERVAS_REPORTE_MAX_DIAS_INCLUSIVOS = 15


def _parse_fecha_reservas_ymd(s):
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _rango_fechas_reporte_reservas(request):
    """
    Sin fechas en GET: últimos 7 días (incluye hoy).
    Con fechas: como máximo 15 días calendario desde la fecha inicial (recorta fecha fin si hace falta).
    """
    from datetime import time as dt_time

    today = timezone.localdate()
    raw_i = request.GET.get('fecha_inicio', '').strip()
    raw_f = request.GET.get('fecha_fin', '').strip()
    aviso = None
    max_delta = RESERVAS_REPORTE_MAX_DIAS_INCLUSIVOS - 1

    if not raw_i and not raw_f:
        d_fin = today
        d_ini = today - timedelta(days=RESERVAS_REPORTE_DIAS_DEFAULT - 1)
    else:
        d_i = _parse_fecha_reservas_ymd(raw_i) if raw_i else None
        d_f = _parse_fecha_reservas_ymd(raw_f) if raw_f else None
        if d_i is None and d_f is None:
            d_fin = today
            d_ini = today - timedelta(days=RESERVAS_REPORTE_DIAS_DEFAULT - 1)
            aviso = 'Las fechas no son válidas. Se aplicaron los últimos 7 días.'
        elif d_i is not None and d_f is not None:
            if d_f < d_i:
                d_i, d_f = d_f, d_i
            if (d_f - d_i).days > max_delta:
                d_f = d_i + timedelta(days=max_delta)
                aviso = (
                    'El rango máximo es de 15 días desde la fecha inicial. '
                    'Se ajustó la fecha fin.'
                )
            d_ini, d_fin = d_i, d_f
        elif d_i is not None:
            d_ini = d_i
            d_fin = d_i + timedelta(days=max_delta)
        else:
            d_fin = d_f
            d_ini = d_f - timedelta(days=max_delta)

    start_dt = timezone.make_aware(datetime.combine(d_ini, dt_time.min))
    end_dt = timezone.make_aware(
        datetime.combine(d_fin, dt_time.max.replace(microsecond=999999))
    )
    return {
        'fecha_inicio_str': d_ini.strftime('%Y-%m-%d'),
        'fecha_fin_str': d_fin.strftime('%Y-%m-%d'),
        'start_dt': start_dt,
        'end_dt': end_dt,
        'aviso': aviso,
    }


@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista', 'Supervisor')
def reporte_reservas(request):
    """
    Reporte detallado de todas las reservas activas (LoteAsignado con surtido=False).
    Permite al usuario validar y liberar reservas si es necesario.

    Cantidades: la columna de línea usa cantidad_asignada (documento de verdad).
    Totales lote/ubicación: suma de LoteAsignado (surtido=False), no Lote.cantidad_reservada.

    Por defecto se listan los últimos 7 días; el rango consultable está acotado a 15 días
    desde la fecha inicial.
    """
    rango = _rango_fechas_reporte_reservas(request)
    fecha_inicio = rango['fecha_inicio_str']
    fecha_fin = rango['fecha_fin_str']
    aviso_fecha = rango['aviso']

    folio = request.GET.get('folio', '').strip()
    clave_cnis = request.GET.get('clave_cnis', '').strip()
    institucion_id = request.GET.get('institucion')
    estado_propuesta = request.GET.get('estado_propuesta', '')
    
    # Obtener todas las reservas activas (LoteAsignado con surtido=False)
    reservas = LoteAsignado.objects.filter(
        surtido=False
    ).select_related(
        'item_propuesta__propuesta__solicitud',
        'item_propuesta__propuesta__solicitud__institucion_solicitante',
        'item_propuesta__propuesta__solicitud__almacen_destino',
        'item_propuesta__propuesta__solicitud__almacen_destino__institucion',
        'item_propuesta__producto',
        'lote_ubicacion__lote',
        'lote_ubicacion__lote__producto',
        'lote_ubicacion__ubicacion'
    )

    reservas = reservas.filter(
        fecha_asignacion__gte=rango['start_dt'],
        fecha_asignacion__lte=rango['end_dt'],
    )

    if folio:
        reservas = reservas.filter(
            Q(item_propuesta__propuesta__solicitud__folio__icontains=folio) |
            Q(item_propuesta__propuesta__solicitud__observaciones_solicitud__icontains=folio)
        )
    
    if clave_cnis:
        reservas = reservas.filter(
            item_propuesta__producto__clave_cnis__icontains=clave_cnis
        )
    
    if institucion_id:
        reservas = reservas.filter(
            item_propuesta__propuesta__solicitud__institucion_solicitante_id=institucion_id
        )
    
    if estado_propuesta:
        reservas = reservas.filter(
            item_propuesta__propuesta__estado=estado_propuesta
        )

    reservas = reservas.order_by('-fecha_asignacion', 'item_propuesta__propuesta__solicitud__folio')

    # Paginación en BD: solo se materializan 50 filas por petición.
    paginator = Paginator(reservas, 50)
    page = request.GET.get('page', 1)
    try:
        datos_paginados = paginator.page(page)
    except PageNotAnInteger:
        datos_paginados = paginator.page(1)
    except EmptyPage:
        datos_paginados = paginator.page(paginator.num_pages)

    rows = list(datos_paginados.object_list)
    lote_ids = {r.lote_ubicacion.lote_id for r in rows}
    lu_ids = {r.lote_ubicacion_id for r in rows}
    totales_lote, totales_lu = _totales_reservas_para_ids(lote_ids, lu_ids)

    offset = (datos_paginados.number - 1) * paginator.per_page
    datos_reporte = []
    for idx, reserva in enumerate(rows):
        propuesta = reserva.item_propuesta.propuesta
        solicitud = propuesta.solicitud
        producto = reserva.item_propuesta.producto
        lote_ubicacion = reserva.lote_ubicacion
        lote = lote_ubicacion.lote
        ubicacion = lote_ubicacion.ubicacion

        if lote.fecha_caducidad:
            dias_caducidad = (lote.fecha_caducidad - timezone.now().date()).days
        else:
            dias_caducidad = None

        datos_reporte.append({
            'id': reserva.id,
            'partida': offset + idx + 1,
            'clave_cnis': producto.clave_cnis,
            'descripcion': producto.descripcion,
            'unidad_medida': producto.unidad_medida if producto.unidad_medida else '',
            'lote': lote.numero_lote,
            'caducidad': lote.fecha_caducidad.strftime('%d/%m/%Y') if lote.fecha_caducidad else '',
            'dias_caducidad': dias_caducidad,
            'cantidad_asignada': reserva.cantidad_asignada,
            'reserva_total_lote': totales_lote.get(lote.id, 0),
            'reserva_total_ubicacion': totales_lu.get(lote_ubicacion.id, 0),
            'cantidad_solicitada': reserva.item_propuesta.cantidad_solicitada,
            'observaciones': solicitud.observaciones_solicitud or '',
            'recurso': solicitud.institucion_solicitante.nombre if solicitud.institucion_solicitante else '',
            'destino': (solicitud.almacen_destino.institucion.nombre or solicitud.almacen_destino.institucion.denominacion) if solicitud.almacen_destino and solicitud.almacen_destino.institucion else '',
            'ubicacion': ubicacion.codigo if ubicacion else '',
            'fecha_reserva': reserva.fecha_asignacion.strftime('%d/%m/%Y %H:%M') if reserva.fecha_asignacion else '',
            'folio': solicitud.observaciones_solicitud or solicitud.folio,
            'fecha_entrega_programada': solicitud.fecha_entrega_programada.strftime('%d/%m/%Y') if solicitud.fecha_entrega_programada else '',
            'estado_propuesta': propuesta.get_estado_display(),
            'estado_propuesta_codigo': propuesta.estado,
            'propuesta_id': propuesta.id,
        })

    datos_paginados.object_list = datos_reporte

    # Obtener instituciones para el filtro
    instituciones = Institucion.objects.all().order_by('nombre')
    
    # Estados de propuesta para el filtro
    estados_propuesta = [
        ('GENERADA', 'Generada'),
        ('REVISADA', 'Revisada'),
        ('EN_SURTIMIENTO', 'En Surtimiento'),
        ('SURTIDA', 'Surtida'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    context = {
        'datos': datos_paginados,
        'total_registros': paginator.count,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'folio': folio,
        'clave_cnis': clave_cnis,
        'institucion_id': institucion_id,
        'estado_propuesta': estado_propuesta,
        'instituciones': instituciones,
        'estados_propuesta': estados_propuesta,
        'aviso_fecha': aviso_fecha,
    }
    
    return render(request, 'inventario/reportes_salidas/reporte_reservas.html', context)


@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Supervisor')
@require_http_methods(["POST"])
@transaction.atomic
def liberar_reserva(request, reserva_id):
    """
    Libera una reserva específica (LoteAsignado).
    Elimina el LoteAsignado y libera la cantidad reservada.
    """
    try:
        reserva = get_object_or_404(
            LoteAsignado.objects.select_related(
                'lote_ubicacion__lote',
                'item_propuesta__propuesta'
            ),
            id=reserva_id,
            surtido=False  # Solo se pueden liberar reservas no surtidas
        )
        
        propuesta = reserva.item_propuesta.propuesta
        
        # Verificar que la propuesta esté en un estado que permita liberar
        estados_liberables = ['GENERADA', 'REVISADA', 'EN_SURTIMIENTO']
        if propuesta.estado not in estados_liberables:
            return JsonResponse({
                'exito': False,
                'mensaje': f'No se puede liberar la reserva. La propuesta está en estado "{propuesta.get_estado_display()}"'
            }, status=400)
        
        lote_ubicacion = reserva.lote_ubicacion
        lote = lote_ubicacion.lote
        cantidad_liberar = reserva.cantidad_asignada
        item_propuesta = reserva.item_propuesta  # Guardar referencia antes de eliminar
        propuesta = reserva.item_propuesta.propuesta
        solicitud = propuesta.solicitud if propuesta else None
        
        # Obtener cantidades antes de liberar para el movimiento
        cantidad_disponible_anterior = lote.cantidad_disponible
        cantidad_reservada_anterior = lote_ubicacion.cantidad_reservada
        
        # Liberar la cantidad reservada
        resultado_liberacion = liberar_cantidad_lote(lote_ubicacion, cantidad_liberar)
        
        # Refrescar para obtener valores actualizados
        lote_ubicacion.refresh_from_db()
        lote.refresh_from_db()
        
        # Crear movimiento de inventario para registrar la liberación
        # Nota: La cantidad disponible no cambia al liberar una reserva,
        # solo se libera la cantidad reservada, pero registramos el movimiento para auditoría
        MovimientoInventario.objects.create(
            lote=lote,
            tipo_movimiento='AJUSTE_POSITIVO',
            cantidad=cantidad_liberar,
            cantidad_anterior=cantidad_disponible_anterior,
            cantidad_nueva=cantidad_disponible_anterior,  # La cantidad disponible no cambia al liberar reserva
            motivo=f"Liberación de reserva - Se liberaron {cantidad_liberar} unidades reservadas. Propuesta: {propuesta.id.hex[:8] if propuesta else 'N/A'}, Folio: {solicitud.folio if solicitud and solicitud.folio else 'N/A'}",
            documento_referencia=solicitud.folio if solicitud and solicitud.folio else '',
            pedido=solicitud.folio if solicitud and solicitud.folio else '',
            folio=str(propuesta.id) if propuesta else '',
            institucion_destino=solicitud.institucion_solicitante if solicitud else None,
            usuario=request.user
        )
        
        # Eliminar el LoteAsignado
        reserva.delete()
        
        # Actualizar cantidad_propuesta del item si es necesario
        item_propuesta.refresh_from_db()
        
        # Recalcular cantidad_propuesta sumando las cantidades asignadas restantes (excluyendo la que se eliminó)
        cantidad_restante = item_propuesta.lotes_asignados.filter(surtido=False).aggregate(
            total=Sum('cantidad_asignada')
        )['total'] or 0
        
        item_propuesta.cantidad_propuesta = cantidad_restante
        item_propuesta.save(update_fields=['cantidad_propuesta'])
        
        messages.success(
            request,
            f'Reserva liberada exitosamente. Se liberaron {cantidad_liberar} unidades del lote {lote_ubicacion.lote.numero_lote}'
        )
        
        return JsonResponse({
            'exito': True,
            'mensaje': f'Reserva liberada exitosamente. Se liberaron {cantidad_liberar} unidades.',
            'cantidad_liberada': cantidad_liberar,
            'lote': lote_ubicacion.lote.numero_lote
        })
        
    except LoteAsignado.DoesNotExist:
        return JsonResponse({
            'exito': False,
            'mensaje': 'La reserva no existe o ya fue surtida'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'mensaje': f'Error al liberar la reserva: {str(e)}'
        }, status=500)


@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista', 'Supervisor')
def exportar_reservas_excel(request):
    """
    Exporta el reporte de reservas a Excel.
    Misma lógica de cantidades que reporte_reservas (suma LoteAsignado, no campo en lote).
    Mismo rango de fechas (7 días por defecto, máximo 15 días desde fecha inicial).
    """
    rango = _rango_fechas_reporte_reservas(request)
    folio = request.GET.get('folio', '').strip()
    clave_cnis = request.GET.get('clave_cnis', '').strip()
    institucion_id = request.GET.get('institucion')
    estado_propuesta = request.GET.get('estado_propuesta', '')
    
    # Obtener reservas (misma lógica que la vista)
    reservas = LoteAsignado.objects.filter(
        surtido=False
    ).select_related(
        'item_propuesta__propuesta__solicitud',
        'item_propuesta__propuesta__solicitud__institucion_solicitante',
        'item_propuesta__propuesta__solicitud__almacen_destino',
        'item_propuesta__propuesta__solicitud__almacen_destino__institucion',
        'item_propuesta__producto',
        'lote_ubicacion__lote',
        'lote_ubicacion__lote__producto',
        'lote_ubicacion__ubicacion'
    )

    reservas = reservas.filter(
        fecha_asignacion__gte=rango['start_dt'],
        fecha_asignacion__lte=rango['end_dt'],
    )

    if folio:
        reservas = reservas.filter(
            Q(item_propuesta__propuesta__solicitud__folio__icontains=folio) |
            Q(item_propuesta__propuesta__solicitud__observaciones_solicitud__icontains=folio)
        )
    
    if clave_cnis:
        reservas = reservas.filter(
            item_propuesta__producto__clave_cnis__icontains=clave_cnis
        )
    
    if institucion_id:
        reservas = reservas.filter(
            item_propuesta__propuesta__solicitud__institucion_solicitante_id=institucion_id
        )
    
    if estado_propuesta:
        reservas = reservas.filter(
            item_propuesta__propuesta__estado=estado_propuesta
        )

    reservas = reservas.order_by('-fecha_asignacion', 'item_propuesta__propuesta__solicitud__folio')
    totales_lote, totales_lu = _mapas_totales_reservas_activas()

    headers = [
        'PARTIDA', 'CLAVE CNIS', 'DESCRIPCIÓN', 'UNIDAD DE MEDIDA', 'LOTE', 'CADUCIDAD',
        'ASIGNADA (LÍNEA)', 'RESERVA TOTAL (LOTE)', 'RESERVA TOTAL (UBICACIÓN)',
        'CANTIDAD SOLICITADA', 'OBSERVACIONES', 'RECURSO', 'DESTINO',
        'UBICACIÓN', 'FECHA RESERVA', 'FOLIO', 'FECHA ENTREGA PROGRAMADA', 'ESTADO PROPUESTA'
    ]

    # write_only + append: evita miles de objetos Cell/Style (lo que disparaba CPU y memoria).
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title='Reservas', index=0)
    ws.append(headers)

    partida_counter = 1
    for reserva in reservas.iterator(chunk_size=500):
        propuesta = reserva.item_propuesta.propuesta
        solicitud = propuesta.solicitud
        producto = reserva.item_propuesta.producto
        lote_ubicacion = reserva.lote_ubicacion
        lote = lote_ubicacion.lote
        ubicacion = lote_ubicacion.ubicacion

        destino = ''
        if solicitud.almacen_destino and solicitud.almacen_destino.institucion:
            inst = solicitud.almacen_destino.institucion
            destino = inst.nombre or inst.denominacion or ''

        ws.append([
            partida_counter,
            producto.clave_cnis,
            producto.descripcion,
            producto.unidad_medida or '',
            lote.numero_lote,
            lote.fecha_caducidad.strftime('%d/%m/%Y') if lote.fecha_caducidad else '',
            reserva.cantidad_asignada,
            totales_lote.get(lote.id, 0),
            totales_lu.get(lote_ubicacion.id, 0),
            reserva.item_propuesta.cantidad_solicitada,
            solicitud.observaciones_solicitud or '',
            solicitud.institucion_solicitante.nombre if solicitud.institucion_solicitante else '',
            destino,
            ubicacion.codigo if ubicacion else '',
            reserva.fecha_asignacion.strftime('%d/%m/%Y %H:%M') if reserva.fecha_asignacion else '',
            solicitud.observaciones_solicitud or solicitud.folio,
            solicitud.fecha_entrega_programada.strftime('%d/%m/%Y') if solicitud.fecha_entrega_programada else '',
            propuesta.get_estado_display(),
        ])
        partida_counter += 1

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"reporte_reservas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response
