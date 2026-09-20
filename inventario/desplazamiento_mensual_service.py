"""
Complemento de reporte mensual de desplazamiento (programa por entidad)
con surtimientos reales del sistema (LoteAsignado surtido en el mes/año).
"""

from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from copy import copy
from datetime import date, datetime
from io import BytesIO
from typing import Dict, Iterable, List, Optional, Tuple

from django.db.models import Q
from django.utils import timezone
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .pedidos_models import LoteAsignado

Key = Tuple[str, str]  # (clues_norm, clave_norm)


def norm(v) -> str:
    return str(v).strip().upper() if v is not None else ''


def to_num(v) -> float:
    if v is None or v == '':
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def rango_mes(anio: int, mes: int) -> Tuple[date, date]:
    ultimo = monthrange(anio, mes)[1]
    return date(anio, mes, 1), date(anio, mes, ultimo)


def obtener_surtimientos_mes(anio: int, mes: int) -> Dict[Key, dict]:
    """
    Agrega cantidad surtida por (CLUES, CLAVE).
    CLUES se indexa tanto por ib_clue como por clue SSA para maximizar match.
    """
    inicio, fin = rango_mes(anio, mes)
    tz = timezone.get_current_timezone()
    dt_ini = timezone.make_aware(datetime.combine(inicio, datetime.min.time()), tz)
    dt_fin = timezone.make_aware(datetime.combine(fin, datetime.max.time()), tz)

    qs = (
        LoteAsignado.objects.filter(surtido=True, cantidad_asignada__gt=0)
        .filter(
            Q(fecha_surtimiento__gte=dt_ini, fecha_surtimiento__lte=dt_fin)
            | Q(
                fecha_surtimiento__isnull=True,
                item_propuesta__propuesta__fecha_surtimiento__gte=dt_ini,
                item_propuesta__propuesta__fecha_surtimiento__lte=dt_fin,
            )
        )
        .select_related(
            'item_propuesta__producto',
            'item_propuesta__propuesta__solicitud__institucion_solicitante',
            'item_propuesta__propuesta__solicitud',
        )
    )

    agg: Dict[Key, dict] = defaultdict(
        lambda: {'cantidad': 0.0, 'folios': [], 'descripcion': '', 'categoria': ''}
    )

    for la in qs.iterator(chunk_size=2000):
        item = la.item_propuesta
        if not item or not item.producto_id:
            continue
        propuesta = item.propuesta
        solicitud = propuesta.solicitud if propuesta else None
        inst = solicitud.institucion_solicitante if solicitud else None
        clave = norm(item.producto.clave_cnis)
        if not clave:
            continue
        folio = ''
        if solicitud:
            folio = (solicitud.observaciones_solicitud or '').strip() or (solicitud.folio or '')
        desc = (item.producto.descripcion or '')[:500]

        clues_keys = []
        if inst:
            if inst.ib_clue:
                clues_keys.append(norm(inst.ib_clue))
            if inst.clue:
                clues_keys.append(norm(inst.clue))
        clues_keys = [c for c in dict.fromkeys(clues_keys) if c]
        if not clues_keys:
            continue

        for clues in clues_keys:
            key = (clues, clave)
            agg[key]['cantidad'] += float(la.cantidad_asignada or 0)
            if folio and folio not in agg[key]['folios']:
                agg[key]['folios'].append(folio)
            if desc and not agg[key]['descripcion']:
                agg[key]['descripcion'] = desc

    return agg


def copy_row_style(ws, src_row: int, dst_row: int, max_col: int = 15):
    for col in range(1, max_col + 1):
        sc = ws.cell(src_row, col)
        dc = ws.cell(dst_row, col)
        if sc.has_style:
            dc.font = copy(sc.font)
            dc.border = copy(sc.border)
            dc.fill = copy(sc.fill)
            dc.number_format = sc.number_format
            dc.protection = copy(sc.protection)
            dc.alignment = copy(sc.alignment)


