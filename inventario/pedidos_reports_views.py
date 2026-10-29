"""
Vistas para reportes de errores en carga masiva de pedidos
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q, F, Value, CharField, Sum, Subquery, OuterRef, IntegerField
from django.db.models.functions import Concat, Coalesce
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta, datetime, time as dt_time, date
from .pedidos_models import LogErrorPedido, SolicitudPedido, ItemSolicitud, PropuestaPedido, ItemPropuesta, LoteAsignado
from .pedidos_utils import obtener_resumen_errores
from .models import Producto, Institucion, Almacen
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from collections import defaultdict
import re


@login_required
def reporte_errores_pedidos(request):
    """
    Muestra un reporte de los errores en carga masiva de pedidos.
    Permite filtrar por fecha, tipo de error, institución, etc.
    """
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    tipo_error = request.GET.get('tipo_error')
    institucion = request.GET.get('institucion')
    clave_solicitada = request.GET.get('clave_solicitada')
    filtro_pedido = request.GET.get('pedido', '').strip()
    
    # Base queryset
    errores = LogErrorPedido.objects.select_related(
        'usuario', 'institucion', 'almacen'
    ).all()
    
    # Aplicar filtros
    if fecha_inicio:
        from datetime import datetime
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        errores = errores.filter(fecha_error__gte=fecha_inicio_dt)
    
    if fecha_fin:
        from datetime import datetime
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        fecha_fin_dt = fecha_fin_dt.replace(hour=23, minute=59, second=59)
        errores = errores.filter(fecha_error__lte=fecha_fin_dt)
    
    if tipo_error:
        errores = errores.filter(tipo_error=tipo_error)
    
    if institucion:
        errores = errores.filter(institucion__id=institucion)
    
    if clave_solicitada:
        errores = errores.filter(clave_solicitada__icontains=clave_solicitada)
    
    # Obtener resumen
    resumen = obtener_resumen_errores(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipo_error=tipo_error
    )
    
    # Estadísticas generales
    total_errores = errores.count()
    errores_hoy = errores.filter(
        fecha_error__date=timezone.now().date()
    ).count()
    errores_semana = errores.filter(
        fecha_error__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Errores sin alerta
    errores_sin_alerta = errores.filter(alerta_enviada=False).count()
    
    # Claves más frecuentes con error
    claves_frecuentes = errores.values('clave_solicitada').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Tipos de error más frecuentes
    tipos_frecuentes = errores.values('tipo_error').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Instituciones con más errores
    instituciones_frecuentes = errores.values(
        'institucion__nombre'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Usuarios con más errores
    usuarios_frecuentes = errores.values(
        'usuario__username'
    ).annotate(
        nombre_completo=Concat(
            F('usuario__first_name'), Value(' '), F('usuario__last_name'),
            output_field=CharField()
        ),
        count=Count('id')
    ).order_by('-count')[:10]

    # Obtener folio del pedido (observaciones_solicitud) para cada error
    # Si hay filtro por pedido, procesar más registros para poder filtrar
    limite = 500 if filtro_pedido else 100
    errores_lista = list(errores[:limite])
    errores_con_folio = []
    for error in errores_lista:
        folio_pedido = _obtener_folio_pedido_para_error(error)
        folio_str = folio_pedido or '-'
        errores_con_folio.append({'error': error, 'folio_pedido': folio_str})
    # Aplicar filtro por pedido (folio) si está activo
    if filtro_pedido:
        termino = filtro_pedido.lower()
        errores_con_folio = [x for x in errores_con_folio if termino in (x['folio_pedido'] or '').lower()]
    errores_con_folio = errores_con_folio[:100]
    
    # Instituciones para filtro
    instituciones = Institucion.objects.filter(activo=True).order_by('denominacion')

    context = {
        'errores': [x['error'] for x in errores_con_folio],
        'errores_con_folio': errores_con_folio,
        'total_errores': total_errores,
        'errores_hoy': errores_hoy,
        'errores_semana': errores_semana,
        'errores_sin_alerta': errores_sin_alerta,
        'claves_frecuentes': claves_frecuentes,
        'tipos_frecuentes': tipos_frecuentes,
        'instituciones_frecuentes': instituciones_frecuentes,
        'usuarios_frecuentes': usuarios_frecuentes,
        'resumen': resumen,
        'errores_por_tipo': resumen.get('errores_por_tipo', {}),
        'alertas_enviadas': errores.filter(alerta_enviada=True).count(),
        'tipo_error_choices': LogErrorPedido.TIPO_ERROR_CHOICES,
        'instituciones': instituciones,
        'filtro_pedido': filtro_pedido,
        'filtro_institucion': institucion,
        'page_title': 'Reporte de Errores en Carga Masiva de Pedidos'
    }
    
    return render(request, 'inventario/pedidos/reporte_errores_pedidos.html', context)


def _obtener_folio_pedido_para_error(error):
    """
    Busca la solicitud relacionada con el error y retorna el folio del pedido
    (observaciones_solicitud). Se busca por clave+usuario+fecha.
    """
    try:
        producto = Producto.objects.get(clave_cnis=error.clave_solicitada)
        fecha_inicio = error.fecha_error - timedelta(hours=24)
        fecha_fin = error.fecha_error + timedelta(hours=1)
        items = ItemSolicitud.objects.filter(
            producto=producto,
            solicitud__fecha_solicitud__gte=fecha_inicio,
            solicitud__fecha_solicitud__lte=fecha_fin
        ).select_related('solicitud').order_by('-solicitud__fecha_solicitud')
        if error.usuario:
            items = items.filter(solicitud__usuario_solicitante=error.usuario)
        item = items.first()
        if item and item.solicitud:
            return (item.solicitud.observaciones_solicitud or '').strip() or (item.solicitud.folio or '')
    except Producto.DoesNotExist:
        if error.usuario:
            solicitud = SolicitudPedido.objects.filter(
                usuario_solicitante=error.usuario,
                fecha_solicitud__gte=error.fecha_error - timedelta(hours=24),
                fecha_solicitud__lte=error.fecha_error + timedelta(hours=1)
            ).order_by('-fecha_solicitud').first()
            if solicitud:
                return (solicitud.observaciones_solicitud or '').strip() or (solicitud.folio or '')
    return None


_MAX_ITEMS_NO_SURTIDOS_EXCEL = 15000
_DIAS_DEFAULT_ITEMS_NO_SURTIDOS = 30


def _subquery_cantidad_surtida_item_propuesta():
    """Suma LoteAsignado.surtido=True del ItemPropuesta (misma regla que el reporte original)."""
    return (
        LoteAsignado.objects.filter(
            item_propuesta_id=OuterRef('pk'),
            surtido=True,
        )
        .values('item_propuesta_id')
        .annotate(total=Sum('cantidad_asignada'))
        .values('total')[:1]
    )


def _queryset_items_no_surtidos(request):
    """
    ItemPropuesta no surtidos / parciales filtrados en SQL.

    Antes: cargaba TODAS las propuestas y por cada item hacía aggregate a LoteAsignado
    (N+1), sin tope de fechas → saturaba CPU/RAM.

    Ahora: subquery de surtido, filtro cantidad_surtida < cantidad_propuesta en BD,
    ventana por defecto de 30 días sobre fecha de solicitud.
    """
    estado_propuesta = (request.GET.get('estado') or '').strip()
    institucion_id = (request.GET.get('institucion') or '').strip()
    folio = (request.GET.get('folio') or '').strip()
    clave_cnis = (request.GET.get('clave_cnis') or '').strip()
    fecha_inicio = (request.GET.get('fecha_inicio') or '').strip()
    fecha_fin = (request.GET.get('fecha_fin') or '').strip()

    filtro_default_aplicado = False

    def _pf(v):
        if not v:
            return None
        try:
            return datetime.strptime(v.strip(), '%Y-%m-%d').date()
        except (ValueError, AttributeError):
            return None

    fi = _pf(fecha_inicio)
    ff = _pf(fecha_fin)
    if not fi and not ff and not folio and not clave_cnis:
        ff = timezone.localdate()
        fi = ff - timedelta(days=_DIAS_DEFAULT_ITEMS_NO_SURTIDOS)
        fecha_inicio = fi.isoformat()
        fecha_fin = ff.isoformat()
        filtro_default_aplicado = True

    qs = (
        ItemPropuesta.objects.filter(
            cantidad_propuesta__gt=0,
            propuesta__solicitud__isnull=False,
        )
        .select_related(
            'propuesta',
            'propuesta__solicitud',
            'propuesta__solicitud__institucion_solicitante',
            'propuesta__solicitud__almacen_destino',
            'producto',
        )
        .annotate(
            cantidad_surtida_real=Coalesce(
                Subquery(_subquery_cantidad_surtida_item_propuesta(), output_field=IntegerField()),
                Value(0),
            )
        )
        .filter(cantidad_surtida_real__lt=F('cantidad_propuesta'))
        .order_by('-propuesta__fecha_generacion', 'producto__clave_cnis')
    )

    if estado_propuesta:
        qs = qs.filter(propuesta__estado=estado_propuesta)
    if institucion_id.isdigit():
        qs = qs.filter(propuesta__solicitud__institucion_solicitante_id=int(institucion_id))
    if folio:
        qs = qs.filter(
            Q(propuesta__solicitud__folio__icontains=folio)
            | Q(propuesta__solicitud__observaciones_solicitud__icontains=folio)
        )
    if clave_cnis:
        qs = qs.filter(producto__clave_cnis__icontains=clave_cnis)
    if fi:
        qs = qs.filter(propuesta__solicitud__fecha_solicitud__date__gte=fi)
    if ff:
        qs = qs.filter(propuesta__solicitud__fecha_solicitud__date__lte=ff)

    meta = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'filtro_default_aplicado': filtro_default_aplicado,
        'filtro_estado': estado_propuesta,
        'filtro_institucion': institucion_id,
        'filtro_folio': folio,
        'filtro_clave': clave_cnis,
    }
    return qs, meta


def _fila_item_no_surtido(item):
    """Dict compatible con la plantilla / Excel del reporte."""
    propuesta = item.propuesta
    solicitud = propuesta.solicitud if propuesta else None
    institucion = solicitud.institucion_solicitante if solicitud else None
    almacen = solicitud.almacen_destino if solicitud else None
    surtida = int(getattr(item, 'cantidad_surtida_real', 0) or 0)
    propuesta_cant = int(item.cantidad_propuesta or 0)
    return {
        'propuesta': propuesta,
        'item': item,
        'producto': item.producto,
        'folio_pedido': (
            ((solicitud.observaciones_solicitud or '').strip() or (solicitud.folio or ''))
            if solicitud else ''
        ),
        'institucion': institucion.denominacion if institucion else '-',
        'almacen': almacen.nombre if almacen else '-',
        'clues': institucion.clue if institucion else '-',
        'fecha_solicitud': (
            solicitud.fecha_solicitud.strftime('%d/%m/%Y')
            if solicitud and solicitud.fecha_solicitud else '-'
        ),
        'cantidad_propuesta': propuesta_cant,
        'cantidad_surtida': surtida,
        'cantidad_faltante': max(0, propuesta_cant - surtida),
        'estado_propuesta': propuesta.get_estado_display() if propuesta else '',
    }


def _obtener_items_no_surtidos(request, limit=None):
    """Lista de dicts para Excel (con tope opcional). Preferir queryset + paginación en la vista."""
    qs, meta = _queryset_items_no_surtidos(request)
    if limit is not None:
        qs = qs[:limit]
    return [_fila_item_no_surtido(item) for item in qs], meta


@login_required
def reporte_items_no_surtidos(request):
    """
    Items no surtidos o parciales: cantidad surtida (LoteAsignado surtido) < cantidad propuesta.
    """
    qs, meta = _queryset_items_no_surtidos(request)
    paginator = Paginator(qs, 25)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    filas = [_fila_item_no_surtido(item) for item in page_obj.object_list]
    # Reusar page_obj para controles de paginación, pero la tabla itera filas dict
    page_obj.object_list = filas

    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    query_string = params.urlencode()

    context = {
        'items_no_surtidos': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_items': paginator.count,
        'is_paginated': paginator.num_pages > 1,
        'query_string': query_string,
        'instituciones': Institucion.objects.filter(activo=True).order_by('denominacion'),
        'filtro_estado': meta['filtro_estado'],
        'filtro_institucion': meta['filtro_institucion'],
        'filtro_folio': meta['filtro_folio'],
        'filtro_clave': meta['filtro_clave'],
        'fecha_inicio': meta['fecha_inicio'],
        'fecha_fin': meta['fecha_fin'],
        'filtro_default_aplicado': meta['filtro_default_aplicado'],
        'estado_choices': PropuestaPedido.ESTADO_CHOICES,
        'page_title': 'Reporte de Items No Surtidos en Propuestas',
    }
    return render(request, 'inventario/pedidos/reporte_items_no_surtidos.html', context)


@login_required
def exportar_items_no_surtidos_excel(request):
    """Exporta el reporte de items no surtidos a Excel respetando los filtros actuales."""
    qs, meta = _queryset_items_no_surtidos(request)
    total = qs.count()
    truncado = total > _MAX_ITEMS_NO_SURTIDOS_EXCEL
    items_no_surtidos = [_fila_item_no_surtido(item) for item in qs[:_MAX_ITEMS_NO_SURTIDOS_EXCEL]]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Items No Surtidos'

    header_fill = PatternFill(start_color='B45F06', end_color='B45F06', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin'),
    )

    headers = [
        'Folio de Pedido',
        'Institución',
        'CLUES',
        'Fecha de Solicitud',
        'Almacén',
        'Clave CNIS',
        'Descripción',
        'Cant. Propuesta',
        'Cant. Surtida',
        'Cant. Faltante',
        'Estado Propuesta',
    ]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = h
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border

    for row_idx, row in enumerate(items_no_surtidos, 2):
        desc = (row['producto'].descripcion or '')[:100] if row['producto'] else ''
        ws.cell(row=row_idx, column=1).value = row['folio_pedido'] or ''
        ws.cell(row=row_idx, column=2).value = row['institucion'] or ''
        ws.cell(row=row_idx, column=3).value = row.get('clues', '') or ''
        ws.cell(row=row_idx, column=4).value = row.get('fecha_solicitud', '') or ''
        ws.cell(row=row_idx, column=5).value = row['almacen'] or ''
        ws.cell(row=row_idx, column=6).value = row['producto'].clave_cnis if row['producto'] else ''
        ws.cell(row=row_idx, column=7).value = desc
        ws.cell(row=row_idx, column=8).value = row['cantidad_propuesta'] or 0
        ws.cell(row=row_idx, column=9).value = row['cantidad_surtida'] or 0
        ws.cell(row=row_idx, column=10).value = row['cantidad_faltante'] or 0
        ws.cell(row=row_idx, column=11).value = row['estado_propuesta'] or ''
        for col in range(1, 12):
            ws.cell(row=row_idx, column=col).border = border
            ws.cell(row=row_idx, column=col).alignment = Alignment(horizontal='left', vertical='center')

    if truncado:
        ws.append([])
        ws.append([
            f'Se exportaron {_MAX_ITEMS_NO_SURTIDOS_EXCEL} de {total} filas. Reduce el rango de fechas.',
        ])

    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['B'].width = 38
    ws.column_dimensions['C'].width = 14
    ws.column_dimensions['D'].width = 18
    ws.column_dimensions['E'].width = 25
    ws.column_dimensions['F'].width = 14
    ws.column_dimensions['G'].width = 45
    ws.column_dimensions['H'].width = 14
    ws.column_dimensions['I'].width = 14
    ws.column_dimensions['J'].width = 14
    ws.column_dimensions['K'].width = 22

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fecha_str = date.today().strftime('%Y%m%d')
    response['Content-Disposition'] = f'attachment; filename="items_no_surtidos_{fecha_str}.xlsx"'
    wb.save(response)
    return response


# Límite de filas para export Excel (evita saturar CPU/memoria en exports masivos)
REPORTE_PEDIDOS_MAX_EXCEL_ROWS = 50000
# Ventana por defecto si no hay fechas (evitar cargar todo el histórico)
REPORTE_PEDIDOS_DIAS_DEFAULT = 30


def _parse_fecha(valor):
    """Parsea YYYY-MM-DD; retorna date o None."""
    if not valor:
        return None
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        return None


def _rango_datetime(fecha_ini, fecha_fin):
    """Convierte fechas a datetime aware [inicio del día, fin del día] en TZ local."""
    tz = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(fecha_ini, dt_time.min), tz) if fecha_ini else None
    fin = timezone.make_aware(datetime.combine(fecha_fin, dt_time.max), tz) if fecha_fin else None
    return inicio, fin


def _subquery_cantidad_surtida():
    """Suma LoteAsignado.surtido=True del item, ligada a la propuesta de esa solicitud."""
    return (
        LoteAsignado.objects.filter(
            surtido=True,
            item_propuesta__item_solicitud_id=OuterRef('pk'),
            item_propuesta__propuesta__solicitud_id=OuterRef('solicitud_id'),
        )
        .values('item_propuesta__item_solicitud_id')
        .annotate(total=Sum('cantidad_asignada'))
        .values('total')[:1]
    )


def _annotar_cantidad_surtida(qs):
    """Aplica Subquery de cantidad surtida solo cuando hace falta (página/Excel)."""
    return qs.annotate(
        cantidad_surtida_calc=Coalesce(
            Subquery(_subquery_cantidad_surtida(), output_field=IntegerField()),
            Value(0),
        )
    )


def _obtener_filtros_reporte_pedidos(request, aplicar_default_fechas=True):
    """
    Queryset de ItemSolicitud (una fila del reporte) con filtros.
    Por defecto limita a los últimos REPORTE_PEDIDOS_DIAS_DEFAULT días
    si no se envían fechas ni búsqueda por folio/clave (evita cargar todo el histórico).
    Sin annotate de surtido (se aplica solo en página/Excel).
    """
    institucion_id = request.GET.get('institucion', '').strip()
    folio = request.GET.get('folio', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()
    clave_cnis = request.GET.get('clave_cnis', '').strip()
    estado = request.GET.get('estado', '').strip()

    fechas_por_defecto = False
    f_inicio = _parse_fecha(fecha_inicio)
    f_fin = _parse_fecha(fecha_fin)

    if aplicar_default_fechas and not f_inicio and not f_fin and not folio and not clave_cnis:
        # Sin fechas ni búsqueda puntual: ventana corta (protege CPU)
        f_fin = timezone.localdate()
        f_inicio = f_fin - timedelta(days=REPORTE_PEDIDOS_DIAS_DEFAULT)
        fecha_inicio = f_inicio.isoformat()
        fecha_fin = f_fin.isoformat()
        fechas_por_defecto = True

    dt_inicio, dt_fin = _rango_datetime(f_inicio, f_fin)

    items = ItemSolicitud.objects.select_related(
        'solicitud',
        'solicitud__institucion_solicitante',
        'solicitud__almacen_destino',
        'producto',
    ).order_by('-solicitud__fecha_solicitud', 'producto__clave_cnis')

    if institucion_id:
        items = items.filter(solicitud__institucion_solicitante_id=institucion_id)
    if folio:
        items = items.filter(
            Q(solicitud__observaciones_solicitud__icontains=folio)
            | Q(solicitud__folio__icontains=folio)
        )
    if dt_inicio:
        items = items.filter(solicitud__fecha_solicitud__gte=dt_inicio)
    if dt_fin:
        items = items.filter(solicitud__fecha_solicitud__lte=dt_fin)
    if clave_cnis:
        items = items.filter(producto__clave_cnis__icontains=clave_cnis)
    if estado:
        items = items.filter(solicitud__estado=estado)

    return items, {
        'filtro_institucion': institucion_id,
        'filtro_folio': folio,
        'filtro_fecha_inicio': fecha_inicio,
        'filtro_fecha_fin': fecha_fin,
        'filtro_clave': clave_cnis,
        'filtro_estado': estado,
        'fechas_por_defecto': fechas_por_defecto,
    }


def _fila_desde_item(item):
    """Construye un dict de fila a partir de un ItemSolicitud ya select_related/annotated."""
    solicitud = item.solicitud
    producto = item.producto
    folio_pedido = (solicitud.observaciones_solicitud or '').strip() or (solicitud.folio or '')
    institucion = solicitud.institucion_solicitante
    return {
        'solicitud': solicitud,
        'item': item,
        'folio_pedido': folio_pedido,
        'folio_sistema': solicitud.folio or '',
        'institucion': institucion.denominacion if institucion else '-',
        'clue': (institucion.ib_clue or '') if institucion else '',
        'almacen': solicitud.almacen_destino.nombre if solicitud.almacen_destino else '-',
        'fecha_solicitud': solicitud.fecha_solicitud,
        'estado': solicitud.get_estado_display(),
        'clave_cnis': producto.clave_cnis if producto else '',
        'descripcion': (producto.descripcion or '')[:100] if producto else '',
        'cantidad_solicitada': item.cantidad_solicitada,
        'cantidad_aprobada': item.cantidad_aprobada,
        'cantidad_surtida': getattr(item, 'cantidad_surtida_calc', 0) or 0,
    }


def _construir_filas_reporte_pedidos(items):
    """Construye filas solo para los items dados (p. ej. página actual)."""
    return [_fila_desde_item(item) for item in items]


@login_required
def reporte_pedidos(request):
    """
    Reporte de pedidos (solicitudes) con filtros: institución, folio, fecha, claves, estado.
    Muestra detalle por item (una fila por producto en cada pedido).
    Paginación en BD; cantidad surtida solo en la página actual.
    """
    items, filtros = _obtener_filtros_reporte_pedidos(request)

    instituciones = Institucion.objects.filter(activo=True).order_by('denominacion')

    # Contadores sin Subquery de surtido (más baratos)
    total_items = items.count()
    total_solicitudes = items.values('solicitud_id').distinct().count()

    paginator = Paginator(items, 25)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Annotate solo la página visible
    page_pks = [obj.pk for obj in page_obj.object_list]
    if page_pks:
        annotated = {
            obj.pk: obj
            for obj in _annotar_cantidad_surtida(
                ItemSolicitud.objects.filter(pk__in=page_pks).select_related(
                    'solicitud',
                    'solicitud__institucion_solicitante',
                    'solicitud__almacen_destino',
                    'producto',
                )
            )
        }
        filas = _construir_filas_reporte_pedidos(
            [annotated[pk] for pk in page_pks if pk in annotated]
        )
    else:
        filas = []

    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    # Si aplicamos fechas por defecto, reflejarlas en query de paginación/export
    if filtros.get('fechas_por_defecto'):
        params['fecha_inicio'] = filtros['filtro_fecha_inicio']
        params['fecha_fin'] = filtros['filtro_fecha_fin']
    query_string = params.urlencode()

    context = {
        'filas': filas,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_items': total_items,
        'total_solicitudes': total_solicitudes,
        'is_paginated': paginator.num_pages > 1,
        'query_string': query_string,
        'instituciones': instituciones,
        'estado_choices': SolicitudPedido.ESTADO_CHOICES,
        'page_title': 'Reporte de Pedidos',
        **filtros,
    }
    return render(request, 'inventario/pedidos/reporte_pedidos.html', context)


@login_required
def exportar_reporte_pedidos_excel(request):
    """Exporta el reporte de pedidos a Excel (write_only + iterator)."""
    items, _filtros = _obtener_filtros_reporte_pedidos(request)

    total = items.count()
    if total > REPORTE_PEDIDOS_MAX_EXCEL_ROWS:
        return HttpResponse(
            f'El resultado tiene {total:,} filas. '
            f'El máximo para exportar es {REPORTE_PEDIDOS_MAX_EXCEL_ROWS:,}. '
            'Reduce el rango de fechas u otros filtros e inténtalo de nuevo.',
            status=400,
            content_type='text/plain; charset=utf-8',
        )

    items = _annotar_cantidad_surtida(items)

    wb = openpyxl.Workbook(write_only=True)
    ws = wb.create_sheet(title='Reporte de Pedidos')

    headers = [
        'Folio de Pedido',
        'Folio Sistema',
        'Institución',
        'CLUE IB',
        'Almacén',
        'Fecha Solicitud',
        'Estado',
        'Clave CNIS',
        'Descripción',
        'Cant. Solicitada',
        'Cant. Aprobada',
        'Cant. Suministrada',
    ]
    ws.append(headers)

    for item in items.iterator(chunk_size=2000):
        f = _fila_desde_item(item)
        ws.append([
            f['folio_pedido'] or '',
            f['folio_sistema'] or '',
            f['institucion'] or '',
            f.get('clue') or '',
            f['almacen'] or '',
            f['fecha_solicitud'].strftime('%d/%m/%Y %H:%M') if f['fecha_solicitud'] else '',
            f['estado'] or '',
            f['clave_cnis'] or '',
            f['descripcion'] or '',
            f['cantidad_solicitada'] or 0,
            f['cantidad_aprobada'] or 0,
            f.get('cantidad_surtida', 0) or 0,
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fecha_str = date.today().strftime('%Y%m%d')
    response['Content-Disposition'] = f'attachment; filename="reporte_pedidos_{fecha_str}.xlsx"'
    wb.save(response)
    return response


def _obtener_claves_sin_existencia_queryset(request):
    """Base queryset de errores SIN_EXISTENCIA con filtros fecha_inicio, fecha_fin, clave_solicitada."""
    from datetime import datetime, time as dt_time
    qs = LogErrorPedido.objects.filter(
        tipo_error='SIN_EXISTENCIA'
    ).select_related('usuario', 'institucion').order_by('-fecha_error')
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()
    clave_solicitada = request.GET.get('clave_solicitada', '').strip()
    if fecha_inicio:
        try:
            qs = qs.filter(fecha_error__gte=datetime.strptime(fecha_inicio, '%Y-%m-%d'))
        except ValueError:
            pass
    if fecha_fin:
        try:
            fh = datetime.strptime(fecha_fin, '%Y-%m-%d')
            qs = qs.filter(fecha_error__lte=datetime.combine(fh.date(), dt_time.max))
        except ValueError:
            pass
    if clave_solicitada:
        qs = qs.filter(clave_solicitada__icontains=clave_solicitada)
    return qs


@login_required
def reporte_claves_sin_existencia(request):
    """
    Muestra un reporte de claves solicitadas sin existencia.
    Útil para que el área médica genere oficios de solicitud.
    """
    errores_sin_existencia = _obtener_claves_sin_existencia_queryset(request)
    # Agrupar por clave
    from .models import Producto
    claves_sin_existencia = {}
    for error in errores_sin_existencia:
        if error.clave_solicitada not in claves_sin_existencia:
            descripcion = 'Producto no encontrado'
            try:
                producto = Producto.objects.get(clave_cnis=error.clave_solicitada)
                descripcion = producto.descripcion
            except Producto.DoesNotExist:
                pass
            
            claves_sin_existencia[error.clave_solicitada] = {
                'clave': error.clave_solicitada,
                'descripcion': descripcion,
                'total_solicitudes': 0,
                'cantidad_total': 0,
                'instituciones': set(),
                'ultimos_errores': []
            }
        
        claves_sin_existencia[error.clave_solicitada]['total_solicitudes'] += 1
        claves_sin_existencia[error.clave_solicitada]['cantidad_total'] += error.cantidad_solicitada or 0
        if error.institucion:
            claves_sin_existencia[error.clave_solicitada]['instituciones'].add(
                error.institucion.nombre
            )
        claves_sin_existencia[error.clave_solicitada]['ultimos_errores'].append(error)
    
    # Convertir instituciones a lista
    for clave_data in claves_sin_existencia.values():
        clave_data['instituciones'] = list(clave_data['instituciones'])
        clave_data['ultimos_errores'] = clave_data['ultimos_errores'][:5]
    lista_ordenada = sorted(
        claves_sin_existencia.values(),
        key=lambda x: x['total_solicitudes'],
        reverse=True
    )
    total_solicitudes = sum(c['total_solicitudes'] for c in lista_ordenada)
    cantidad_total = sum(c['cantidad_total'] for c in lista_ordenada)
    context = {
        'claves_sin_existencia': lista_ordenada,
        'total_claves': len(claves_sin_existencia),
        'total_solicitudes': total_solicitudes,
        'cantidad_total': cantidad_total,
        'page_title': 'Reporte de Claves sin Existencia'
    }
    return render(request, 'inventario/pedidos/reporte_claves_sin_existencia.html', context)


# Tope de seguridad: evita saturar Gunicorn si alguien abre un rango enorme.
_MAX_ERRORES_PEDIDOS_SIN_EXISTENCIA = 15000
_DIAS_DEFAULT_PEDIDOS_SIN_EXISTENCIA = 30
_RE_FOLIO_EN_DESCRIPCION = re.compile(
    r'solicitud\s+([A-Za-z0-9][A-Za-z0-9._\-/]*)',
    re.IGNORECASE,
)


def _parse_fecha_ymd(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor.strip(), '%Y-%m-%d').date()
    except (ValueError, AttributeError):
        return None


def _folios_pedido_bulk(errores, productos_por_clave):
    """
    Resuelve folio de pedido (observaciones_solicitud / folio) en bloque.
    1) Extrae folio de descripcion_error cuando viene en el texto.
    2) Completa el resto con UNA consulta a ItemSolicitud en la ventana de fechas.
    """
    folios = {}
    pendientes = []

    for error in errores:
        texto = error.descripcion_error or ''
        m = _RE_FOLIO_EN_DESCRIPCION.search(texto)
        if m:
            folios[error.id] = m.group(1).rstrip('.')
            continue
        pendientes.append(error)

    if not pendientes:
        return folios

    producto_ids = {
        productos_por_clave[e.clave_solicitada].id
        for e in pendientes
        if e.clave_solicitada in productos_por_clave
    }
    if not producto_ids:
        return folios

    fmin = min(e.fecha_error for e in pendientes) - timedelta(hours=24)
    fmax = max(e.fecha_error for e in pendientes) + timedelta(hours=1)

    items = ItemSolicitud.objects.filter(
        producto_id__in=producto_ids,
        solicitud__fecha_solicitud__gte=fmin,
        solicitud__fecha_solicitud__lte=fmax,
    ).select_related('solicitud')

    indice_usuario = defaultdict(list)
    indice_producto = defaultdict(list)
    for item in items.iterator(chunk_size=2000):
        sol = item.solicitud
        if not sol:
            continue
        folio = (sol.observaciones_solicitud or '').strip() or (sol.folio or '')
        if not folio:
            continue
        fila = (sol.fecha_solicitud, folio)
        indice_usuario[(item.producto_id, sol.usuario_solicitante_id)].append(fila)
        indice_producto[item.producto_id].append(fila)

    for lista in indice_usuario.values():
        lista.sort(key=lambda x: x[0], reverse=True)
    for lista in indice_producto.values():
        lista.sort(key=lambda x: x[0], reverse=True)

    for error in pendientes:
        prod = productos_por_clave.get(error.clave_solicitada)
        if not prod:
            continue
        candidatos = indice_usuario.get((prod.id, error.usuario_id)) or indice_producto.get(prod.id, [])
        ventana_ini = error.fecha_error - timedelta(hours=24)
        ventana_fin = error.fecha_error + timedelta(hours=1)
        for fecha_sol, folio in candidatos:
            if ventana_ini <= fecha_sol <= ventana_fin:
                folios[error.id] = folio
                break

    return folios


def _construir_pedidos_sin_existencia(request):
    """
    Agrupa LogErrorPedido SIN_EXISTENCIA por destino.

    Antes: por cada error hacía Producto.get + ItemSolicitud.filter (N+1), sin tope de
    fechas → saturaba CPU/RAM y provocaba Bad Gateway.

    Ahora:
    - Usa institucion/almacen ya guardados en el log (sin reconstruir la solicitud por fila).
    - Por defecto limita a los últimos 30 días si no hay fechas.
    - Carga descripciones y folios en bloque.
    """
    fecha_inicio = (request.GET.get('fecha_inicio') or '').strip()
    fecha_fin = (request.GET.get('fecha_fin') or '').strip()
    institucion_id = (request.GET.get('institucion') or '').strip()
    almacen_id = (request.GET.get('almacen') or '').strip()

    filtro_default_aplicado = False
    if not fecha_inicio and not fecha_fin:
        hoy = timezone.localdate()
        fecha_fin = hoy.isoformat()
        fecha_inicio = (hoy - timedelta(days=_DIAS_DEFAULT_PEDIDOS_SIN_EXISTENCIA)).isoformat()
        filtro_default_aplicado = True

    qs = (
        LogErrorPedido.objects.filter(tipo_error='SIN_EXISTENCIA')
        .filter(Q(institucion__isnull=False) | Q(almacen__isnull=False))
        .select_related('usuario', 'institucion', 'almacen')
        .order_by('-fecha_error')
    )

    fi = _parse_fecha_ymd(fecha_inicio)
    ff = _parse_fecha_ymd(fecha_fin)
    if fi:
        qs = qs.filter(fecha_error__date__gte=fi)
    if ff:
        qs = qs.filter(fecha_error__date__lte=ff)
    if institucion_id.isdigit():
        qs = qs.filter(institucion_id=int(institucion_id))
    if almacen_id.isdigit():
        qs = qs.filter(almacen_id=int(almacen_id))

    total_errores_filtrados = qs.count()
    truncado = total_errores_filtrados > _MAX_ERRORES_PEDIDOS_SIN_EXISTENCIA
    errores = list(qs[:_MAX_ERRORES_PEDIDOS_SIN_EXISTENCIA])

    claves = {e.clave_solicitada for e in errores if e.clave_solicitada}
    productos_por_clave = {
        p.clave_cnis: p
        for p in Producto.objects.filter(clave_cnis__in=claves).only('id', 'clave_cnis', 'descripcion')
    }
    folios_por_error = _folios_pedido_bulk(errores, productos_por_clave)

    pedidos_sin_existencia = {}
    for error in errores:
        institucion = error.institucion
        almacen = error.almacen
        institucion_nombre = institucion.denominacion if institucion else 'Sin institución'
        almacen_nombre = almacen.nombre if almacen else 'Sin almacén'
        destino_key = f"{institucion_nombre}|{almacen_nombre}"

        if destino_key not in pedidos_sin_existencia:
            pedidos_sin_existencia[destino_key] = {
                'institucion': institucion_nombre,
                'almacen': almacen_nombre,
                'institucion_obj': institucion,
                'almacen_obj': almacen,
                'total_claves': 0,
                'total_solicitudes': 0,
                'cantidad_total': 0,
                'claves': set(),
                'folios_pedidos': set(),
                'errores': [],
            }

        destino = pedidos_sin_existencia[destino_key]
        destino['total_solicitudes'] += 1
        destino['cantidad_total'] += error.cantidad_solicitada or 0
        destino['claves'].add(error.clave_solicitada)

        folio_pedido = folios_por_error.get(error.id)
        if folio_pedido:
            destino['folios_pedidos'].add(folio_pedido)
        if len(destino['errores']) < 10:
            destino['errores'].append({'error': error, 'folio_pedido': folio_pedido})

    for destino in pedidos_sin_existencia.values():
        claves_ord = sorted(destino['claves'])
        destino['total_claves'] = len(claves_ord)
        destino['claves'] = claves_ord
        destino['claves_detalle'] = [
            {
                'clave': clave,
                'descripcion': (
                    productos_por_clave[clave].descripcion
                    if clave in productos_por_clave
                    else 'Producto no encontrado'
                ),
            }
            for clave in claves_ord
        ]
        destino['folios_pedidos'] = sorted(destino['folios_pedidos'])
        destino['total_folios'] = len(destino['folios_pedidos'])

    destinos = sorted(
        pedidos_sin_existencia.values(),
        key=lambda x: x['total_solicitudes'],
        reverse=True,
    )
    return {
        'destinos': destinos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'institucion_id': institucion_id,
        'almacen_id': almacen_id,
        'filtro_default_aplicado': filtro_default_aplicado,
        'truncado': truncado,
        'total_errores_filtrados': total_errores_filtrados,
        'total_errores_procesados': len(errores),
    }


@login_required
def reporte_pedidos_sin_existencia(request):
    """
    Pedidos con claves sin existencia agrupados por destino (institución y almacén).
    """
    data = _construir_pedidos_sin_existencia(request)
    context = {
        'pedidos_sin_existencia': data['destinos'],
        'total_destinos': len(data['destinos']),
        'instituciones': Institucion.objects.filter(activo=True).order_by('denominacion'),
        'almacenes': Almacen.objects.filter(activo=True).order_by('nombre'),
        'fecha_inicio': data['fecha_inicio'],
        'fecha_fin': data['fecha_fin'],
        'institucion_id': data['institucion_id'],
        'almacen_id': data['almacen_id'],
        'filtro_default_aplicado': data['filtro_default_aplicado'],
        'truncado': data['truncado'],
        'total_errores_filtrados': data['total_errores_filtrados'],
        'total_errores_procesados': data['total_errores_procesados'],
        'page_title': 'Reporte de Pedidos Sin Existencia por Destino',
    }
    return render(request, 'inventario/pedidos/reporte_pedidos_sin_existencia.html', context)


@login_required
def exportar_pedidos_sin_existencia_excel(request):
    """Exporta el reporte de pedidos sin existencia por destino a Excel."""
    data = _construir_pedidos_sin_existencia(request)
    destinos = data['destinos']

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Pedidos Sin Existencia por Destino'

    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin'),
    )

    headers = [
        'Institución Destino',
        'Almacén Destino',
        'Folio(s) Pedido',
        'Total Claves',
        'Total Solicitudes',
        'Cantidad Total Solicitada',
        'Claves Afectadas',
    ]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border

    for row, destino in enumerate(destinos, 2):
        ws.cell(row=row, column=1).value = destino.get('institucion') or 'Sin institución'
        ws.cell(row=row, column=2).value = destino.get('almacen') or 'Sin almacén'
        ws.cell(row=row, column=3).value = ', '.join(destino.get('folios_pedidos') or [])
        ws.cell(row=row, column=4).value = destino.get('total_claves', 0) or 0
        ws.cell(row=row, column=5).value = destino.get('total_solicitudes', 0) or 0
        ws.cell(row=row, column=6).value = destino.get('cantidad_total', 0) or 0
        ws.cell(row=row, column=7).value = ', '.join(destino.get('claves') or [])
        for col in range(1, 8):
            cell = ws.cell(row=row, column=col)
            cell.border = border
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 18
    ws.column_dimensions['F'].width = 25
    ws.column_dimensions['G'].width = 50

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="pedidos_sin_existencia_por_destino.xlsx"'
    wb.save(response)
    return response


@login_required
def exportar_claves_sin_existencia_excel(request):
    """
    Exporta el reporte de claves sin existencia a Excel respetando los mismos filtros (fecha_inicio, fecha_fin, clave_solicitada).
    """
    from datetime import date
    errores_sin_existencia = _obtener_claves_sin_existencia_queryset(request)
    from .models import Producto
    claves_sin_existencia = {}
    for error in errores_sin_existencia:
        if error.clave_solicitada not in claves_sin_existencia:
            descripcion = 'Producto no encontrado'
            try:
                producto = Producto.objects.get(clave_cnis=error.clave_solicitada)
                descripcion = (producto.descripcion or '')[:500]
            except Producto.DoesNotExist:
                pass
            claves_sin_existencia[error.clave_solicitada] = {
                'clave': error.clave_solicitada,
                'descripcion': descripcion,
                'total_solicitudes': 0,
                'cantidad_total': 0,
                'instituciones': set(),
            }
        claves_sin_existencia[error.clave_solicitada]['total_solicitudes'] += 1
        claves_sin_existencia[error.clave_solicitada]['cantidad_total'] += error.cantidad_solicitada or 0
        if error.institucion:
            claves_sin_existencia[error.clave_solicitada]['instituciones'].add(
                error.institucion.nombre or error.institucion.denominacion or ''
            )
    for clave_data in claves_sin_existencia.values():
        clave_data['instituciones'] = ', '.join(sorted(clave_data['instituciones'])) if clave_data['instituciones'] else ''
    
    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Claves Sin Existencia'
    
    # Estilos
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Encabezados
    headers = ['Clave', 'Descripción', 'Cantidad Total Solicitada', 'Total Solicitudes', 'Instituciones', 'Prioridad']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border
    
    # Datos
    for row, clave_data in enumerate(sorted(
        claves_sin_existencia.values(),
        key=lambda x: x['total_solicitudes'],
        reverse=True
    ), 2):
        ws.cell(row=row, column=1).value = clave_data['clave']
        ws.cell(row=row, column=2).value = clave_data['descripcion']
        ws.cell(row=row, column=3).value = clave_data['cantidad_total']
        ws.cell(row=row, column=4).value = clave_data['total_solicitudes']
        ws.cell(row=row, column=5).value = clave_data.get('instituciones', '')
        ws.cell(row=row, column=6).value = ''  # Prioridad: vacío para que lo llene quien corresponda
        for col in range(1, 7):
            cell = ws.cell(row=row, column=col)
            cell.border = border
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 45
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 16
    ws.column_dimensions['E'].width = 35
    ws.column_dimensions['F'].width = 18
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fecha_str = date.today().strftime('%Y%m%d')
    response['Content-Disposition'] = f'attachment; filename="claves_sin_existencia_{fecha_str}.xlsx"'
    wb.save(response)
    
    return response


@login_required
def reporte_claves_no_existen(request):
    """
    Muestra un reporte de claves que no existen en el catálogo.
    Útil para que el área médica genere oficios de solicitud de nuevos productos.
    """
    # Obtener claves que no existen
    errores_no_existen = LogErrorPedido.objects.filter(
        tipo_error='CLAVE_NO_EXISTE'
    ).select_related('usuario', 'institucion').order_by('-fecha_error')
    
    # Agrupar por clave
    claves_no_existen = {}
    for error in errores_no_existen:
        if error.clave_solicitada not in claves_no_existen:
            claves_no_existen[error.clave_solicitada] = {
                'clave': error.clave_solicitada,
                'total_solicitudes': 0,
                'cantidad_total': 0,
                'instituciones': set(),
                'ultimos_errores': []
            }
        
        claves_no_existen[error.clave_solicitada]['total_solicitudes'] += 1
        claves_no_existen[error.clave_solicitada]['cantidad_total'] += error.cantidad_solicitada or 0
        if error.institucion:
            claves_no_existen[error.clave_solicitada]['instituciones'].add(
                error.institucion.nombre
            )
        claves_no_existen[error.clave_solicitada]['ultimos_errores'].append(error)
    
    # Convertir instituciones a lista
    for clave_data in claves_no_existen.values():
        clave_data['instituciones'] = list(clave_data['instituciones'])
        clave_data['ultimos_errores'] = clave_data['ultimos_errores'][:5]
    
    context = {
        'claves_no_existen': sorted(
            claves_no_existen.values(),
            key=lambda x: x['total_solicitudes'],
            reverse=True
        ),
        'total_claves': len(claves_no_existen),
        'page_title': 'Reporte de Claves que no Existen en Catálogo'
    }
    
    return render(request, 'inventario/pedidos/reporte_claves_no_existen.html', context)


# ============================================================================
# REPORTE ENTREGAS POR PEDIDO (Clave, Inventario disponible = cantidad entregada, Lote, F_CAD)
# ============================================================================

def _nombre_proveedor_lote(lote):
    """Razón social de la orden de suministro; si no hay, el texto guardado en el lote."""
    if not lote:
        return '-'
    orden = getattr(lote, 'orden_suministro', None)
    prov = getattr(orden, 'proveedor', None) if orden else None
    nombre = (getattr(prov, 'razon_social', None) or '').strip() if prov else ''
    if nombre:
        return nombre
    texto = (getattr(lote, 'proveedor', None) or '').strip()
    return texto or '-'


def _obtener_filas_entregas_por_pedido(request):
    """
    LoteAsignado con surtido=True; filtros: folio_pedido, institucion, fecha_desde, fecha_hasta, clave.
    Retorna lista de dicts: folio_pedido, institucion, proveedor, fecha_entrega, clave, descripcion,
    inventario_disponible (cantidad entregada), lote, f_cad.
    """
    from datetime import datetime, time as dt_time
    qs = LoteAsignado.objects.filter(
        surtido=True
    ).select_related(
        'item_propuesta__propuesta__solicitud__institucion_solicitante',
        'item_propuesta__producto',
        'lote_ubicacion__lote__orden_suministro__proveedor',
    ).order_by(
        'item_propuesta__propuesta__solicitud__fecha_solicitud',
        'item_propuesta__producto__clave_cnis',
        'lote_ubicacion__lote__numero_lote',
    )
    folio = request.GET.get('folio_pedido', '').strip()
    institucion_id = request.GET.get('institucion', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    clave = request.GET.get('clave', '').strip()
    if folio:
        qs = qs.filter(
            Q(item_propuesta__propuesta__solicitud__observaciones_solicitud__icontains=folio)
            | Q(item_propuesta__propuesta__solicitud__folio__icontains=folio)
        )
    if institucion_id:
        qs = qs.filter(item_propuesta__propuesta__solicitud__institucion_solicitante_id=institucion_id)
    if fecha_desde:
        try:
            fd = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            qs = qs.filter(item_propuesta__propuesta__solicitud__fecha_solicitud__date__gte=fd)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fh = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            qs = qs.filter(item_propuesta__propuesta__solicitud__fecha_solicitud__date__lte=fh)
        except ValueError:
            pass
    if clave:
        qs = qs.filter(item_propuesta__producto__clave_cnis__icontains=clave)
    filas = []
    for la in qs:
        solicitud = la.item_propuesta.propuesta.solicitud if la.item_propuesta and la.item_propuesta.propuesta else None
        prod = la.item_propuesta.producto if la.item_propuesta else None
        lote = la.lote_ubicacion.lote if la.lote_ubicacion else None
        inst = solicitud.institucion_solicitante if solicitud else None
        filas.append({
            'folio_pedido': (solicitud.observaciones_solicitud or '').strip() if solicitud else '-',
            'institucion': (inst.denominacion or getattr(inst, 'nombre', '') or '-') if inst else '-',
            'proveedor': _nombre_proveedor_lote(lote),
            'fecha_entrega': la.fecha_surtimiento or (solicitud.fecha_solicitud if solicitud else None),
            'clave': (prod.clave_cnis or '-') if prod else '-',
            'descripcion': ((prod.descripcion or '')[:120]) if prod else '-',
            'inventario_disponible': la.cantidad_asignada,  # cantidad entregada en ese pedido
            'lote': (lote.numero_lote or '-') if lote else '-',
            'f_cad': lote.fecha_caducidad if lote else None,
        })
    return filas


@login_required
def reporte_entregas_por_pedido(request):
    """
    Reporte de entregas por pedido: consulta por folio de pedido, institución, fechas, clave.
    Columnas: Folio pedido, Institución, Proveedor, Fecha entrega, Clave, Descripción, Inventario disponible (cantidad entregada), Lote, F_CAD.
    """
    instituciones = Institucion.objects.filter(activo=True).order_by('denominacion')
    filas = _obtener_filas_entregas_por_pedido(request)
    paginator = Paginator(filas, 25)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    query_string = params.urlencode()
    try:
        selected_institucion_id = int(request.GET.get('institucion', 0)) or None
    except (ValueError, TypeError):
        selected_institucion_id = None
    filtros = {
        'folio_pedido': request.GET.get('folio_pedido', ''),
        'institucion': request.GET.get('institucion', ''),
        'selected_institucion_id': selected_institucion_id,
        'fecha_desde': request.GET.get('fecha_desde', ''),
        'fecha_hasta': request.GET.get('fecha_hasta', ''),
        'clave': request.GET.get('clave', ''),
    }
    context = {
        'filas': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_items': paginator.count,
        'is_paginated': paginator.num_pages > 1,
        'query_string': query_string,
        'instituciones': instituciones,
        'filtros': filtros,
        'page_title': 'Reporte de Entregas por Pedido',
    }
    return render(request, 'inventario/pedidos/reporte_entregas_por_pedido.html', context)


@login_required
def exportar_entregas_por_pedido_excel(request):
    """Exporta el reporte de entregas por pedido a Excel con los mismos filtros."""
    from datetime import date
    filas = _obtener_filas_entregas_por_pedido(request)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Entregas por Pedido'
    header_fill = PatternFill(start_color='2E7D32', end_color='2E7D32', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'),
    )
    headers = [
        'Folio pedido', 'Institución', 'Proveedor', 'Fecha entrega', 'Clave', 'Descripción',
        'Inventario disponible (cant. entregada)', 'Lote', 'F_CAD',
    ]
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=col)
        c.value = h
        c.fill = header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = border
    for row_idx, r in enumerate(filas, 2):
        ws.cell(row=row_idx, column=1).value = r.get('folio_pedido', '')
        ws.cell(row=row_idx, column=2).value = r.get('institucion', '')
        ws.cell(row=row_idx, column=3).value = r.get('proveedor', '')
        fecha = r.get('fecha_entrega')
        ws.cell(row=row_idx, column=4).value = fecha.strftime('%d/%m/%Y %H:%M') if fecha else ''
        ws.cell(row=row_idx, column=5).value = r.get('clave', '')
        ws.cell(row=row_idx, column=6).value = r.get('descripcion', '')
        ws.cell(row=row_idx, column=7).value = r.get('inventario_disponible', 0)
        ws.cell(row=row_idx, column=8).value = r.get('lote', '')
        f_cad = r.get('f_cad')
        ws.cell(row=row_idx, column=9).value = f_cad.strftime('%d/%m/%Y') if f_cad else ''
        for col in range(1, 10):
            ws.cell(row=row_idx, column=col).border = border
    for letra, w in [('A', 22), ('B', 32), ('C', 36), ('D', 18), ('E', 16), ('F', 45), ('G', 22), ('H', 14), ('I', 12)]:
        ws.column_dimensions[letra].width = w
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fecha_str = date.today().strftime('%Y%m%d')
    response['Content-Disposition'] = f'attachment; filename="entregas_por_pedido_{fecha_str}.xlsx"'
    wb.save(response)
    return response


# ============================================================================
# DASHBOARD SURTIMIENTO POR INSTITUCIÓN
# ============================================================================

@login_required
def dashboard_surtimiento_institucion(request):
    """
    Dashboard por institución: productos surtidos completamente, no surtidos y surtidos parcialmente.
    Permite ver gráficas o tablas según selección del usuario.
    """
    from datetime import datetime

    institucion_id = request.GET.get('institucion', '').strip()
    folio_pedido = request.GET.get('folio_pedido', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    vista = request.GET.get('vista', 'graficas')  # 'graficas' | 'tablas'

    instituciones = Institucion.objects.filter(activo=True).order_by('denominacion')

    # Exigir institución O folio de pedido para no procesar todos los pedidos (mejor performance)
    tiene_filtro = bool(institucion_id or folio_pedido)
    surtido_completo = []
    no_surtido = []
    surtido_parcial = []

    def _datos_extra_fila(item):
        solicitud = item.propuesta.solicitud if item.propuesta else None
        inst = solicitud.institucion_solicitante if solicitud else None
        prod = item.producto
        cat = prod.categoria if prod else None
        return {
            'institucion': (inst.denominacion or '-') if inst else '-',
            'entidad': (getattr(inst, 'estado', None) or '-') if inst else '-',
            'categoria_nombre': (cat.nombre or '-') if cat else '-',
            'categoria_descripcion': (getattr(cat, 'descripcion', None) or '-') if cat else '-',
            'categoria_codigo': (getattr(cat, 'codigo', None) or '-') if cat else '-',
            'categoria_tipo': (getattr(cat, 'tipo', None) or '-') if cat else '-',
            'marca': (getattr(prod, 'marca', None) or '-') if prod else '-',
            'fabricante': (getattr(prod, 'fabricante', None) or '-') if prod else '-',
            'fecha_emision': solicitud.fecha_solicitud.strftime('%d/%m/%Y') if solicitud and getattr(solicitud, 'fecha_solicitud', None) else '-',
        }

    if tiene_filtro:
        items = ItemPropuesta.objects.select_related(
            'propuesta__solicitud__institucion_solicitante',
            'producto',
            'producto__categoria',
        ).prefetch_related('lotes_asignados').filter(
            propuesta__solicitud__institucion_solicitante__activo=True,
        ).exclude(propuesta__solicitud__estado='CANCELADA')

        if institucion_id:
            items = items.filter(propuesta__solicitud__institucion_solicitante_id=institucion_id)
        if folio_pedido:
            items = items.filter(propuesta__solicitud__observaciones_solicitud__icontains=folio_pedido)
        if fecha_desde:
            try:
                fd = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                items = items.filter(propuesta__solicitud__fecha_solicitud__date__gte=fd)
            except ValueError:
                pass
        if fecha_hasta:
            try:
                fh = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                items = items.filter(propuesta__solicitud__fecha_solicitud__date__lte=fh)
            except ValueError:
                pass

        for item in items:
            sol = item.cantidad_solicitada or 0
            sur = sum(la.cantidad_asignada for la in item.lotes_asignados.all() if la.surtido)
            extra = _datos_extra_fila(item)
            solicitud = item.propuesta.solicitud if item.propuesta else None
            folio = (solicitud.observaciones_solicitud or solicitud.folio or '').strip() or '-' if solicitud else '-'
            if sur == 0:
                no_surtido.append({
                    'item': item,
                    'cantidad_solicitada': sol,
                    'cantidad_surtida': sur,
                    'diferencia': sol,
                    'folio': folio,
                    **extra,
                })
            elif sur >= sol:
                surtido_completo.append({
                    'item': item,
                    'cantidad_solicitada': sol,
                    'cantidad_surtida': sur,
                    'diferencia': 0,
                    'folio': folio,
                    **extra,
                })
            else:
                surtido_parcial.append({
                    'item': item,
                    'cantidad_solicitada': sol,
                    'cantidad_surtida': sur,
                    'diferencia': sol - sur,
                    'folio': folio,
                    **extra,
                })

    institucion_seleccionada = None
    if institucion_id:
        institucion_seleccionada = Institucion.objects.filter(id=institucion_id).first()

    from urllib.parse import urlencode
    q = request.GET.copy()
    q['vista'] = 'graficas'
    url_graficas = '?' + q.urlencode()
    q['vista'] = 'tablas'
    url_tablas = '?' + q.urlencode()

    context = {
        'instituciones': instituciones,
        'institucion_seleccionada': institucion_seleccionada,
        'filtro_institucion': institucion_id,
        'filtro_folio_pedido': folio_pedido,
        'filtro_fecha_desde': fecha_desde,
        'filtro_fecha_hasta': fecha_hasta,
        'vista': vista,
        'tiene_filtro': tiene_filtro,
        'url_graficas': url_graficas,
        'url_tablas': url_tablas,
        'surtido_completo': surtido_completo,
        'no_surtido': no_surtido,
        'surtido_parcial': surtido_parcial,
        'total_completo': len(surtido_completo),
        'total_no_surtido': len(no_surtido),
        'total_parcial': len(surtido_parcial),
        'page_title': 'Dashboard de Surtimiento por Institución',
    }
    return render(request, 'inventario/pedidos/dashboard_surtimiento_institucion.html', context)


def _obtener_datos_dashboard_surtimiento(request):
    """
    Obtiene las listas surtido_completo, no_surtido, surtido_parcial con los mismos
    filtros que el dashboard (para reutilizar en vista y exportación Excel).
    Retorna (surtido_completo, no_surtido, surtido_parcial) o None si no hay filtro.
    """
    from datetime import datetime

    institucion_id = request.GET.get('institucion', '').strip()
    folio_pedido = request.GET.get('folio_pedido', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    if not (institucion_id or folio_pedido):
        return None

    items = ItemPropuesta.objects.select_related(
        'propuesta__solicitud__institucion_solicitante',
        'producto',
        'producto__categoria',
    ).prefetch_related('lotes_asignados').filter(
        propuesta__solicitud__institucion_solicitante__activo=True,
    ).exclude(propuesta__solicitud__estado='CANCELADA')

    if institucion_id:
        items = items.filter(propuesta__solicitud__institucion_solicitante_id=institucion_id)
    if folio_pedido:
        items = items.filter(propuesta__solicitud__observaciones_solicitud__icontains=folio_pedido)
    if fecha_desde:
        try:
            fd = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            items = items.filter(propuesta__solicitud__fecha_solicitud__date__gte=fd)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fh = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            items = items.filter(propuesta__solicitud__fecha_solicitud__date__lte=fh)
        except ValueError:
            pass

    surtido_completo = []
    no_surtido = []
    surtido_parcial = []

    for item in items:
        sol = item.cantidad_solicitada or 0
        sur = sum(la.cantidad_asignada for la in item.lotes_asignados.all() if la.surtido)
        solicitud = item.propuesta.solicitud if item.propuesta else None
        inst = solicitud.institucion_solicitante if solicitud else None
        prod = item.producto
        cat = prod.categoria if prod else None
        folio = (solicitud.observaciones_solicitud or solicitud.folio or '').strip() or '-' if solicitud else '-'
        clave = (prod.clave_cnis or '-') if prod else '-'
        desc = ((prod.descripcion or '-')[:200]) if prod else '-'
        row = {
            'folio': folio,
            'clave_cnis': clave,
            'descripcion': desc,
            'institucion': (inst.denominacion or '-') if inst else '-',
            'entidad': (getattr(inst, 'estado', None) or '-') if inst else '-',
            'categoria_nombre': (cat.nombre or '-') if cat else '-',
            'categoria_descripcion': (getattr(cat, 'descripcion', None) or '-') if cat else '-',
            'categoria_codigo': (getattr(cat, 'codigo', None) or '-') if cat else '-',
            'categoria_tipo': (getattr(cat, 'tipo', None) or '-') if cat else '-',
            'marca': (getattr(prod, 'marca', None) or '-') if prod else '-',
            'fabricante': (getattr(prod, 'fabricante', None) or '-') if prod else '-',
            'fecha_emision': solicitud.fecha_solicitud.strftime('%d/%m/%Y') if solicitud and getattr(solicitud, 'fecha_solicitud', None) else '-',
            'cantidad_solicitada': sol,
            'cantidad_surtida': sur,
            'diferencia': sol - sur if sur < sol else 0,
        }
        if sur == 0:
            row['diferencia'] = sol
            no_surtido.append(row)
        elif sur >= sol:
            surtido_completo.append(row)
        else:
            row['diferencia'] = sol - sur
            surtido_parcial.append(row)

    return (surtido_completo, no_surtido, surtido_parcial)


def _obtener_datos_dashboard_surtimiento_con_lotes(request):
    """
    Igual que _obtener_datos_dashboard_surtimiento pero genera una fila por cada
    lote asignado (detalle por lote) para revisión detallada. Cada fila incluye
    los mismos campos más 'lote' (numero_lote) y 'cantidad_lote'.
    """
    from datetime import datetime

    institucion_id = request.GET.get('institucion', '').strip()
    folio_pedido = request.GET.get('folio_pedido', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    if not (institucion_id or folio_pedido):
        return None

    items = ItemPropuesta.objects.select_related(
        'propuesta__solicitud__institucion_solicitante',
        'producto',
        'producto__categoria',
    ).prefetch_related('lotes_asignados__lote_ubicacion__lote').filter(
        propuesta__solicitud__institucion_solicitante__activo=True,
    ).exclude(propuesta__solicitud__estado='CANCELADA')

    if institucion_id:
        items = items.filter(propuesta__solicitud__institucion_solicitante_id=institucion_id)
    if folio_pedido:
        items = items.filter(propuesta__solicitud__observaciones_solicitud__icontains=folio_pedido)
    if fecha_desde:
        try:
            fd = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            items = items.filter(propuesta__solicitud__fecha_solicitud__date__gte=fd)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fh = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            items = items.filter(propuesta__solicitud__fecha_solicitud__date__lte=fh)
        except ValueError:
            pass

    surtido_completo = []
    no_surtido = []
    surtido_parcial = []

    for item in items:
        sol = item.cantidad_solicitada or 0
        lotes_list = list(item.lotes_asignados.all())
        sur = sum(la.cantidad_asignada for la in lotes_list if la.surtido)
        solicitud = item.propuesta.solicitud if item.propuesta else None
        inst = solicitud.institucion_solicitante if solicitud else None
        prod = item.producto
        cat = prod.categoria if prod else None
        folio = (solicitud.observaciones_solicitud or solicitud.folio or '').strip() or '-' if solicitud else '-'
        clave = (prod.clave_cnis or '-') if prod else '-'
        desc = ((prod.descripcion or '-')[:200]) if prod else '-'
        base = {
            'folio': folio,
            'clave_cnis': clave,
            'descripcion': desc,
            'institucion': (inst.denominacion or '-') if inst else '-',
            'entidad': (getattr(inst, 'estado', None) or '-') if inst else '-',
            'categoria_nombre': (cat.nombre or '-') if cat else '-',
            'categoria_descripcion': (getattr(cat, 'descripcion', None) or '-') if cat else '-',
            'categoria_codigo': (getattr(cat, 'codigo', None) or '-') if cat else '-',
            'categoria_tipo': (getattr(cat, 'tipo', None) or '-') if cat else '-',
            'marca': (getattr(prod, 'marca', None) or '-') if prod else '-',
            'fabricante': (getattr(prod, 'fabricante', None) or '-') if prod else '-',
            'fecha_emision': solicitud.fecha_solicitud.strftime('%d/%m/%Y') if solicitud and getattr(solicitud, 'fecha_solicitud', None) else '-',
            'cantidad_solicitada': sol,
            'cantidad_surtida': sur,
            'diferencia': sol - sur if sur < sol else 0,
        }
        if sur == 0:
            base['diferencia'] = sol
            lista_destino = no_surtido
        elif sur >= sol:
            lista_destino = surtido_completo
        else:
            base['diferencia'] = sol - sur
            lista_destino = surtido_parcial

        if not lotes_list:
            row = dict(base)
            row['lote'] = '-'
            row['cantidad_lote'] = 0
            lista_destino.append(row)
        else:
            for la in lotes_list:
                row = dict(base)
                row['lote'] = (la.lote_ubicacion.lote.numero_lote or '-') if (getattr(la, 'lote_ubicacion', None) and getattr(la.lote_ubicacion, 'lote', None)) else '-'
                row['cantidad_lote'] = la.cantidad_asignada or 0
                lista_destino.append(row)

    return (surtido_completo, no_surtido, surtido_parcial)


@login_required
def exportar_dashboard_surtimiento_excel(request):
    """Exporta el dashboard de surtimiento a Excel con los mismos filtros (institución o folio obligatorio)."""
    from datetime import date

    datos = _obtener_datos_dashboard_surtimiento(request)
    if datos is None:
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.warning(request, 'Seleccione una institución o un folio de pedido para exportar.')
        return redirect('pedidos:dashboard_surtimiento_institucion')

    surtido_completo, no_surtido, surtido_parcial = datos

    wb = openpyxl.Workbook()
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=11)
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'),
    )

    def escribir_hoja(ws, titulo, filas, color_header='1F4E78'):
        headers = [
            'Folio', 'INSTITUCIÓN', 'ENTIDAD', 'Clave CNIS', 'Descripción',
            'Cat. Nombre', 'Cat. Descripción', 'Cat. Código', 'Cat. Tipo',
            'MARCA', 'FABRICANTE', 'FECHA DE EMISIÓN',
            'PZAS. SOLICITADAS', 'PZAS. ENTREGADAS', 'Diferencia',
        ]
        for col, h in enumerate(headers, 1):
            c = ws.cell(row=1, column=col)
            c.value = h
            c.fill = PatternFill(start_color=color_header, end_color=color_header, fill_type='solid')
            c.font = header_font
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            c.border = border
        for row_idx, r in enumerate(filas, 2):
            ws.cell(row=row_idx, column=1).value = r.get('folio', '')
            ws.cell(row=row_idx, column=2).value = r.get('institucion', '')
            ws.cell(row=row_idx, column=3).value = r.get('entidad', '')
            ws.cell(row=row_idx, column=4).value = r.get('clave_cnis', '')
            ws.cell(row=row_idx, column=5).value = r.get('descripcion', '')
            ws.cell(row=row_idx, column=6).value = r.get('categoria_nombre', '')
            ws.cell(row=row_idx, column=7).value = r.get('categoria_descripcion', '')
            ws.cell(row=row_idx, column=8).value = r.get('categoria_codigo', '')
            ws.cell(row=row_idx, column=9).value = r.get('categoria_tipo', '')
            ws.cell(row=row_idx, column=10).value = r.get('marca', '')
            ws.cell(row=row_idx, column=11).value = r.get('fabricante', '')
            ws.cell(row=row_idx, column=12).value = r.get('fecha_emision', '')
            ws.cell(row=row_idx, column=13).value = r.get('cantidad_solicitada', 0)
            ws.cell(row=row_idx, column=14).value = r.get('cantidad_surtida', 0)
            ws.cell(row=row_idx, column=15).value = r.get('diferencia', 0)
            for col in range(1, 16):
                ws.cell(row=row_idx, column=col).border = border
        for letra, w in [('A', 18), ('B', 28), ('C', 18), ('D', 14), ('E', 50),
                         ('F', 18), ('G', 30), ('H', 12), ('I', 14), ('J', 14),
                         ('K', 18), ('L', 14), ('M', 12), ('N', 12), ('O', 12)]:
            ws.column_dimensions[letra].width = w

    ws1 = wb.active
    ws1.title = 'Surtido completo'
    escribir_hoja(ws1, 'Surtido completo', surtido_completo, '28a745')
    ws2 = wb.create_sheet('No surtido')
    escribir_hoja(ws2, 'No surtido', no_surtido, 'dc3545')
    ws3 = wb.create_sheet('Surtido parcial')
    escribir_hoja(ws3, 'Surtido parcial', surtido_parcial, 'ffc107')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fecha_str = date.today().strftime('%Y%m%d')
    response['Content-Disposition'] = f'attachment; filename="dashboard_surtimiento_{fecha_str}.xlsx"'
    wb.save(response)
    return response


@login_required
def exportar_dashboard_surtimiento_excel_con_lotes(request):
    """
    Exporta el mismo detalle del dashboard de surtimiento pero con una fila por lote
    (campo Lote y Cant. por lote) para revisión detallada. Mismos filtros que el dashboard.
    No modifica el comportamiento del dashboard ni del export estándar.
    """
    from datetime import date

    datos = _obtener_datos_dashboard_surtimiento_con_lotes(request)
    if datos is None:
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.warning(request, 'Seleccione una institución o un folio de pedido para exportar.')
        return redirect('pedidos:dashboard_surtimiento_institucion')

    surtido_completo, no_surtido, surtido_parcial = datos

    wb = openpyxl.Workbook()
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=11)
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'),
    )

    def escribir_hoja_con_lotes(ws, titulo, filas, color_header='1F4E78'):
        headers = [
            'Folio', 'INSTITUCIÓN', 'ENTIDAD', 'Clave CNIS', 'Descripción',
            'Cat. Nombre', 'Cat. Descripción', 'Cat. Código', 'Cat. Tipo',
            'MARCA', 'FABRICANTE', 'FECHA DE EMISIÓN',
            'PZAS. SOLICITADAS', 'PZAS. ENTREGADAS', 'Diferencia',
            'LOTE', 'Cant. por lote',
        ]
        for col, h in enumerate(headers, 1):
            c = ws.cell(row=1, column=col)
            c.value = h
            c.fill = PatternFill(start_color=color_header, end_color=color_header, fill_type='solid')
            c.font = header_font
            c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            c.border = border
        for row_idx, r in enumerate(filas, 2):
            ws.cell(row=row_idx, column=1).value = r.get('folio', '')
            ws.cell(row=row_idx, column=2).value = r.get('institucion', '')
            ws.cell(row=row_idx, column=3).value = r.get('entidad', '')
            ws.cell(row=row_idx, column=4).value = r.get('clave_cnis', '')
            ws.cell(row=row_idx, column=5).value = r.get('descripcion', '')
            ws.cell(row=row_idx, column=6).value = r.get('categoria_nombre', '')
            ws.cell(row=row_idx, column=7).value = r.get('categoria_descripcion', '')
            ws.cell(row=row_idx, column=8).value = r.get('categoria_codigo', '')
            ws.cell(row=row_idx, column=9).value = r.get('categoria_tipo', '')
            ws.cell(row=row_idx, column=10).value = r.get('marca', '')
            ws.cell(row=row_idx, column=11).value = r.get('fabricante', '')
            ws.cell(row=row_idx, column=12).value = r.get('fecha_emision', '')
            ws.cell(row=row_idx, column=13).value = r.get('cantidad_solicitada', 0)
            ws.cell(row=row_idx, column=14).value = r.get('cantidad_surtida', 0)
            ws.cell(row=row_idx, column=15).value = r.get('diferencia', 0)
            ws.cell(row=row_idx, column=16).value = r.get('lote', '')
            ws.cell(row=row_idx, column=17).value = r.get('cantidad_lote', 0)
            for col in range(1, 18):
                ws.cell(row=row_idx, column=col).border = border
        for letra, w in [('A', 18), ('B', 28), ('C', 18), ('D', 14), ('E', 50),
                         ('F', 18), ('G', 30), ('H', 12), ('I', 14), ('J', 14),
                         ('K', 18), ('L', 14), ('M', 12), ('N', 12), ('O', 12),
                         ('P', 14), ('Q', 12)]:
            ws.column_dimensions[letra].width = w

    ws1 = wb.active
    ws1.title = 'Surtido completo'
    escribir_hoja_con_lotes(ws1, 'Surtido completo', surtido_completo, '28a745')
    ws2 = wb.create_sheet('No surtido')
    escribir_hoja_con_lotes(ws2, 'No surtido', no_surtido, 'dc3545')
    ws3 = wb.create_sheet('Surtido parcial')
    escribir_hoja_con_lotes(ws3, 'Surtido parcial', surtido_parcial, 'ffc107')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fecha_str = date.today().strftime('%Y%m%d')
    response['Content-Disposition'] = f'attachment; filename="dashboard_surtimiento_detalle_lotes_{fecha_str}.xlsx"'
    wb.save(response)
    return response
