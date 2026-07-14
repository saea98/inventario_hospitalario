"""
Reporte para solicitudes de información (transparencia / auditorías).

Existencia física al cierre de un mes, filtrable por grupos CNIS (010–040 medicamentos)
y almacenes. Reconstruye stock histórico vía MovimientoInventario (mismo criterio que
el comparativo de inventario).
"""

from calendar import monthrange
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import (
    Case,
    F,
    IntegerField,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook

from .comparativo_inventario_utils import _subquery_existencia_fisica_en_fecha
from .models import Almacen, Lote

# Grupos de cuadro básico más solicitados (medicamentos)
GRUPOS_CNIS_MEDICAMENTOS = ('010', '020', '030', '040')
GRUPOS_CNIS_OPCIONES = [
    ('010', '010 — Medicamentos'),
    ('020', '020 — Medicamentos'),
    ('030', '030 — Medicamentos'),
    ('040', '040 — Medicamentos'),
    ('060', '060 — Material de curación'),
    ('080', '080 — Material'),
    ('130', '130 — Otros'),
]

AGRUPACION_CLAVE_ALMACEN = 'clave_almacen'
AGRUPACION_CLAVE = 'clave'

HEADERS_DETALLE = [
    'Clave de cuadro básico',
    'Descripción completa',
    'Almacén',
    'Institución / CLUES',
    'Piezas al cierre',
    'Fecha de cierre',
]

HEADERS_CONSOLIDADO = [
    'Clave de cuadro básico',
    'Descripción completa',
    'Almacenes con existencia',
    'Piezas totales al cierre',
    'Fecha de cierre',
]

MAX_EXCEL_ROWS = 50000


def _ultimo_dia_mes(anio, mes):
    return date(anio, mes, monthrange(anio, mes)[1])


def _parse_periodo(request):
    """Lee año-mes (input type=month) o fecha_cierre; retorna (fecha_cierre, anio_mes_str)."""
    anio_mes = (request.GET.get('periodo') or '').strip()
    fecha_cierre_str = (request.GET.get('fecha_cierre') or '').strip()

    fecha_cierre = None
    if anio_mes and len(anio_mes) >= 7:
        try:
            anio = int(anio_mes[:4])
            mes = int(anio_mes[5:7])
            if 1 <= mes <= 12:
                fecha_cierre = _ultimo_dia_mes(anio, mes)
                anio_mes = f'{anio:04d}-{mes:02d}'
        except ValueError:
            fecha_cierre = None

    if fecha_cierre is None and fecha_cierre_str:
        try:
            fecha_cierre = date.fromisoformat(fecha_cierre_str)
            anio_mes = f'{fecha_cierre.year:04d}-{fecha_cierre.month:02d}'
        except ValueError:
            fecha_cierre = None

    hoy = timezone.localdate()
    if fecha_cierre and fecha_cierre > hoy:
        fecha_cierre = hoy

    return fecha_cierre, anio_mes


def _grupos_seleccionados(request):
    grupos = [g.strip() for g in request.GET.getlist('grupo') if g.strip()]
    if not grupos and request.GET.get('consultar'):
        # Si consultaron sin marcar grupos: ningún filtro de grupo (todos)
        return []
    if not grupos:
        # Primera carga / sin consulta: preset medicamentos
        return list(GRUPOS_CNIS_MEDICAMENTOS)
    return grupos


def _annotar_existencia_cierre(lotes_qs, fecha_cierre):
    subq = _subquery_existencia_fisica_en_fecha(fecha_cierre)
    existencia_si_recepcion = Case(
        When(fecha_recepcion__lte=fecha_cierre, then=F('cantidad_inicial')),
        default=Value(0),
        output_field=IntegerField(),
    )
    return lotes_qs.annotate(
        exist_cierre=Coalesce(
            Subquery(subq, output_field=IntegerField()),
            existencia_si_recepcion,
            output_field=IntegerField(),
        )
    )


def _queryset_lotes_filtrados(request, fecha_cierre):
    grupos = _grupos_seleccionados(request)
    almacen_ids = [a for a in request.GET.getlist('almacen_id') if a.isdigit()]
    entidad = (request.GET.get('entidad') or '').strip()
    clues = (request.GET.get('clues') or '').strip()
    solo_con_existencia = request.GET.get('solo_existencia') == 'si'

    lotes = Lote.objects.select_related('producto', 'almacen', 'institucion')

    if grupos:
        q_grupos = Q()
        for g in grupos:
            q_grupos |= Q(producto__clave_cnis__startswith=g)
        lotes = lotes.filter(q_grupos)

    if almacen_ids:
        lotes = lotes.filter(almacen_id__in=almacen_ids)
    if entidad:
        lotes = lotes.filter(
            Q(institucion__denominacion__icontains=entidad)
            | Q(institucion__estado__icontains=entidad)
            | Q(institucion__nombre__icontains=entidad)
        )
    if clues:
        lotes = lotes.filter(institucion__clue__icontains=clues)

    # Lotes que ya existían al cierre (evita escanear futuros)
    lotes = lotes.filter(
        Q(fecha_recepcion__isnull=True) | Q(fecha_recepcion__lte=fecha_cierre)
    )

    lotes = _annotar_existencia_cierre(lotes, fecha_cierre)
    if solo_con_existencia:
        lotes = lotes.filter(exist_cierre__gt=0)
    return lotes, grupos, almacen_ids


def _agregar_filas(lotes_qs, fecha_cierre, agrupacion):
    """Agrega filas del reporte. Retorna lista de dicts."""
    fecha_str = fecha_cierre.strftime('%d/%m/%Y')

    if agrupacion == AGRUPACION_CLAVE:
        qs = (
            lotes_qs.values(
                'producto__clave_cnis',
                'producto__descripcion',
            )
            .annotate(piezas=Sum('exist_cierre'))
            .order_by('producto__clave_cnis')
        )
        # Almacenes por clave (segunda pasada liviana sobre valores distintos)
        almacenes_por_clave = {}
        for row in (
            lotes_qs.filter(exist_cierre__gt=0)
            .values('producto__clave_cnis', 'almacen__nombre')
            .distinct()
            .order_by('producto__clave_cnis', 'almacen__nombre')
        ):
            clave = row['producto__clave_cnis'] or ''
            nombre = (row['almacen__nombre'] or '').strip() or '(Sin almacén)'
            almacenes_por_clave.setdefault(clave, [])
            if nombre not in almacenes_por_clave[clave]:
                almacenes_por_clave[clave].append(nombre)

        filas = []
        for g in qs:
            clave = g['producto__clave_cnis'] or ''
            piezas = g['piezas'] or 0
            if piezas <= 0:
                continue
            filas.append({
                'clave_cnis': clave,
                'descripcion': g['producto__descripcion'] or '',
                'almacenes': ', '.join(almacenes_por_clave.get(clave, [])),
                'piezas': piezas,
                'fecha_cierre': fecha_str,
            })
        return filas

    # Detalle por clave + almacén
    qs = (
        lotes_qs.values(
            'producto__clave_cnis',
            'producto__descripcion',
            'almacen__nombre',
            'institucion__denominacion',
            'institucion__clue',
        )
        .annotate(piezas=Sum('exist_cierre'))
        .order_by('producto__clave_cnis', 'almacen__nombre')
    )
    filas = []
    for g in qs:
        piezas = g['piezas'] or 0
        if piezas <= 0:
            continue
        institucion = g['institucion__denominacion'] or ''
        clue = g['institucion__clue'] or ''
        institucion_clues = f'{institucion} ({clue})' if clue else institucion
        filas.append({
            'clave_cnis': g['producto__clave_cnis'] or '',
            'descripcion': g['producto__descripcion'] or '',
            'almacen': (g['almacen__nombre'] or '').strip() or '(Sin almacén)',
            'institucion_clues': institucion_clues,
            'piezas': piezas,
            'fecha_cierre': fecha_str,
        })
    return filas


def _filtros_contexto(request, fecha_cierre, anio_mes, grupos, almacen_ids, agrupacion, consultado):
    return {
        'periodo': anio_mes,
        'fecha_cierre': fecha_cierre,
        'grupos_seleccionados': grupos,
        'grupos_opciones': GRUPOS_CNIS_OPCIONES,
        'almacen_ids': [int(a) for a in almacen_ids],
        'almacenes': Almacen.objects.filter(activo=True).order_by('nombre'),
        'filtro_entidad': (request.GET.get('entidad') or '').strip(),
        'filtro_clues': (request.GET.get('clues') or '').strip(),
        'agrupacion': agrupacion,
        'solo_existencia': (
            request.GET.get('solo_existencia') == 'si'
            if request.GET.get('consultar') == '1'
            else True
        ),
        'consultado': consultado,
    }


@login_required
def reporte_solicitud_informacion(request):
    """
    Existencias al cierre de mes por grupos CNIS y almacenes
    (útil para solicitudes de información / transparencia).
    """
    consultado = request.GET.get('consultar') == '1'
    agrupacion = request.GET.get('agrupacion') or AGRUPACION_CLAVE_ALMACEN
    if agrupacion not in (AGRUPACION_CLAVE_ALMACEN, AGRUPACION_CLAVE):
        agrupacion = AGRUPACION_CLAVE_ALMACEN

    fecha_cierre, anio_mes = _parse_periodo(request)
    grupos = _grupos_seleccionados(request)
    almacen_ids = [a for a in request.GET.getlist('almacen_id') if a.isdigit()]

    filas = []
    total_piezas = 0
    total_claves = 0
    page_obj = None
    requiere_periodo = False

    if consultado:
        if not fecha_cierre:
            messages.warning(request, 'Indique el mes de cierre (periodo).')
            requiere_periodo = True
        else:
            lotes_qs, grupos, almacen_ids = _queryset_lotes_filtrados(request, fecha_cierre)
            filas = _agregar_filas(lotes_qs, fecha_cierre, agrupacion)
            total_piezas = sum(f['piezas'] for f in filas)
            total_claves = len({f['clave_cnis'] for f in filas})

            paginator = Paginator(filas, 50)
            try:
                page_obj = paginator.page(request.GET.get('page', 1))
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)

    if page_obj is None:
        page_obj = Paginator([], 50).get_page(1)

    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    query_string = params.urlencode()

    ctx = {
        'page_obj': page_obj,
        'filas': page_obj.object_list,
        'total_filas': page_obj.paginator.count if consultado and fecha_cierre else 0,
        'total_piezas': total_piezas,
        'total_claves': total_claves,
        'headers': HEADERS_CONSOLIDADO if agrupacion == AGRUPACION_CLAVE else HEADERS_DETALLE,
        'is_consolidado': agrupacion == AGRUPACION_CLAVE,
        'query_string': query_string,
        'requiere_periodo': requiere_periodo,
        **_filtros_contexto(request, fecha_cierre, anio_mes, grupos, almacen_ids, agrupacion, consultado),
    }
    return render(request, 'inventario/reportes/reporte_solicitud_informacion.html', ctx)


