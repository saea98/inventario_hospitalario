"""
Reporte de existencias por clave en formato de transferencias.

Columnas (mismo orden que el anexo):
CLAVE | DESCRIPCIÓN | EXISTENCIAS | ORDEN DE SUMINISTRO | LOTE | CADUCIDAD

EXISTENCIAS = inventario disponible neto (misma regla que inventario detallado /
disponibilidad): ``Lote.cantidad_disponible`` (stock físico tras entradas−salidas)
menos reservas activas en propuestas (``LoteAsignado`` con surtido=False).

Una fila por lote con existencia neta > 0 de la(s) clave(s) solicitada(s).
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Iterable, List

from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .decorators_roles import requiere_rol
from .models import Lote, MenuItemRol
from .views_reporte_inventario_detallado import _annotate_inventario_disponible_real

HEADERS = [
    'CLAVE',
    'DESCRIPCIÓN',
    'EXISTENCIAS',
    'ORDEN DE SUMINISTRO',
    'LOTE',
    'CADUCIDAD',
]


def _parse_claves(raw: str) -> List[str]:
    """Acepta claves separadas por coma, punto y coma, espacio o salto de línea."""
    if not raw:
        return []
    texto = raw.replace(';', ',').replace('\n', ',').replace('\t', ',')
    partes = []
    for chunk in texto.split(','):
        c = chunk.strip().upper()
        if c:
            partes.append(c)
    # únicos conservando orden
    return list(dict.fromkeys(partes))


def _variantes_clave(clave: str) -> List[str]:
    c = clave.strip().upper().replace(' ', '')
    out = [c]
    if c.endswith('.00'):
        out.append(c[:-3])
    else:
        out.append(c + '.00')
    return list(dict.fromkeys(out))


def _claves_busqueda(claves: Iterable[str]) -> List[str]:
    todas = []
    for c in claves:
        todas.extend(_variantes_clave(c))
    return list(dict.fromkeys(todas))


def _existencia_neta(lote) -> int:
    """Lee el neto anotado; fallback defensivo si no viene anotado."""
    if hasattr(lote, '_inventario_disponible_neto'):
        return max(0, int(lote._inventario_disponible_neto or 0))
    fisico = int(lote.cantidad_disponible or 0)
    reservado = int(getattr(lote, 'cantidad_reservada', 0) or 0)
    return max(0, fisico - reservado)


def obtener_lotes_con_existencia(claves: List[str]):
    """
    Lotes con existencia neta > 0 (físico − reservas activas) cuya clave CNIS coincide
    (exacta o con/sin sufijo .00).
    """
    variantes = _claves_busqueda(claves)
    if not variantes:
        return Lote.objects.none()

    q = Q()
    for v in variantes:
        q |= Q(producto__clave_cnis__iexact=v)

    qs = (
        Lote.objects.filter(q, cantidad_disponible__gt=0)
        .select_related('producto', 'orden_suministro')
        .order_by('producto__clave_cnis', 'fecha_caducidad', 'numero_lote')
    )
    return _annotate_inventario_disponible_real(qs).filter(
        _inventario_disponible_neto__gt=0
    )


def generar_excel_existencias_transferencias(claves: List[str]) -> BytesIO:
    lotes = obtener_lotes_con_existencia(claves)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Hoja1'

    header_fill = PatternFill('solid', fgColor='1F4E78')
    header_font = Font(bold=True, color='FFFFFF')
    for col, header in enumerate(HEADERS, 1):
        cell = ws.cell(1, col, header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    row_i = 2
    total_existencias = 0
    for lote in lotes.iterator(chunk_size=500):
        prod = lote.producto
        orden = ''
        if lote.orden_suministro_id and lote.orden_suministro:
            orden = lote.orden_suministro.numero_orden or ''
        existencia = _existencia_neta(lote)
        total_existencias += existencia
        ws.cell(row_i, 1, (prod.clave_cnis if prod else '') or '')
        ws.cell(row_i, 2, (prod.descripcion if prod else '') or '')
        ws.cell(row_i, 3, existencia)
        ws.cell(row_i, 4, orden)
        ws.cell(row_i, 5, lote.numero_lote or '')
        cell_cad = ws.cell(row_i, 6, lote.fecha_caducidad)
        if lote.fecha_caducidad:
            cell_cad.number_format = 'DD/MM/YYYY'
        row_i += 1

    # Fila de totales para facilitar revisión
    if row_i > 2:
        total_fill = PatternFill('solid', fgColor='D9E2F3')
        total_font = Font(bold=True)
        ws.cell(row_i, 1, 'TOTAL').font = total_font
        ws.cell(row_i, 1).fill = total_fill
        ws.cell(row_i, 2, '').fill = total_fill
        cell_tot = ws.cell(row_i, 3, total_existencias)
        cell_tot.font = total_font
        cell_tot.fill = total_fill
        cell_tot.number_format = '#,##0'
        for c in range(4, 7):
            ws.cell(row_i, c).fill = total_fill

    widths = [18, 55, 14, 45, 18, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def asegurar_menu_existencias_transferencias():
    from django.contrib.auth.models import Group

    item, _ = MenuItemRol.objects.update_or_create(
        menu_item='existencias_transferencias',
        defaults={
            'nombre_mostrado': 'Transferencias entre estados',
            'icono': 'fas fa-exchange-alt',
            'url_name': 'reportes:existencias_transferencias',
            'orden': 54,
            'es_submenu': False,
            'activo': True,
        },
    )
    roles = Group.objects.filter(
        name__in=['Supervisión', 'Administrador', 'Gestor de Inventario', 'Analista', 'Almacenero']
    )
    if roles.exists():
        item.roles_permitidos.set(roles)
    return item


@requiere_rol('Administrador', 'Gestor de Inventario', 'Supervisión', 'Analista', 'Almacenero')
def existencias_transferencias(request):
    """
    Formulario: indica una o varias claves CNIS y descarga Excel
    con todos los lotes que tienen existencia neta (físico − reservas).
    """
    context = {
        'claves_sel': '',
        'preview': None,
        'total_lotes': 0,
        'total_piezas': 0,
    }

    if request.method != 'POST':
        try:
            asegurar_menu_existencias_transferencias()
        except Exception:
            pass
        return render(request, 'inventario/reportes/existencias_transferencias.html', context)

    accion = (request.POST.get('accion') or 'descargar').strip().lower()
    claves_raw = (request.POST.get('claves') or '').strip()
    context['claves_sel'] = claves_raw
    claves = _parse_claves(claves_raw)

    if not claves:
        messages.error(request, 'Indica al menos una clave CNIS.')
        return render(request, 'inventario/reportes/existencias_transferencias.html', context)

    lotes_qs = obtener_lotes_con_existencia(claves)
    total_lotes = lotes_qs.count()
    if total_lotes == 0:
        messages.warning(
            request,
            f'No hay lotes con existencia disponible (neto) para la(s) clave(s): {", ".join(claves)}.',
        )
        return render(request, 'inventario/reportes/existencias_transferencias.html', context)

    if accion == 'vista_previa':
        preview = []
        for lote in lotes_qs[:200]:
            cant = _existencia_neta(lote)
            preview.append({
                'clave': lote.producto.clave_cnis if lote.producto else '',
                'descripcion': (lote.producto.descripcion if lote.producto else '') or '',
                'existencias': cant,
                'orden': (
                    lote.orden_suministro.numero_orden
                    if lote.orden_suministro_id and lote.orden_suministro
                    else ''
                ),
                'lote': lote.numero_lote or '',
                'caducidad': lote.fecha_caducidad,
            })
        total_piezas = (
            lotes_qs.aggregate(s=Sum('_inventario_disponible_neto'))['s'] or 0
        )
        context.update({
            'preview': preview,
            'total_lotes': total_lotes,
            'total_piezas': total_piezas,
            'preview_truncado': total_lotes > 200,
        })
        messages.success(
            request,
            f'{total_lotes} lote(s) con existencia neta ({total_piezas:,} piezas). '
            f'Puedes descargar el Excel.',
        )
        return render(request, 'inventario/reportes/existencias_transferencias.html', context)

    buf = generar_excel_existencias_transferencias(claves)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    clave_fn = claves[0].replace('.', '_').replace('/', '_')[:40]
    if len(claves) > 1:
        filename = f'existencias_transferencias_{len(claves)}_claves_{stamp}.xlsx'
    else:
        filename = f'existencias_transferencias_{clave_fn}_{stamp}.xlsx'

    response = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
