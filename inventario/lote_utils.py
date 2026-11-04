"""
Utilidades para completar datos de Lote desde Citas, Llegadas, Pedidos y Propuestas.
Obtiene RFC proveedor, orden de suministro, proveedor, partida, contrato, folio,
subtotal, IVA, importe_total, licitación, pedido (folio de pedido desde observaciones_solicitud),
remisión, responsable, revisó, tipo_entrega, tipo_red.
"""


def _valor_o_vacio(val):
    """Retorna valor o cadena vacía si es None."""
    if val is None:
        return ''
    if hasattr(val, 'strip'):
        return (val or '').strip()
    return str(val)


def resolver_remision_lote(lote, remision=None, partida=None):
    """
    Remisión efectiva del lote.

    Si el campo remisión está vacío, sugiere/usa ``partida`` (en algunos casos
    el número de remisión se captura ahí por error o por costumbre operativa).
    También considera partida_presupuestal de la orden de suministro.
    """
    rem = _valor_o_vacio(remision if remision is not None else getattr(lote, 'remision', None))
    if rem:
        return rem
    part = _valor_o_vacio(partida if partida is not None else getattr(lote, 'partida', None))
    if part:
        return part
    orden = getattr(lote, 'orden_suministro', None) if lote is not None else None
    if orden:
        return _valor_o_vacio(getattr(orden, 'partida_presupuestal', None))
    return ''


def _out_base_lote(lote):
    """Campos del lote + orden de suministro (sin consultas extra)."""
    out = {
        'rfc_proveedor': _valor_o_vacio(getattr(lote, 'rfc_proveedor', None)),
        'proveedor': _valor_o_vacio(getattr(lote, 'proveedor', None)),
        'partida': _valor_o_vacio(getattr(lote, 'partida', None)),
        'contrato': _valor_o_vacio(getattr(lote, 'contrato', None)),
        'folio': _valor_o_vacio(getattr(lote, 'folio', None)),
        'subtotal': getattr(lote, 'subtotal', None),
        'iva': getattr(lote, 'iva', None),
        'importe_total': getattr(lote, 'importe_total', None),
        'licitacion': _valor_o_vacio(getattr(lote, 'licitacion', None)),
        'pedido': _valor_o_vacio(getattr(lote, 'pedido', None)),
        'remision': _valor_o_vacio(getattr(lote, 'remision', None)),
        'responsable': _valor_o_vacio(getattr(lote, 'responsable', None)),
        'reviso': _valor_o_vacio(getattr(lote, 'reviso', None)),
        'tipo_entrega': _valor_o_vacio(getattr(lote, 'tipo_entrega', None)),
        'tipo_red': _valor_o_vacio(getattr(lote, 'tipo_red', None)),
    }
    orden = getattr(lote, 'orden_suministro', None)
    out['orden_suministro_numero'] = orden.numero_orden if orden else ''
    if orden and getattr(orden, 'proveedor', None):
        if not out['rfc_proveedor']:
            out['rfc_proveedor'] = _valor_o_vacio(orden.proveedor.rfc)
        if not out['proveedor']:
            out['proveedor'] = _valor_o_vacio(orden.proveedor.razon_social)
        if not out['partida']:
            out['partida'] = _valor_o_vacio(getattr(orden, 'partida_presupuestal', None))
    return out


def _aplicar_item_llegada(out, item_llegada):
    """Rellena huecos de out con ItemLlegada → Llegada → Cita."""
    if not item_llegada:
        return
    llegada = item_llegada.llegada
    if not llegada:
        return
    cita = getattr(llegada, 'cita', None)
    if not out['remision']:
        out['remision'] = _valor_o_vacio(getattr(llegada, 'remision', None))
    if not out['tipo_red']:
        out['tipo_red'] = _valor_o_vacio(getattr(llegada, 'tipo_red', None))
    if not out['folio']:
        out['folio'] = _valor_o_vacio(getattr(llegada, 'folio', None))
    if not out['contrato']:
        out['contrato'] = _valor_o_vacio(getattr(llegada, 'numero_contrato', None))
    if not out['contrato'] and cita:
        out['contrato'] = _valor_o_vacio(getattr(cita, 'numero_contrato', None))
    if not out['proveedor'] and llegada.proveedor:
        out['proveedor'] = _valor_o_vacio(
            getattr(llegada.proveedor, 'razon_social', None)
            or getattr(llegada.proveedor, 'nombre', None)
        )
    if not out['rfc_proveedor'] and llegada.proveedor:
        out['rfc_proveedor'] = _valor_o_vacio(getattr(llegada.proveedor, 'rfc', None))
    if not out['tipo_entrega'] and cita:
        te = getattr(cita, 'tipo_entrega', None)
        if te:
            if hasattr(cita, 'get_tipo_entrega_display'):
                out['tipo_entrega'] = cita.get_tipo_entrega_display()
            else:
                out['tipo_entrega'] = te if isinstance(te, str) else str(te)
    if not out['orden_suministro_numero'] and cita:
        out['orden_suministro_numero'] = _valor_o_vacio(getattr(cita, 'numero_orden_suministro', None))
    if not out['licitacion']:
        out['licitacion'] = _valor_o_vacio(getattr(llegada, 'numero_procedimiento', None))
    if not out['partida']:
        out['partida'] = _valor_o_vacio(getattr(llegada, 'programa_presupuestario', None))
    if out['subtotal'] is None and getattr(item_llegada, 'subtotal', None) is not None:
        out['subtotal'] = item_llegada.subtotal
    if out['iva'] is None and getattr(item_llegada, 'importe_iva', None) is not None:
        out['iva'] = item_llegada.importe_iva
    if out['importe_total'] is None and getattr(item_llegada, 'importe_total', None) is not None:
        out['importe_total'] = item_llegada.importe_total
    if not out['responsable'] and getattr(llegada, 'usuario_ubicacion', None):
        u = llegada.usuario_ubicacion
        out['responsable'] = _valor_o_vacio(
            u.get_username() if hasattr(u, 'get_username') else str(u)
        )
    if not out['reviso'] and getattr(llegada, 'usuario_supervision', None):
        u = llegada.usuario_supervision
        out['reviso'] = _valor_o_vacio(
            u.get_username() if hasattr(u, 'get_username') else str(u)
        )


