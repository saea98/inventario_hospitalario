"""
Fase 5 - Movimientos de Suministro de Pedido
Funciones auxiliares para generar movimientos de inventario automáticamente
cuando se marca una propuesta como surtida.
"""

from collections import defaultdict
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from datetime import date
import logging
from .models import MovimientoInventario, Lote, LoteUbicacion
from .pedidos_models import PropuestaPedido

logger = logging.getLogger(__name__)


def _folio_pedido_desde_solicitud(solicitud):
    """
    Folio comercial capturado en el pedido (SolicitudPedido.observaciones_solicitud,
    label «Folio del Pedido»). Si viene vacío, se usa el folio interno SOL-...
    """
    if not solicitud:
        return ''
    raw = (solicitud.observaciones_solicitud or '').strip()
    if raw:
        return raw.split('\n', 1)[0].strip()[:255]
    return (solicitud.folio or '')[:255]


def _texto_destino_solicitud(solicitud):
    """CLUE y denominación de la institución a la que va el pedido (solicitante)."""
    inst = getattr(solicitud, 'institucion_solicitante', None) if solicitud else None
    if not inst:
        return 'N/D'
    clue = (getattr(inst, 'clue', None) or '').strip()
    den = (getattr(inst, 'denominacion', None) or getattr(inst, 'nombre', None) or '').strip()
    if clue and den:
        return f'{clue} — {den}'
    return den or clue or 'N/D'


def _mensaje_cantidad_insuficiente(lote, lote_ubicacion, cantidad_anterior_ubicacion, cantidad_surtida):
    """Mensaje de error incluyendo nota sobre fecha de recepción si está en el futuro."""
    msg = (
        f"Cantidad insuficiente en lote {lote.numero_lote} ubicación {lote_ubicacion.ubicacion.codigo}. "
        f"Disponible: {cantidad_anterior_ubicacion}, Solicitado: {cantidad_surtida}"
    )
    if getattr(lote, 'fecha_recepcion', None) and lote.fecha_recepcion > date.today():
        msg += (
            f" Este lote tiene fecha de recepción en el futuro ({lote.fecha_recepcion.strftime('%d/%m/%Y')}). "
            "La disponibilidad no depende de esa fecha; si la cantidad en ubicación es correcta, verifique que no haya "
            "asignaciones duplicadas en la propuesta (editar propuesta y quitar filas repetidas del mismo lote)."
        )
    return msg


