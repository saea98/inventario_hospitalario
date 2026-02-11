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


def get_datos_complementarios_lote(lote):
    """
    Obtiene datos complementarios del lote desde relaciones:
    OrdenSuministro, ItemLlegada->Llegada->Cita, y Pedidos (SolicitudPedido.observaciones_solicitud).
    Retorna un diccionario con las mismas claves que los campos del Lote y rutas de export;
    se usa para rellenar valores vacíos en listados y exportación.
    """
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
    # Orden de suministro (número) para export orden_suministro__*
    orden = getattr(lote, 'orden_suministro', None)
    out['orden_suministro_numero'] = orden.numero_orden if orden else ''
    if orden and orden.proveedor:
        if not out['rfc_proveedor']:
            out['rfc_proveedor'] = _valor_o_vacio(orden.proveedor.rfc)
        if not out['proveedor']:
            out['proveedor'] = _valor_o_vacio(orden.proveedor.razon_social)
        if not out['partida']:
            out['partida'] = _valor_o_vacio(getattr(orden, 'partida_presupuestal', None))
    # Desde ItemLlegada -> Llegada -> Cita (si el lote fue creado desde llegada)
    try:
        from .llegada_models import ItemLlegada
        item_llegada = getattr(lote, 'item_llegada', None)
        if item_llegada is None:
            try:
                item_llegada = ItemLlegada.objects.filter(lote_creado=lote).select_related(
                    'llegada', 'llegada__cita', 'llegada__proveedor'
                ).first()
            except Exception:
                item_llegada = None
        if item_llegada:
            llegada = item_llegada.llegada
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
                out['proveedor'] = _valor_o_vacio(getattr(llegada.proveedor, 'razon_social', None) or getattr(llegada.proveedor, 'nombre', None))
            if not out['rfc_proveedor'] and llegada.proveedor:
                out['rfc_proveedor'] = _valor_o_vacio(getattr(llegada.proveedor, 'rfc', None))
            if not out['tipo_entrega'] and cita:
                te = getattr(cita, 'tipo_entrega', None)
                if te:
                    out['tipo_entrega'] = getattr(cita, 'get_tipo_entrega_display', lambda: te)() if hasattr(cita, 'get_tipo_entrega_display') else (te if isinstance(te, str) else str(te))
            if not out['orden_suministro_numero'] and cita:
                out['orden_suministro_numero'] = _valor_o_vacio(getattr(cita, 'numero_orden_suministro', None))
            if not out['licitacion'] and llegada:
                out['licitacion'] = _valor_o_vacio(getattr(llegada, 'numero_procedimiento', None))
            if not out['partida'] and llegada:
                out['partida'] = _valor_o_vacio(getattr(llegada, 'programa_presupuestario', None))
            # Subtotal, IVA, importe_total desde ItemLlegada
            if out['subtotal'] is None and getattr(item_llegada, 'subtotal', None) is not None:
                out['subtotal'] = item_llegada.subtotal
            if out['iva'] is None and getattr(item_llegada, 'importe_iva', None) is not None:
                out['iva'] = item_llegada.importe_iva
            if out['importe_total'] is None and getattr(item_llegada, 'importe_total', None) is not None:
                out['importe_total'] = item_llegada.importe_total
            # Responsable / Revisó desde llegada (usuarios)
            if not out['responsable'] and getattr(llegada, 'usuario_ubicacion', None):
                out['responsable'] = _valor_o_vacio(llegada.usuario_ubicacion.get_username() if hasattr(llegada.usuario_ubicacion, 'get_username') else str(llegada.usuario_ubicacion))
            if not out['reviso'] and getattr(llegada, 'usuario_supervision', None):
                out['reviso'] = _valor_o_vacio(llegada.usuario_supervision.get_username() if hasattr(llegada.usuario_supervision, 'get_username') else str(llegada.usuario_supervision))
    except Exception:
        pass
    # Pedido (folio de pedido) desde inventario_pedidos: SolicitudPedido.observaciones_solicitud
    if not out['pedido']:
        try:
            from .pedidos_models import LoteAsignado
            la = LoteAsignado.objects.filter(
                lote_ubicacion__lote=lote
            ).select_related('item_propuesta__propuesta__solicitud').first()
            if la:
                sol = la.item_propuesta.propuesta.solicitud
                out['pedido'] = _valor_o_vacio(getattr(sol, 'observaciones_solicitud', None))
        except Exception:
            pass
    return out


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