def _pedidos_por_lote_ids(lote_ids):
    """Una consulta: folio de pedido (observaciones_solicitud) por lote_id."""
    if not lote_ids:
        return {}
    from .pedidos_models import LoteAsignado

    pedido_por_lote = {}
    qs = (
        LoteAsignado.objects.filter(lote_ubicacion__lote_id__in=lote_ids)
        .select_related('item_propuesta__propuesta__solicitud', 'lote_ubicacion')
        .order_by('id')
    )
    for la in qs.iterator(chunk_size=2000):
        lid = la.lote_ubicacion.lote_id
        if lid in pedido_por_lote:
            continue
        sol = la.item_propuesta.propuesta.solicitud
        pedido_por_lote[lid] = _valor_o_vacio(getattr(sol, 'observaciones_solicitud', None))
    return pedido_por_lote


def get_datos_complementarios_lotes_bulk(lotes):
    """
    Igual que get_datos_complementarios_lote, pero en bloque (sin N+1).
    Retorna {lote.id: dict}.
    """
    lotes = list(lotes)
    if not lotes:
        return {}

    result = {lote.id: _out_base_lote(lote) for lote in lotes}
    lote_ids = list(result.keys())

    # ItemLlegada en una sola query (si no vino por select_related)
    pendientes_llegada = []
    for lote in lotes:
        item = None
        try:
            item = getattr(lote, 'item_llegada', None)
        except Exception:
            item = None
        if item is not None:
            _aplicar_item_llegada(result[lote.id], item)
        else:
            pendientes_llegada.append(lote.id)

    if pendientes_llegada:
        from .llegada_models import ItemLlegada
        items = (
            ItemLlegada.objects.filter(lote_creado_id__in=pendientes_llegada)
            .select_related(
                'llegada',
                'llegada__cita',
                'llegada__proveedor',
                'llegada__usuario_ubicacion',
                'llegada__usuario_supervision',
            )
        )
        for item in items.iterator(chunk_size=2000):
            out = result.get(item.lote_creado_id)
            if out is not None:
                _aplicar_item_llegada(out, item)

    sin_pedido = [lid for lid, out in result.items() if not out.get('pedido')]
    for lid, pedido in _pedidos_por_lote_ids(sin_pedido).items():
        if pedido:
            result[lid]['pedido'] = pedido

    for out in result.values():
        if not out['remision'] and out['partida']:
            out['remision'] = out['partida']
    return result


def get_datos_complementarios_lote(lote):
    """
    Obtiene datos complementarios del lote desde relaciones:
    OrdenSuministro, ItemLlegada->Llegada->Cita, y Pedidos (SolicitudPedido.observaciones_solicitud).
    Retorna un diccionario con las mismas claves que los campos del Lote y rutas de export;
    se usa para rellenar valores vacíos en listados y exportación.
    """
    return get_datos_complementarios_lotes_bulk([lote]).get(lote.id, _out_base_lote(lote))