def generar_movimientos_suministro(propuesta_id, usuario):
    """
    Genera movimientos de inventario cuando una propuesta se va a marcar como SURTIDA.
    Se llama ANTES de marcar como surtido para validar y crear movimientos.
    Si falla, no se marca la propuesta como SURTIDA (evita falsos positivos).

    Agrupa por (item, lote_ubicacion) para deducir una sola vez por ubicación y evitar
    doble descuento si hubiera LoteAsignado duplicados.

    Args:
        propuesta_id: UUID de la propuesta
        usuario: Usuario que realizó el surtimiento

    Returns:
        dict: {'exito': bool, 'mensaje': str, 'movimientos_creados': int}
    """
    try:
        logger.info(f"Iniciando generación de movimientos para propuesta {propuesta_id}")
        propuesta = PropuestaPedido.objects.select_related(
            'solicitud__institucion_solicitante',
        ).get(id=propuesta_id)
        movimientos_creados = 0
        sol = propuesta.solicitud
        folio_pedido = _folio_pedido_desde_solicitud(sol) or (sol.folio or '')
        destino_txt = _texto_destino_solicitud(sol)
        motivo_salida = (
            f'Suministro de Pedido — Pedido: {folio_pedido}. Destino: {destino_txt}.'
        )

        with transaction.atomic():
            # Detectar asignaciones duplicadas (mismo item + misma lote_ubicacion): provocan doble descuento
            for item in propuesta.items.all():
                seen = set()
                for la in item.lotes_asignados.select_related('lote_ubicacion').all():
                    key = (item.id, la.lote_ubicacion_id)
                    if key in seen:
                        return {
                            'exito': False,
                            'mensaje': (
                                f"La propuesta tiene asignaciones duplicadas del mismo lote/ubicación "
                                f"(producto {item.producto.clave_cnis}). Edite la propuesta, elimine la fila duplicada "
                                f"del lote en «Lotes Asignados» y guarde de nuevo antes de surtir."
                            )
                        }
                    seen.add(key)

            # Total a descontar por lote_ubicacion (toda la propuesta), orden fijo para select_for_update
            por_lu_id = defaultdict(int)
            for item in propuesta.items.all():
                for la in item.lotes_asignados.all():
                    if la.cantidad_asignada and la.cantidad_asignada > 0:
                        por_lu_id[la.lote_ubicacion_id] += la.cantidad_asignada

            for lu_id in sorted(por_lu_id.keys()):
                cantidad_surtida = por_lu_id[lu_id]
                if cantidad_surtida <= 0:
                    continue
                lote_ubicacion = (
                    LoteUbicacion.objects.select_for_update()
                    .select_related('lote', 'ubicacion')
                    .get(pk=lu_id)
                )
                lote = lote_ubicacion.lote
                cantidad_anterior_ubicacion = lote_ubicacion.cantidad
                cantidad_nueva_ubicacion = cantidad_anterior_ubicacion - cantidad_surtida

                if cantidad_nueva_ubicacion < 0:
                    raise ValueError(
                        _mensaje_cantidad_insuficiente(
                            lote, lote_ubicacion,
                            cantidad_anterior_ubicacion, cantidad_surtida
                        )
                    )

                cantidad_anterior_lote = (
                    LoteUbicacion.objects.filter(lote=lote).aggregate(t=Sum('cantidad'))['t'] or 0
                )
                cantidad_nueva_lote = cantidad_anterior_lote - cantidad_surtida

                if cantidad_nueva_lote < 0:
                    raise ValueError(
                        f"Cantidad insuficiente en lote {lote.numero_lote} (total en ubicaciones). "
                        f"Disponible: {cantidad_anterior_lote}, Solicitado: {cantidad_surtida}"
                    )

                logger.info(
                    f"Movimiento surtido lote {lote.numero_lote} ubic {lote_ubicacion.ubicacion.codigo}: "
                    f"{cantidad_surtida} u (exist. ubic antes {cantidad_anterior_ubicacion})"
                )
                MovimientoInventario.objects.create(
                    lote=lote,
                    tipo_movimiento='SALIDA',
                    cantidad=cantidad_surtida,
                    cantidad_anterior=cantidad_anterior_lote,
                    cantidad_nueva=cantidad_nueva_lote,
                    motivo=motivo_salida,
                    documento_referencia=(sol.folio or '')[:100],
                    pedido=folio_pedido[:255],
                    folio=folio_pedido[:255],
                    institucion_destino=sol.institucion_solicitante,
                    usuario=usuario,
                )

                lote_ubicacion.cantidad = cantidad_nueva_ubicacion
                lote_ubicacion.cantidad_reservada = max(
                    0, lote_ubicacion.cantidad_reservada - cantidad_surtida
                )
                lote_ubicacion.save(update_fields=['cantidad', 'cantidad_reservada'])

                tot_cant = (
                    LoteUbicacion.objects.filter(lote=lote).aggregate(t=Sum('cantidad'))['t'] or 0
                )
                tot_res = (
                    LoteUbicacion.objects.filter(lote=lote).aggregate(t=Sum('cantidad_reservada'))['t']
                    or 0
                )
                Lote.objects.filter(pk=lote.pk).update(
                    cantidad_disponible=tot_cant, cantidad_reservada=tot_res
                )
                movimientos_creados += 1

        return {
            'exito': True,
            'movimientos_creados': movimientos_creados,
            'mensaje': f'Se generaron {movimientos_creados} movimientos de inventario'
        }

    except PropuestaPedido.DoesNotExist:
        return {
            'exito': False,
            'mensaje': f'Propuesta {propuesta_id} no encontrada'
        }
    except ValueError as e:
        return {
            'exito': False,
            'mensaje': f'Error al generar movimientos: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Error al generar movimientos para propuesta {propuesta_id}: {str(e)}", exc_info=True)
        return {
            'exito': False,
            'mensaje': f'Error al generar movimientos: {str(e)}'
        }


def revertir_movimientos_suministro(propuesta_id, usuario):
    """
    Revierte los movimientos de inventario de una propuesta ya surtida.
    Se usa al editar una propuesta SURTIDA: devuelve el stock a ubicaciones/lotes,
    crea movimientos de ENTRADA (reversión) y marca LoteAsignado como no surtido.
    Después de esto se pueden aplicar cambios en la propuesta y volver a llamar
    a generar_movimientos_suministro para que el inventario quede alineado.
    """
    from .pedidos_models import LoteAsignado
    try:
        logger.info(f"Revirtiendo movimientos de suministro para propuesta {propuesta_id}")
        propuesta = PropuestaPedido.objects.select_related(
            'solicitud__institucion_solicitante',
        ).get(id=propuesta_id)
        movimientos_revertidos = 0
        sol = propuesta.solicitud
        folio_pedido = _folio_pedido_desde_solicitud(sol) or (sol.folio or '')
        destino_txt = _texto_destino_solicitud(sol)
        motivo_reversion = (
            f'Reversión suministro — Pedido: {folio_pedido}. Destino: {destino_txt}. '
            f'Ref. solicitud: {sol.folio}.'
        )

        with transaction.atomic():
            for item in propuesta.items.select_related('producto').prefetch_related(
                'lotes_asignados__lote_ubicacion__lote', 'lotes_asignados__lote_ubicacion__ubicacion'
            ).all():
                for la in item.lotes_asignados.all():
                    if not la.surtido or la.cantidad_asignada <= 0:
                        continue
                    lu = la.lote_ubicacion
                    lote = lu.lote
                    cantidad = la.cantidad_asignada

                    cantidad_anterior_lote = sum(
                        LoteUbicacion.objects.filter(lote=lote).values_list('cantidad', flat=True)
                    )
                    cantidad_nueva_lote = cantidad_anterior_lote + cantidad

                    MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento='ENTRADA',
                        cantidad=cantidad,
                        cantidad_anterior=cantidad_anterior_lote,
                        cantidad_nueva=cantidad_nueva_lote,
                        motivo=motivo_reversion,
                        documento_referencia=(sol.folio or '')[:100],
                        pedido=folio_pedido[:255],
                        folio=folio_pedido[:255],
                        institucion_destino=sol.institucion_solicitante,
                        usuario=usuario
                    )
                    lu = LoteUbicacion.objects.select_for_update().get(pk=lu.pk)
                    lu.cantidad += cantidad
                    lu.save(update_fields=['cantidad'])
                    tot_cant = (
                        LoteUbicacion.objects.filter(lote=lote).aggregate(t=Sum('cantidad'))['t'] or 0
                    )
                    tot_res = (
                        LoteUbicacion.objects.filter(lote=lote).aggregate(t=Sum('cantidad_reservada'))[
                            't'
                        ]
                        or 0
                    )
                    Lote.objects.filter(pk=lote.pk).update(
                        cantidad_disponible=tot_cant, cantidad_reservada=tot_res
                    )
                    la.surtido = False
                    la.save(update_fields=['surtido'])
                    movimientos_revertidos += 1

        return {
            'exito': True,
            'movimientos_revertidos': movimientos_revertidos,
            'mensaje': f'Se revirtieron {movimientos_revertidos} movimientos de inventario'
        }
    except PropuestaPedido.DoesNotExist:
        return {'exito': False, 'mensaje': f'Propuesta {propuesta_id} no encontrada'}
    except Exception as e:
        logger.error(f"Error al revertir movimientos para propuesta {propuesta_id}: {str(e)}", exc_info=True)
        return {'exito': False, 'mensaje': str(e)}


