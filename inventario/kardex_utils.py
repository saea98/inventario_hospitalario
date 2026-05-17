"""
Libro mayor / kardex de inventario por lote.

Presenta movimientos en orden cronológico con saldo inicial, entradas, salidas
y saldo acumulado (usa ``cantidad_nueva`` del sistema como saldo autoritativo).
"""

from datetime import datetime

from .comparativo_inventario_utils import signo_movimiento
from .models import Lote, MovimientoInventario


def _parse_fecha(s):
    if not s:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def saldo_inicial_lote(lote, fecha_desde):
    """
    Existencia al inicio del periodo (antes de fecha_desde).
    Si no hay fecha_desde, 0 antes del primer movimiento mostrado.
    """
    if not fecha_desde:
        return 0

    ultimo = (
        MovimientoInventario.objects.filter(
            lote_id=lote.id,
            anulado=False,
            fecha_movimiento__date__lt=fecha_desde,
        )
        .exclude(tipo_movimiento='AJUSTE_DATOS_LOTE')
        .order_by('-fecha_movimiento', '-id')
        .first()
    )
    if ultimo is not None:
        return int(ultimo.cantidad_nueva)

    if lote.fecha_recepcion and lote.fecha_recepcion < fecha_desde:
        return int(lote.cantidad_inicial or 0)
    return 0


def _movimiento_a_fila_kardex(mov, saldo_inicial_previo):
    signo = signo_movimiento(mov.tipo_movimiento)
    cantidad = int(mov.cantidad or 0)
    entrada = cantidad if signo > 0 else 0
    salida = cantidad if signo < 0 else 0
    saldo = int(mov.cantidad_nueva)
    return {
        'id': mov.id,
        'fecha': mov.fecha_movimiento,
        'tipo': mov.tipo_movimiento,
        'tipo_display': mov.get_tipo_movimiento_display(),
        'entrada': entrada,
        'salida': salida,
        'saldo': saldo,
        'cantidad_anterior': mov.cantidad_anterior,
        'cantidad_nueva': mov.cantidad_nueva,
        'motivo': mov.motivo or '',
        'documento': mov.documento_referencia or '',
        'folio': mov.folio or '',
        'pedido': mov.pedido or '',
        'usuario': (
            mov.usuario.get_full_name() or mov.usuario.username if mov.usuario else ''
        ),
        'anulado': mov.anulado,
        'institucion_destino': (
            mov.institucion_destino.denominacion if mov.institucion_destino else ''
        ),
        'delta_saldo': saldo - saldo_inicial_previo,
    }


def construir_kardex_lote(lote, fecha_desde=None, fecha_hasta=None, incluir_anulados=False):
    """Libro mayor de un solo lote."""
    movs = MovimientoInventario.objects.filter(lote=lote).select_related(
        'usuario', 'institucion_destino'
    )
    if not incluir_anulados:
        movs = movs.filter(anulado=False)
    movs = movs.exclude(tipo_movimiento='AJUSTE_DATOS_LOTE')

    if fecha_desde:
        movs = movs.filter(fecha_movimiento__date__gte=fecha_desde)
    if fecha_hasta:
        movs = movs.filter(fecha_movimiento__date__lte=fecha_hasta)

    movs = list(movs.order_by('fecha_movimiento', 'id'))

    saldo_ini = saldo_inicial_lote(lote, fecha_desde)
    saldo_corr = saldo_ini
    filas = []
    total_entradas = 0
    total_salidas = 0

    for m in movs:
        fila = _movimiento_a_fila_kardex(m, saldo_corr)
        filas.append(fila)
        total_entradas += fila['entrada']
        total_salidas += fila['salida']
        saldo_corr = fila['saldo']

    saldo_fin = saldo_corr if filas else saldo_ini

    return {
        'lote_id': lote.id,
        'numero_lote': lote.numero_lote,
        'clave_cnis': lote.producto.clave_cnis if lote.producto else '',
        'producto': lote.producto.descripcion if lote.producto else '',
        'clues': lote.institucion.clue if lote.institucion else '',
        'institucion': lote.institucion.denominacion if lote.institucion else '',
        'almacen': lote.almacen.nombre if lote.almacen else '',
        'existencia_actual': int(lote.cantidad_disponible or 0),
        'saldo_inicial': saldo_ini,
        'saldo_final': saldo_fin,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
        'neto_periodo': total_entradas - total_salidas,
        'movimientos': filas,
        'conteo_movimientos': len(filas),
    }