@login_required
def exportar_solicitud_informacion_excel(request):
    """Exporta el reporte de solicitud de información a Excel."""
    if request.GET.get('consultar') != '1':
        messages.warning(request, 'Ejecute la consulta con filtros antes de exportar.')
        return redirect('reportes:reporte_solicitud_informacion')

    fecha_cierre, _anio_mes = _parse_periodo(request)
    if not fecha_cierre:
        messages.warning(request, 'Indique el mes de cierre para exportar.')
        return redirect(f"{reverse('reportes:reporte_solicitud_informacion')}?{request.GET.urlencode()}")

    agrupacion = request.GET.get('agrupacion') or AGRUPACION_CLAVE_ALMACEN
    if agrupacion not in (AGRUPACION_CLAVE_ALMACEN, AGRUPACION_CLAVE):
        agrupacion = AGRUPACION_CLAVE_ALMACEN

    lotes_qs, _grupos, _almacen_ids = _queryset_lotes_filtrados(request, fecha_cierre)
    filas = _agregar_filas(lotes_qs, fecha_cierre, agrupacion)

    if len(filas) > MAX_EXCEL_ROWS:
        messages.error(
            request,
            f'El resultado tiene {len(filas):,} filas (máximo {MAX_EXCEL_ROWS:,}). '
            'Reduce grupos, almacenes o el periodo.',
        )
        return redirect(f"{reverse('reportes:reporte_solicitud_informacion')}?{request.GET.urlencode()}")

    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title='Existencias cierre')
    headers = HEADERS_CONSOLIDADO if agrupacion == AGRUPACION_CLAVE else HEADERS_DETALLE
    ws.append(list(headers))

    if agrupacion == AGRUPACION_CLAVE:
        for f in filas:
            ws.append([
                f['clave_cnis'],
                f['descripcion'],
                f['almacenes'],
                f['piezas'],
                f['fecha_cierre'],
            ])
    else:
        for f in filas:
            ws.append([
                f['clave_cnis'],
                f['descripcion'],
                f['almacen'],
                f['institucion_clues'],
                f['piezas'],
                f['fecha_cierre'],
            ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    nombre = f"solicitud_informacion_cierre_{fecha_cierre.strftime('%Y%m')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    wb.save(response)
    return response