def complementar_workbook(
    archivo,
    anio: int,
    mes: int,
    *,
    nombre_fuente: str = '',
) -> Tuple[BytesIO, dict]:
    """
    Recibe el xlsx del programa mensual (hojas Resumen/Datos[/Extraordinario]),
    llena cantidad entregada desde surtimientos del mes y agrega filas adicionales.
    Retorna (buffer xlsx, estadisticas).
    """
    agg = obtener_surtimientos_mes(anio, mes)
    wb = load_workbook(archivo)

    if 'Datos' not in wb.sheetnames:
        raise ValueError("El archivo debe contener la hoja 'Datos'.")

    ws = wb['Datos']

    # Detectar fila de encabezados (busca 'CLUES' + 'CLAVE')
    header_row = None
    for r in range(1, min(20, ws.max_row + 1)):
        vals = [norm(ws.cell(r, c).value) for c in range(1, 16)]
        if 'CLUES' in vals and 'CLAVE' in vals:
            header_row = r
            break
    if not header_row:
        header_row = 8
    data_start = header_row + 1

    meta_clues = {}
    programa: Dict[Key, List[int]] = {}
    for r in range(data_start, ws.max_row + 1):
        clues = norm(ws.cell(r, 2).value)
        clave = norm(ws.cell(r, 4).value)
        if not clues or not clave:
            continue
        programa.setdefault((clues, clave), []).append(r)
        if clues not in meta_clues:
            meta_clues[clues] = {
                'entidad': ws.cell(r, 1).value or 'CIUDAD DE MEXICO',
                'categoria': ws.cell(r, 3).value or '',
                'unidad': ws.cell(r, 8).value or '',
            }

    extra_pairs = set()
    if 'Extraordinario' in wb.sheetnames:
        wse = wb['Extraordinario']
        for r in range(1, wse.max_row + 1):
            # columnas típicas: B entidad, C CLUES, D CLAVE (a veces con col A vacía)
            for clues_col, clave_col in ((3, 4), (2, 3)):
                clues = norm(wse.cell(r, clues_col).value)
                clave = norm(wse.cell(r, clave_col).value)
                if clues.startswith('DF') or clues.startswith('BC') or len(clues) >= 8:
                    if clave and '.' in clave or clave.startswith('0') or len(clave) >= 5:
                        if clues and clave and not clues.startswith('ENTIDAD'):
                            extra_pairs.add((clues, clave))

    fill_entregado = PatternFill('solid', fgColor='C6EFCE')
    fill_parcial = PatternFill('solid', fgColor='FFF2CC')
    fill_sin_exist = PatternFill('solid', fgColor='D9E2F3')
    fill_adicional = PatternFill('solid', fgColor='FCE4D6')
    fill_adic_row = PatternFill('solid', fgColor='FDF2E9')
    font_ok = Font(color='006100', bold=True)
    font_info = Font(color='1F4E79')
    font_adic = Font(color='C65911', bold=True)

    n_entregado = n_parcial = n_sin_exist = 0
    piezas_programa = piezas_adicionales = 0.0
    n_adicionales = 0

    for key, rows in programa.items():
        info = agg.get(key)
        for r in rows:
            proyectada = to_num(ws.cell(r, 11).value)
            cell_l = ws.cell(r, 12)
            cell_obs = ws.cell(r, 15)
            prev = str(cell_obs.value or '').strip()
            for tag in (
                'ENTREGADO según reporte pedidos',
                'SIN ENTREGA en reporte de pedidos',
                'ENTREGA ADICIONAL',
                'Sin entrega en el periodo',
                'Entrega parcial',
                'Entregado conforme a programa',
                'falta de existencia',
            ):
                if tag.lower() in prev.lower():
                    parts = [
                        p.strip()
                        for p in prev.split('|')
                        if p.strip() and tag.lower() not in p.lower()
                    ]
                    prev = ' | '.join(parts)

            if info and info['cantidad'] > 0:
                cant = info['cantidad']
                cell_l.value = cant
                piezas_programa += cant
                folios = ', '.join(info['folios'][:6])
                if len(info['folios']) > 6:
                    folios += f' (+{len(info["folios"]) - 6} más)'
                if proyectada and cant + 0.001 < proyectada:
                    n_parcial += 1
                    cell_l.fill = fill_parcial
                    nota = (
                        f'Entrega parcial ({cant:g} de {proyectada:g} proyectadas). '
                        f'Resto sujeto a existencia/disponibilidad. Folios: {folios}'
                    )
                else:
                    n_entregado += 1
                    cell_l.fill = fill_entregado
                    cell_l.font = font_ok
                    nota = f'Entregado conforme a programa. Folios: {folios}'
                cell_obs.value = (prev + ' | ' + nota) if prev else nota
            else:
                n_sin_exist += 1
                cell_l.value = 0
                cell_l.fill = fill_sin_exist
                cell_l.font = font_info
                nota = (
                    'Sin entrega en el periodo por falta de existencia o disponibilidad '
                    'en almacén central (no implica falta de gestión).'
                )
                cell_obs.value = (prev + ' | ' + nota) if prev else nota

    last_data_row = max((max(rows) for rows in programa.values()), default=header_row)
    template_row = data_start if data_start <= ws.max_row else header_row

    adicionales = [
        (clues, clave, info)
        for (clues, clave), info in sorted(agg.items(), key=lambda x: (x[0][0], x[0][1]))
        if (clues, clave) not in programa and info['cantidad'] > 0
    ]

    for clues, clave, info in adicionales:
        last_data_row += 1
        n_adicionales += 1
        piezas_adicionales += info['cantidad']
        copy_row_style(ws, template_row, last_data_row, 15)
        meta = meta_clues.get(clues, {})
        en_extra = (clues, clave) in extra_pairs
        folios = ', '.join(info['folios'][:6])
        if len(info['folios']) > 6:
            folios += f' (+{len(info["folios"]) - 6} más)'

        ws.cell(last_data_row, 1).value = meta.get('entidad') or 'CIUDAD DE MEXICO'
        ws.cell(last_data_row, 2).value = clues
        ws.cell(last_data_row, 3).value = meta.get('categoria') or info.get('categoria') or 'Entrega adicional'
        ws.cell(last_data_row, 4).value = clave
        ws.cell(last_data_row, 5).value = 'Entrega adicional'
        ws.cell(last_data_row, 6).value = 'Atención a demanda / fuera de programa'
        ws.cell(last_data_row, 7).value = info.get('descripcion') or ''
        ws.cell(last_data_row, 8).value = meta.get('unidad') or ''
        ws.cell(last_data_row, 9).value = None
        ws.cell(last_data_row, 10).value = None
        ws.cell(last_data_row, 11).value = 0
        cell_l = ws.cell(last_data_row, 12)
        cell_l.value = info['cantidad']
        cell_l.fill = fill_adicional
        cell_l.font = font_adic
        ws.cell(last_data_row, 13).value = 'ENTREGA ADICIONAL'
        ws.cell(last_data_row, 14).value = None
        obs = (
            'ENTREGA ADICIONAL / fuera del programa de desplazamiento. '
            'Atención a necesidades de la unidad más allá del listado base. '
            f'Folios: {folios}'
        )
        if en_extra:
            obs += ' (También referida en hoja Extraordinario).'
        ws.cell(last_data_row, 15).value = obs
        for col in range(1, 16):
            if col == 12:
                continue
            c = ws.cell(last_data_row, col)
            c.fill = fill_adic_row

    # Resumen ejecutivo
    _reescribir_resumen(
        wb,
        anio=anio,
        mes=mes,
        nombre_fuente=nombre_fuente,
        n_programa=len(programa),
        n_entregado=n_entregado,
        n_parcial=n_parcial,
        n_sin_exist=n_sin_exist,
        n_adicionales=n_adicionales,
        piezas_programa=piezas_programa,
        piezas_adicionales=piezas_adicionales,
        ws_datos=ws,
        data_start=data_start,
        last_data_row=last_data_row,
        fill_entregado=fill_entregado,
        fill_parcial=fill_parcial,
        fill_sin_exist=fill_sin_exist,
        fill_adicional=fill_adicional,
    )

    for name in ('Entregas fuera de programa', 'Resumen cruce entregas'):
        if name in wb.sheetnames:
            del wb[name]

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    total = piezas_programa + piezas_adicionales
    stats = {
        'anio': anio,
        'mes': mes,
        'pares_programa': len(programa),
        'entregado_ok': n_entregado,
        'entregado_parcial': n_parcial,
        'sin_existencia': n_sin_exist,
        'adicionales': n_adicionales,
        'piezas_programa': piezas_programa,
        'piezas_adicionales': piezas_adicionales,
        'piezas_total': total,
        'pares_surtimiento_bd': len(agg),
    }
    return buf, stats


