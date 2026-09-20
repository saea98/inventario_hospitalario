#!/usr/bin/env python3
"""
Arqueo / rastreo de claves+lotes desde Excel:
- ¿Existen en BD?
- Fecha recepción / remisión
- Ubicaciones (Lote.ubicacion + LoteUbicacion)
- Kardex de movimientos
- Indicador si se encontró y si salió sin ubicación

Salida: Excel en Downloads.
"""
from __future__ import annotations

import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import psycopg2
import psycopg2.extras
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
INPUT_XLSX = Path('/Users/Sjimenez/Downloads/Claves a buscar.xlsx')
OUT_DIR = Path('/Users/Sjimenez/Downloads')


def leer_busqueda(path: Path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall('m:si', NS):
                texts = [
                    t.text or ''
                    for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                ]
                shared.append(''.join(texts))
        root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows = []
        for row in root.findall('m:sheetData/m:row', NS):
            vals = []
            for c in row.findall('m:c', NS):
                t = c.get('t')
                v = c.find('m:v', NS)
                if v is None or v.text is None:
                    vals.append(None)
                    continue
                vals.append(shared[int(v.text)] if t == 's' else v.text)
            if not any(x is not None and str(x).strip() for x in vals):
                continue
            rows.append(vals)
    header = [str(h or '').strip().lower() for h in rows[0]]
    # columnas por posición según archivo conocido
    out = []
    for i, r in enumerate(rows[1:], start=2):
        while len(r) < 7:
            r.append(None)
        clave = str(r[0] or '').strip()
        lote = str(r[5] or '').strip()
        if not clave and not lote:
            continue
        out.append({
            'fila_excel': i,
            'clave': clave,
            'descripcion_excel': str(r[1] or '').strip()[:200],
            'um': str(r[2] or '').strip(),
            'piezas_emitidas': r[3],
            'piezas_recibidas': r[4],
            'lote': lote,
            'caducidad_excel': str(r[6] or '').strip(),
        })
    return out


def connect():
    return psycopg2.connect(
        host=os.environ['PGHOST'],
        port=os.environ.get('PGPORT', '5432'),
        dbname=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD'],
        connect_timeout=30,
    )


def norm_clave(c: str) -> str:
    return (c or '').strip().upper().replace(' ', '')


def buscar_lotes(cur, clave: str, lote: str):
    """Busca por clave+lote; fallback solo lote; fallback clave similar."""
    c = clave.strip()
    l = lote.strip()
    cur.execute(
        """
        SELECT l.id, l.numero_lote, l.cantidad_inicial, l.cantidad_disponible,
               l.cantidad_reservada, l.fecha_recepcion, l.fecha_caducidad,
               l.remision, l.folio, l.pedido, l.contrato, l.proveedor,
               l.fecha_creacion, l.estado, l.ubicacion_id,
               p.clave_cnis, left(p.descripcion, 120) AS descripcion,
               a.codigo AS almacen_codigo, a.nombre AS almacen_nombre,
               i.clue AS institucion_clue, i.denominacion AS institucion_nombre,
               ua.codigo AS ubicacion_fk_codigo
        FROM inventario_lote l
        JOIN inventario_producto p ON p.id = l.producto_id
        LEFT JOIN inventario_almacen a ON a.id = l.almacen_id
        LEFT JOIN inventario_institucion i ON i.id = l.institucion_id
        LEFT JOIN inventario_ubicacionalmacen ua ON ua.id = l.ubicacion_id
        WHERE upper(replace(p.clave_cnis, ' ', '')) = upper(replace(%s, ' ', ''))
          AND upper(trim(l.numero_lote)) = upper(trim(%s))
        ORDER BY l.fecha_recepcion, l.id
        """,
        (c, l),
    )
    rows = cur.fetchall()
    if rows:
        return rows, 'clave+lote'

    # solo lote (por si clave viene distinta)
    cur.execute(
        """
        SELECT l.id, l.numero_lote, l.cantidad_inicial, l.cantidad_disponible,
               l.cantidad_reservada, l.fecha_recepcion, l.fecha_caducidad,
               l.remision, l.folio, l.pedido, l.contrato, l.proveedor,
               l.fecha_creacion, l.estado, l.ubicacion_id,
               p.clave_cnis, left(p.descripcion, 120) AS descripcion,
               a.codigo AS almacen_codigo, a.nombre AS almacen_nombre,
               i.clue AS institucion_clue, i.denominacion AS institucion_nombre,
               ua.codigo AS ubicacion_fk_codigo
        FROM inventario_lote l
        JOIN inventario_producto p ON p.id = l.producto_id
        LEFT JOIN inventario_almacen a ON a.id = l.almacen_id
        LEFT JOIN inventario_institucion i ON i.id = l.institucion_id
        LEFT JOIN inventario_ubicacionalmacen ua ON ua.id = l.ubicacion_id
        WHERE upper(trim(l.numero_lote)) = upper(trim(%s))
          AND (
            upper(replace(p.clave_cnis, ' ', '')) LIKE '%%' || upper(replace(%s, ' ', '')) || '%%'
            OR upper(replace(%s, ' ', '')) LIKE '%%' || upper(replace(p.clave_cnis, ' ', '')) || '%%'
          )
        ORDER BY l.fecha_recepcion, l.id
        """,
        (l, c, c),
    )
    rows = cur.fetchall()
    if rows:
        return rows, 'lote+clave_parcial'

    cur.execute(
        """
        SELECT l.id, l.numero_lote, l.cantidad_inicial, l.cantidad_disponible,
               l.cantidad_reservada, l.fecha_recepcion, l.fecha_caducidad,
               l.remision, l.folio, l.pedido, l.contrato, l.proveedor,
               l.fecha_creacion, l.estado, l.ubicacion_id,
               p.clave_cnis, left(p.descripcion, 120) AS descripcion,
               a.codigo AS almacen_codigo, a.nombre AS almacen_nombre,
               i.clue AS institucion_clue, i.denominacion AS institucion_nombre,
               ua.codigo AS ubicacion_fk_codigo
        FROM inventario_lote l
        JOIN inventario_producto p ON p.id = l.producto_id
        LEFT JOIN inventario_almacen a ON a.id = l.almacen_id
        LEFT JOIN inventario_institucion i ON i.id = l.institucion_id
        LEFT JOIN inventario_ubicacionalmacen ua ON ua.id = l.ubicacion_id
        WHERE upper(trim(l.numero_lote)) = upper(trim(%s))
        ORDER BY l.fecha_recepcion, l.id
        LIMIT 20
        """,
        (l,),
    )
    rows = cur.fetchall()
    if rows:
        return rows, 'solo_lote'
    return [], 'no_encontrado'


def ubicaciones_lote(cur, lote_id: int):
    cur.execute(
        """
        SELECT lu.id, lu.cantidad, ua.codigo, ua.descripcion, a.codigo AS alm, a.nombre AS alm_nom
        FROM inventario_loteubicacion lu
        JOIN inventario_ubicacionalmacen ua ON ua.id = lu.ubicacion_id
        LEFT JOIN inventario_almacen a ON a.id = ua.almacen_id
        WHERE lu.lote_id = %s
        ORDER BY ua.codigo
        """,
        (lote_id,),
    )
    return cur.fetchall()


def movimientos_lote(cur, lote_id: int):
    cur.execute(
        """
        SELECT m.id, m.tipo_movimiento, m.cantidad, m.cantidad_anterior, m.cantidad_nueva,
               m.fecha_movimiento, m.motivo, m.remision, m.folio, m.pedido, m.documento_referencia,
               m.anulado, u.username,
               idest.clue AS dest_clue, idest.denominacion AS dest_nombre
        FROM inventario_movimientoinventario m
        LEFT JOIN inventario_user u ON u.id = m.usuario_id
        LEFT JOIN inventario_institucion idest ON idest.id = m.institucion_destino_id
        WHERE m.lote_id = %s
        ORDER BY m.fecha_movimiento, m.id
        """,
        (lote_id,),
    )
    return cur.fetchall()


def style_header(ws, row=1):
    fill = PatternFill('solid', fgColor='1F4E79')
    font = Font(color='FFFFFF', bold=True)
    for cell in ws[row]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(wrap_text=True, vertical='center')


def main():
    busqueda = leer_busqueda(INPUT_XLSX)
    print(f'Filas a buscar: {len(busqueda)}')

    conn = connect()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    resumen = []
    movimientos = []
    ubicaciones = []

    for item in busqueda:
        lotes, match = buscar_lotes(cur, item['clave'], item['lote'])
        if not lotes:
            resumen.append({
                **item,
                'encontrado': 'NO',
                'match': match,
                'lote_id': None,
                'clave_bd': None,
                'lote_bd': None,
                'fecha_recepcion': None,
                'fecha_creacion': None,
                'remision_lote': None,
                'cant_inicial': None,
                'cant_disponible': None,
                'cant_reservada': None,
                'almacen': None,
                'ubicacion_fk': None,
                'tiene_loteubicacion': 'NO',
                'ubicaciones_detalle': '',
                'suma_ubicaciones': 0,
                'n_movimientos': 0,
                'n_entradas': 0,
                'n_salidas': 0,
                'total_entradas': 0,
                'total_salidas': 0,
                'primera_entrada': None,
                'ultima_salida': None,
                'salio_sin_ubicacion': '',
                'observacion': 'No existe lote/clave en BD',
            })
            continue

        for lot in lotes:
            ubis = ubicaciones_lote(cur, lot['id'])
            movs = movimientos_lote(cur, lot['id'])
            suma_ubi = sum(int(u['cantidad'] or 0) for u in ubis)
            tiene_ubi = bool(ubis) or bool(lot['ubicacion_id'])
            entradas = [m for m in movs if m['tipo_movimiento'] in ('ENTRADA', 'TRANSFERENCIA_ENTRADA', 'AJUSTE_POSITIVO') and not m['anulado']]
            salidas = [m for m in movs if m['tipo_movimiento'] in ('SALIDA', 'TRANSFERENCIA_SALIDA', 'AJUSTE_NEGATIVO', 'CADUCIDAD', 'DETERIORO') and not m['anulado']]
            tot_e = sum(int(m['cantidad'] or 0) for m in entradas)
            tot_s = sum(int(m['cantidad'] or 0) for m in salidas)
            prim_e = min((m['fecha_movimiento'] for m in entradas), default=None)
            ult_s = max((m['fecha_movimiento'] for m in salidas), default=None)

            salio_sin = ''
            if salidas and not tiene_ubi:
                salio_sin = 'SI — hay salidas y no hay registro de ubicación'
            elif salidas and not ubis and lot['ubicacion_id']:
                salio_sin = 'Parcial — solo FK ubicacion en lote, sin LoteUbicacion'
            elif salidas and tiene_ubi:
                salio_sin = 'NO — tiene ubicación registrada'
            elif not salidas:
                salio_sin = 'N/A — sin salidas'

            obs = []
            if match != 'clave+lote':
                obs.append(f'Match por {match}')
            if not lot['remision']:
                obs.append('Sin remisión en lote')
            if not tiene_ubi:
                obs.append('Sin ubicación')
            if lot['fecha_recepcion'] and lot['fecha_recepcion'].month in (1, 2):
                obs.append(f'Recepción mes {lot["fecha_recepcion"].month}/{lot["fecha_recepcion"].year}')

            resumen.append({
                **item,
                'encontrado': 'SI',
                'match': match,
                'lote_id': lot['id'],
                'clave_bd': lot['clave_cnis'],
                'lote_bd': lot['numero_lote'],
                'fecha_recepcion': lot['fecha_recepcion'],
                'fecha_creacion': lot['fecha_creacion'],
                'remision_lote': lot['remision'],
                'cant_inicial': lot['cantidad_inicial'],
                'cant_disponible': lot['cantidad_disponible'],
                'cant_reservada': lot['cantidad_reservada'],
                'almacen': f"{lot['almacen_codigo'] or ''} | {lot['almacen_nombre'] or ''}".strip(' |'),
                'ubicacion_fk': lot['ubicacion_fk_codigo'],
                'tiene_loteubicacion': 'SI' if ubis else 'NO',
                'ubicaciones_detalle': '; '.join(
                    f"{u['codigo']}({u['cantidad']})" for u in ubis
                ),
                'suma_ubicaciones': suma_ubi,
                'n_movimientos': len(movs),
                'n_entradas': len(entradas),
                'n_salidas': len(salidas),
                'total_entradas': tot_e,
                'total_salidas': tot_s,
                'primera_entrada': prim_e,
                'ultima_salida': ult_s,
                'salio_sin_ubicacion': salio_sin,
                'observacion': '; '.join(obs) if obs else 'OK',
            })

            for u in ubis:
                ubicaciones.append({
                    'fila_excel': item['fila_excel'],
                    'clave_buscada': item['clave'],
                    'lote_buscado': item['lote'],
                    'lote_id': lot['id'],
                    'clave_bd': lot['clave_cnis'],
                    'lote_bd': lot['numero_lote'],
                    'ubicacion': u['codigo'],
                    'descripcion_ubi': u['descripcion'],
                    'cantidad': u['cantidad'],
                    'almacen': u['alm_nom'] or u['alm'],
                })

            for m in movs:
                movimientos.append({
                    'fila_excel': item['fila_excel'],
                    'clave_buscada': item['clave'],
                    'lote_buscado': item['lote'],
                    'encontrado': 'SI',
                    'lote_id': lot['id'],
                    'clave_bd': lot['clave_cnis'],
                    'lote_bd': lot['numero_lote'],
                    'mov_id': m['id'],
                    'tipo': m['tipo_movimiento'],
                    'cantidad': m['cantidad'],
                    'cant_ant': m['cantidad_anterior'],
                    'cant_nueva': m['cantidad_nueva'],
                    'fecha': m['fecha_movimiento'],
                    'remision': m['remision'],
                    'folio': m['folio'],
                    'pedido': m['pedido'],
                    'doc_ref': m['documento_referencia'],
                    'motivo': (m['motivo'] or '')[:300],
                    'usuario': m['username'],
                    'destino': f"{m['dest_clue'] or ''} {m['dest_nombre'] or ''}".strip(),
                    'anulado': 'SI' if m['anulado'] else 'NO',
                    'tenia_ubicacion_al_rastreo': 'SI' if tiene_ubi else 'NO',
                })

    cur.close()
    conn.close()

    # Excel salida
    wb = Workbook()
    ws = wb.active
    ws.title = 'Resumen arqueo'

    headers_r = [
        'Fila Excel', 'Encontrado', 'Match', 'Clave buscada', 'Lote buscado',
        'Piezas recibidas Excel', 'Clave BD', 'Lote BD', 'Lote ID',
        'Fecha recepción', 'Fecha creación registro', 'Remisión lote',
        'Cant. inicial', 'Cant. disponible', 'Cant. reservada',
        'Almacén', 'Ubicación FK lote', '¿Tiene LoteUbicacion?', 'Ubicaciones',
        'Suma en ubicaciones', 'N movs', 'N entradas', 'N salidas',
        'Total entradas', 'Total salidas', 'Primera entrada', 'Última salida',
        '¿Salió sin ubicación?', 'Observación',
    ]
    ws.append(headers_r)
    style_header(ws)
    for r in resumen:
        ws.append([
            r['fila_excel'], r['encontrado'], r['match'], r['clave'], r['lote'],
            r['piezas_recibidas'], r['clave_bd'], r['lote_bd'], r['lote_id'],
            r['fecha_recepcion'].isoformat() if r['fecha_recepcion'] else '',
            r['fecha_creacion'].strftime('%Y-%m-%d %H:%M') if r['fecha_creacion'] else '',
            r['remision_lote'] or '',
            r['cant_inicial'], r['cant_disponible'], r['cant_reservada'],
            r['almacen'] or '', r['ubicacion_fk'] or '', r['tiene_loteubicacion'],
            r['ubicaciones_detalle'], r['suma_ubicaciones'],
            r['n_movimientos'], r['n_entradas'], r['n_salidas'],
            r['total_entradas'], r['total_salidas'],
            r['primera_entrada'].strftime('%Y-%m-%d %H:%M') if r['primera_entrada'] else '',
            r['ultima_salida'].strftime('%Y-%m-%d %H:%M') if r['ultima_salida'] else '',
            r['salio_sin_ubicacion'], r['observacion'],
        ])

    # colorear NO encontrados / salió sin ub
    red = PatternFill('solid', fgColor='F4CCCC')
    yellow = PatternFill('solid', fgColor='FFF2CC')
    green = PatternFill('solid', fgColor='D9EAD3')
    for i, r in enumerate(resumen, start=2):
        if r['encontrado'] == 'NO':
            for col in range(1, len(headers_r) + 1):
                ws.cell(i, col).fill = red
        elif str(r['salio_sin_ubicacion']).startswith('SI'):
            ws.cell(i, 28).fill = yellow
        else:
            ws.cell(i, 2).fill = green

    ws2 = wb.create_sheet('Movimientos')
    headers_m = [
        'Fila Excel', 'Encontrado', 'Clave buscada', 'Lote buscado', 'Lote ID',
        'Clave BD', 'Lote BD', 'Mov ID', 'Tipo', 'Cantidad', 'Cant ant', 'Cant nueva',
        'Fecha', 'Remisión mov', 'Folio', 'Pedido', 'Doc ref', 'Motivo',
        'Usuario', 'Destino', 'Anulado', 'Tenía ubicación (al rastreo)',
    ]
    ws2.append(headers_m)
    style_header(ws2)
    for m in movimientos:
        ws2.append([
            m['fila_excel'], m['encontrado'], m['clave_buscada'], m['lote_buscado'],
            m['lote_id'], m['clave_bd'], m['lote_bd'], m['mov_id'], m['tipo'],
            m['cantidad'], m['cant_ant'], m['cant_nueva'],
            m['fecha'].strftime('%Y-%m-%d %H:%M:%S') if m['fecha'] else '',
            m['remision'] or '', m['folio'] or '', m['pedido'] or '',
            m['doc_ref'] or '', m['motivo'], m['usuario'] or '', m['destino'],
            m['anulado'], m['tenia_ubicacion_al_rastreo'],
        ])

    ws3 = wb.create_sheet('Ubicaciones')
    headers_u = [
        'Fila Excel', 'Clave buscada', 'Lote buscado', 'Lote ID', 'Clave BD', 'Lote BD',
        'Código ubicación', 'Descripción', 'Cantidad', 'Almacén',
    ]
    ws3.append(headers_u)
    style_header(ws3)
    for u in ubicaciones:
        ws3.append([
            u['fila_excel'], u['clave_buscada'], u['lote_buscado'], u['lote_id'],
            u['clave_bd'], u['lote_bd'], u['ubicacion'], u['descripcion_ubi'] or '',
            u['cantidad'], u['almacen'] or '',
        ])

    # hoja no encontrados explícita
    ws4 = wb.create_sheet('No encontrados')
    ws4.append(['Fila Excel', 'Clave', 'Lote', 'Piezas recibidas', 'Caducidad Excel', 'Descripción'])
    style_header(ws4)
    for r in resumen:
        if r['encontrado'] == 'NO':
            ws4.append([
                r['fila_excel'], r['clave'], r['lote'], r['piezas_recibidas'],
                r['caducidad_excel'], r['descripcion_excel'],
            ])

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = OUT_DIR / f'arqueo_claves_lotes_{stamp}.xlsx'
    wb.save(out)

    n_si = sum(1 for r in resumen if r['encontrado'] == 'SI')
    n_no = sum(1 for r in resumen if r['encontrado'] == 'NO')
    # unique excel rows
    filas = {r['fila_excel'] for r in resumen}
    filas_si = {r['fila_excel'] for r in resumen if r['encontrado'] == 'SI'}
    filas_no = filas - filas_si
    salio_sin = sum(1 for r in resumen if str(r['salio_sin_ubicacion']).startswith('SI'))
    sin_ubi = sum(1 for r in resumen if r['encontrado'] == 'SI' and r['tiene_loteubicacion'] == 'NO' and not r['ubicacion_fk'])

    print(f'Registros resumen (lote matches): {len(resumen)}')
    print(f'Filas Excel encontradas: {len(filas_si)} / {len(filas)}')
    print(f'Filas Excel NO encontradas: {len(filas_no)}')
    print(f'Sin ubicación (encontrados): {sin_ubi}')
    print(f'Salieron sin ubicación: {salio_sin}')
    print(f'Movimientos listados: {len(movimientos)}')
    print(f'OUT: {out}')


if __name__ == '__main__':
    # openpyxl may be missing; install hint
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print('Instala openpyxl en el venv antes de correr.', file=sys.stderr)
        sys.exit(1)
    main()