def _queryset_lotes_filtrados(params, institucion_usuario=None):
    clave = (params.get('clave') or params.get('busqueda_clave') or '').strip()
    lote = (params.get('lote') or params.get('busqueda_lote') or '').strip()
    clues = (params.get('clues') or '').strip()
    almacen = (params.get('almacen') or '').strip()
    tipo_producto = (params.get('producto') or params.get('busqueda_producto') or '').strip()

    qs = Lote.objects.select_related(
        'producto', 'institucion', 'almacen'
    ).order_by('producto__clave_cnis', 'numero_lote')

    if institucion_usuario:
        qs = qs.filter(institucion=institucion_usuario)

    if clave:
        qs = qs.filter(producto__clave_cnis__icontains=clave)
    if lote:
        qs = qs.filter(numero_lote__icontains=lote)
    if clues:
        qs = qs.filter(institucion__clue__icontains=clues)
    if almacen:
        qs = qs.filter(almacen__nombre__icontains=almacen)
    if tipo_producto:
        qs = qs.filter(producto__descripcion__icontains=tipo_producto)

    return qs, clave, lote


def construir_kardex_desde_request(request, max_lotes=30):
    """
    Devuelve (kardexes, error_msg, filtros_dict).
    Requiere al menos clave CNIS o número de lote.
    """
    params = request.GET
    fecha_desde = _parse_fecha(params.get('fecha_desde', ''))
    fecha_hasta = _parse_fecha(params.get('fecha_hasta', ''))
    incluir_anulados = params.get('incluir_anulados', '') == 'si'
    tipo_mov = (params.get('tipo') or '').strip()

    institucion = (
        request.user.institucion
        if hasattr(request.user, 'institucion') and request.user.institucion
        else None
    )
    lotes_qs, clave, lote = _queryset_lotes_filtrados(params, institucion)

    filtros = {
        'clave': clave or params.get('clave', ''),
        'lote': lote or params.get('lote', ''),
        'clues': params.get('clues', ''),
        'almacen': params.get('almacen', ''),
        'producto': params.get('producto', '') or params.get('busqueda_producto', ''),
        'fecha_desde': params.get('fecha_desde', ''),
        'fecha_hasta': params.get('fecha_hasta', ''),
        'tipo': tipo_mov,
        'incluir_anulados': incluir_anulados,
    }

    if not clave and not lote:
        return [], 'Indique al menos la clave CNIS o el número de lote para generar el kardex.', filtros

    total = lotes_qs.count()
    if total == 0:
        return [], 'No se encontraron lotes con los filtros indicados.', filtros
    if total > max_lotes and not lote:
        return (
            [],
            f'Se encontraron {total} lotes. Acote por número de lote o CLUES '
            f'(máximo {max_lotes} lotes por consulta).',
            filtros,
        )

    lotes = list(lotes_qs[:max_lotes])
    kardexes = []

    for l in lotes:
        k = construir_kardex_lote(
            l, fecha_desde, fecha_hasta, incluir_anulados=incluir_anulados
        )
        if tipo_mov:
            k['movimientos'] = [f for f in k['movimientos'] if f['tipo'] == tipo_mov]
            k['conteo_movimientos'] = len(k['movimientos'])
            if k['movimientos']:
                k['total_entradas'] = sum(f['entrada'] for f in k['movimientos'])
                k['total_salidas'] = sum(f['salida'] for f in k['movimientos'])
                k['neto_periodo'] = k['total_entradas'] - k['total_salidas']
                k['saldo_final'] = k['movimientos'][-1]['saldo']
            else:
                k['total_entradas'] = 0
                k['total_salidas'] = 0
                k['neto_periodo'] = 0

        if k['conteo_movimientos'] > 0 or not fecha_desde:
            kardexes.append(k)
        elif lote:
            kardexes.append(k)

    if not kardexes:
        return [], 'No hay movimientos en el periodo seleccionado.', filtros

    return kardexes, None, filtros