def _reescribir_resumen(
    wb,
    *,
    anio,
    mes,
    nombre_fuente,
    n_programa,
    n_entregado,
    n_parcial,
    n_sin_exist,
    n_adicionales,
    piezas_programa,
    piezas_adicionales,
    ws_datos,
    data_start,
    last_data_row,
    fill_entregado,
    fill_parcial,
    fill_sin_exist,
    fill_adicional,
):
    if 'Resumen' not in wb.sheetnames:
        wsr = wb.create_sheet('Resumen', 0)
    else:
        wsr = wb['Resumen']
        for row in wsr.iter_rows(min_row=1, max_row=100, max_col=12):
            for cell in row:
                cell.value = None
                cell.fill = PatternFill()
                cell.font = Font()

    meses = (
        '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
    )
    total = piezas_programa + piezas_adicionales
    cobertura = (n_entregado + n_parcial) / max(n_programa, 1) * 100
    pct_adic = piezas_adicionales / max(total, 1) * 100

    cat_stats = defaultdict(lambda: {'clues': set(), 'claves': 0, 'piezas': 0.0, 'adic': 0.0, 'prog': 0.0})
    clues_all = set()
    for r in range(data_start, last_data_row + 1):
        clues = norm(ws_datos.cell(r, 2).value)
        clave = norm(ws_datos.cell(r, 4).value)
        if not clues or not clave:
            continue
        cat = str(ws_datos.cell(r, 3).value or 'Sin categoría').strip()
        tipo = str(ws_datos.cell(r, 5).value or '').strip()
        cant = to_num(ws_datos.cell(r, 12).value)
        cat_stats[cat]['clues'].add(clues)
        cat_stats[cat]['claves'] += 1
        cat_stats[cat]['piezas'] += cant
        clues_all.add(clues)
        if tipo == 'Entrega adicional':
            cat_stats[cat]['adic'] += cant
        else:
            cat_stats[cat]['prog'] += cant

    title_font = Font(bold=True, size=14, color='1F4E79')
    kpi_fill = PatternFill('solid', fgColor='1F4E79')
    kpi_font = Font(bold=True, color='FFFFFF', size=11)
    pos_fill = PatternFill('solid', fgColor='C6EFCE')
    adic_fill = PatternFill('solid', fgColor='FCE4D6')

    wsr['A1'] = f'AVANCE DE ENTREGAS — {meses[mes].upper()} {anio}'
    wsr['A1'].font = title_font
    wsr['A2'] = (
        f'Complementado con surtimientos del sistema | '
        f'Archivo base: {nombre_fuente or "programa mensual"} | '
        f'Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    )
    wsr['A2'].font = Font(italic=True, size=10)

    wsr['A4'] = 'INDICADORES DE GESTIÓN'
    wsr['A4'].font = Font(bold=True, size=12, color='833C0C')

    kpis = [
        (6, 'TOTAL PIEZAS ENTREGADAS', f'{total:,.0f}', True),
        (7, 'Piezas del programa (Datos)', f'{piezas_programa:,.0f}', False),
        (8, 'Piezas ENTREGA ADICIONAL (fuera de listado base)', f'{piezas_adicionales:,.0f}', True),
        (9, '% del volumen que fue atención adicional', f'{pct_adic:.1f}%', True),
        (10, 'CLUES atendidas', f'{len(clues_all)}', False),
        (11, 'Líneas de programa con entrega', f'{n_entregado + n_parcial} de {n_programa} ({cobertura:.1f}%)', False),
        (12, 'Líneas sin entrega por existencia/disponibilidad', f'{n_sin_exist}', False),
        (13, 'Líneas de entrega adicional agregadas', f'{n_adicionales}', True),
    ]
    for row, label, val, highlight_adic in kpis:
        wsr.cell(row, 1, label).fill = kpi_fill
        wsr.cell(row, 1).font = kpi_font
        wsr.cell(row, 2, val).font = Font(bold=True, size=12)
        if row == 6:
            wsr.cell(row, 2).fill = pos_fill
        elif highlight_adic:
            wsr.cell(row, 2).fill = adic_fill

    wsr['A15'] = (
        'Lectura: las líneas en azul en Datos no entregadas responden a falta de existencia/disponibilidad, '
        'no a falta de operación. Las líneas en naranja son entregas adicionales que evidencian atención '
        'a demanda real de las unidades, más allá del programa base.'
    )
    wsr['A15'].alignment = Alignment(wrap_text=True)
    wsr.merge_cells('A15:F17')

    wsr['A19'] = 'RESUMEN POR CATEGORÍA GERENCIAL (incluye adicionales)'
    wsr['A19'].font = Font(bold=True, size=12)
    headers = ['CATEGORIA GERENCIAL', 'CLUES', 'CLAVES/LÍNEAS', 'PIEZAS ENTREGADAS', 'DE PROGRAMA', 'ADICIONALES']
    for i, h in enumerate(headers, 1):
        cell = wsr.cell(20, i, h)
        cell.fill = PatternFill('solid', fgColor='833C0C')
        cell.font = Font(bold=True, color='FFFFFF')

    row_i = 21
    total_l = total_p = total_pg = total_ad = 0
    for cat, st in sorted(cat_stats.items(), key=lambda x: -x[1]['piezas']):
        wsr.cell(row_i, 1, cat)
        wsr.cell(row_i, 2, len(st['clues']))
        wsr.cell(row_i, 3, st['claves'])
        wsr.cell(row_i, 4, st['piezas'])
        wsr.cell(row_i, 5, st['prog'])
        wsr.cell(row_i, 6, st['adic'])
        total_l += st['claves']
        total_p += st['piezas']
        total_pg += st['prog']
        total_ad += st['adic']
        row_i += 1

    wsr.cell(row_i, 1, 'TOTAL').font = Font(bold=True)
    wsr.cell(row_i, 2, len(clues_all)).font = Font(bold=True)
    wsr.cell(row_i, 3, total_l).font = Font(bold=True)
    wsr.cell(row_i, 4, total_p).font = Font(bold=True)
    wsr.cell(row_i, 5, total_pg).font = Font(bold=True)
    wsr.cell(row_i, 6, total_ad).font = Font(bold=True)
    for col in range(1, 7):
        wsr.cell(row_i, col).fill = pos_fill

    row_i += 3
    wsr.cell(row_i, 1, 'LEYENDA EN HOJA DATOS').font = Font(bold=True)
    wsr.cell(row_i + 1, 1, 'Verde — Entregado conforme a programa').fill = fill_entregado
    wsr.cell(row_i + 2, 1, 'Amarillo — Entrega parcial (resto por existencia)').fill = fill_parcial
    wsr.cell(row_i + 3, 1, 'Azul — Sin entrega por falta de existencia/disponibilidad').fill = fill_sin_exist
    wsr.cell(row_i + 4, 1, 'Naranja — ENTREGA ADICIONAL / fuera del programa base').fill = fill_adicional

    wsr.column_dimensions['A'].width = 58
    wsr.column_dimensions['B'].width = 14
    wsr.column_dimensions['C'].width = 16
    wsr.column_dimensions['D'].width = 20
    wsr.column_dimensions['E'].width = 16
    wsr.column_dimensions['F'].width = 14


def asegurar_menu_desplazamiento_mensual():
    """Crea/actualiza la opción de menú (idempotente)."""
    from django.contrib.auth.models import Group

    from .models import MenuItemRol

    item, _ = MenuItemRol.objects.update_or_create(
        menu_item='desplazamiento_mensual',
        defaults={
            'nombre_mostrado': 'Desplazamiento mensual',
            'icono': 'fas fa-truck-loading',
            'url_name': 'reportes:desplazamiento_mensual',
            'orden': 53,
            'es_submenu': False,
            'activo': True,
        },
    )
    roles = Group.objects.filter(
        name__in=['Supervisión', 'Administrador', 'Gestor de Inventario', 'Analista']
    )
    if roles.exists():
        item.roles_permitidos.set(roles)
    return item