def completar_datos_lote_desde_llegada(lote, item_llegada):
    """
    Completa los campos del Lote con datos de ItemLlegada, Llegada y Cita.
    Se llama al crear el lote desde una llegada de proveedor.
    """
    if not item_llegada or not lote:
        return
    llegada = item_llegada.llegada
    cita = getattr(llegada, 'cita', None)
    # Proveedor y RFC
    if llegada.proveedor:
        if not (getattr(lote, 'proveedor', None) or '').strip():
            lote.proveedor = getattr(llegada.proveedor, 'razon_social', None) or getattr(llegada.proveedor, 'nombre', '') or ''
        if not (getattr(lote, 'rfc_proveedor', None) or '').strip():
            lote.rfc_proveedor = getattr(llegada.proveedor, 'rfc', None) or ''
    # Partida
    if not (getattr(lote, 'partida', None) or '').strip():
        lote.partida = (getattr(llegada, 'programa_presupuestario', None) or '').strip() or (getattr(cita, 'numero_orden_suministro', None) or '').strip()
    # Contrato, folio, remisión
    if not (getattr(lote, 'contrato', None) or '').strip():
        lote.contrato = (getattr(llegada, 'numero_contrato', None) or '').strip() or (getattr(cita, 'numero_contrato', None) or '').strip()
    if not (getattr(lote, 'folio', None) or '').strip():
        lote.folio = (getattr(llegada, 'folio', None) or '').strip()
    if not (getattr(lote, 'remision', None) or '').strip():
        lote.remision = (getattr(llegada, 'remision', None) or '').strip()
    # Si sigue vacía, a veces el número de remisión quedó capturado en partida
    if not (getattr(lote, 'remision', None) or '').strip():
        lote.remision = (getattr(lote, 'partida', None) or '').strip()
    # Tipo red / tipo entrega
    if not (getattr(lote, 'tipo_red', None) or '').strip():
        lote.tipo_red = (getattr(llegada, 'tipo_red', None) or '').strip()
    if not (getattr(lote, 'tipo_entrega', None) or '').strip() and cita:
        lote.tipo_entrega = (getattr(cita, 'tipo_entrega', None) or '').strip()
    # Licitación / procedimiento
    if not (getattr(lote, 'licitacion', None) or '').strip():
        lote.licitacion = (getattr(llegada, 'numero_procedimiento', None) or '').strip()
    # Subtotal, IVA, importe total desde ItemLlegada
    if getattr(lote, 'subtotal', None) is None and getattr(item_llegada, 'subtotal', None) is not None:
        lote.subtotal = item_llegada.subtotal
    if getattr(lote, 'iva', None) is None and getattr(item_llegada, 'importe_iva', None) is not None:
        lote.iva = item_llegada.importe_iva
    if getattr(lote, 'importe_total', None) is None and getattr(item_llegada, 'importe_total', None) is not None:
        lote.importe_total = item_llegada.importe_total
    # Responsable / Revisó (usuarios de llegada)
    if not (getattr(lote, 'responsable', None) or '').strip() and getattr(llegada, 'usuario_ubicacion', None):
        lote.responsable = getattr(llegada.usuario_ubicacion, 'username', None) or str(llegada.usuario_ubicacion)
    if not (getattr(lote, 'reviso', None) or '').strip() and getattr(llegada, 'usuario_supervision', None):
        lote.reviso = getattr(llegada.usuario_supervision, 'username', None) or str(llegada.usuario_supervision)
    # Orden de suministro: intentar enlazar por número si coincide
    if not lote.orden_suministro_id and cita:
        num_orden = (getattr(cita, 'numero_orden_suministro', None) or getattr(llegada, 'numero_orden_suministro', None) or '').strip()
        if num_orden:
            try:
                from .models import OrdenSuministro
                os = OrdenSuministro.objects.filter(numero_orden=num_orden).first()
                if os:
                    lote.orden_suministro = os
                    if not (getattr(lote, 'partida', None) or '').strip():
                        lote.partida = (getattr(os, 'partida_presupuestal', None) or '').strip()
            except Exception:
                pass
    lote.save()


def completar_datos_lote_desde_transferencia(lote, item_transferencia):
    """Completa metadatos del lote creado desde una entrada por transferencia."""
    if not item_transferencia or not lote:
        return
    transferencia = item_transferencia.transferencia
    if not (getattr(lote, 'folio', None) or '').strip():
        lote.folio = (transferencia.folio or '').strip()
    if not (getattr(lote, 'remision', None) or '').strip():
        lote.remision = (transferencia.remision or '').strip()
    if not (getattr(lote, 'remision', None) or '').strip():
        lote.remision = (getattr(lote, 'partida', None) or '').strip()
    if not (getattr(lote, 'tipo_entrega', None) or '').strip():
        lote.tipo_entrega = 'transferencia'
    if not (getattr(lote, 'proveedor', None) or '').strip():
        origen = (transferencia.entidad_origen or '').strip()
        if transferencia.estado_origen:
            origen = f'{origen} ({transferencia.estado_origen})'
        lote.proveedor = origen
    if not (getattr(lote, 'responsable', None) or '').strip() and transferencia.usuario_aprobacion:
        u = transferencia.usuario_aprobacion
        lote.responsable = getattr(u, 'username', None) or str(u)
    if getattr(item_transferencia, 'subtotal', None) is not None:
        lote.subtotal = item_transferencia.subtotal
    if getattr(item_transferencia, 'importe_iva', None) is not None:
        lote.iva = item_transferencia.importe_iva
    if getattr(item_transferencia, 'importe_total', None) is not None:
        lote.importe_total = item_transferencia.importe_total
    lote.save()