def generar_movimiento_entrada_llegada(llegada_id, usuario):
    """
    Genera movimiento de inventario cuando se asignan ubicaciones en una llegada.
    
    Args:
        llegada_id: UUID de la llegada
        usuario: Usuario que realizó la asignación
        
    Returns:
        dict: Información sobre los movimientos creados
    """
    try:
        from .llegada_models import LlegadaProveedor
        
        logger.info(f"Iniciando generación de movimientos de entrada para llegada {llegada_id}")
        llegada = LlegadaProveedor.objects.get(pk=llegada_id)
        movimientos_creados = 0
        
        with transaction.atomic():
            # Iterar sobre los items de la llegada
            for item in llegada.items.all():
                logger.info(f"Procesando item {item.id} de llegada {llegada_id}")
                
                if not item.lote_creado:
                    logger.warning(f"Item {item.id} no tiene lote creado, saltando")
                    continue
                
                lote = item.lote_creado
                
                # Obtener todas las ubicaciones asignadas para este lote
                for lote_ubicacion in lote.ubicaciones_detalle.all():
                    cantidad = lote_ubicacion.cantidad
                    
                    # Crear movimiento de entrada
                    movimiento = MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento='Entrada de Proveedor',
                        cantidad_anterior=0,  # Es una entrada, no hay cantidad anterior
                        cantidad=cantidad,
                        cantidad_nueva=cantidad,
                        usuario=usuario,
                        documento_referencia=llegada.remision or f"LLEGADA-{llegada.id}",
                        folio=llegada.remision,
                        institucion_destino=lote.institucion,
                        motivo='Recepción de mercancía del proveedor'
                    )
                    
                    logger.info(f"Movimiento de entrada creado: {movimiento.id} para lote {lote.id}, cantidad {cantidad}")
                    movimientos_creados += 1
        
        logger.info(f"Se generaron {movimientos_creados} movimientos de entrada para llegada {llegada_id}")
        return {
            'exito': True,
            'movimientos_creados': movimientos_creados,
            'mensaje': f'Se generaron {movimientos_creados} movimientos de inventario'
        }
    
    except Exception as e:
        logger.error(f"Error al generar movimientos para llegada {llegada_id}: {str(e)}", exc_info=True)
        return {
            'exito': False,
            'movimientos_creados': 0,
            'mensaje': f'Error al generar movimientos: {str(e)}'
        }
