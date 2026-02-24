"""
Fase 5 - Movimientos de Suministro de Pedido
Funciones auxiliares para generar movimientos de inventario automáticamente
cuando se marca una propuesta como surtida.
"""

from collections import defaultdict
from django.db import transaction
from django.utils import timezone
from datetime import date
import logging
from .models import MovimientoInventario, Lote
from .pedidos_models import PropuestaPedido

logger = logging.getLogger(__name__)


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
        propuesta = PropuestaPedido.objects.get(id=propuesta_id)
        movimientos_creados = 0

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

            # Iterar sobre los items y agrupar por lote_ubicacion para deducir una sola vez por ubicación
            for item in propuesta.items.all():
                logger.info(f"Procesando item {item.id} de propuesta {propuesta_id}")
                lotes_asignados = list(item.lotes_asignados.select_related(
                    'lote_ubicacion__lote', 'lote_ubicacion__ubicacion'
                ).all())
                # Agrupar por lote_ubicacion: total a deducir por ubicación
                por_ubicacion = defaultdict(int)
                for la in lotes_asignados:
                    if la.cantidad_asignada > 0:
                        por_ubicacion[la.lote_ubicacion] += la.cantidad_asignada

                for lote_ubicacion, cantidad_surtida in por_ubicacion.items():
                    if cantidad_surtida <= 0:
                        continue
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

                    cantidad_anterior_lote = lote.cantidad_disponible
                    cantidad_nueva_lote = cantidad_anterior_lote - cantidad_surtida

                    logger.info(f"Creando movimiento para lote {lote.numero_lote}: {cantidad_surtida} unidades")
                    MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento='SALIDA',
                        cantidad=cantidad_surtida,
                        cantidad_anterior=cantidad_anterior_lote,
                        cantidad_nueva=cantidad_nueva_lote,
                        motivo=f"Suministro de Pedido - Propuesta {propuesta.solicitud.folio}",
                        documento_referencia=str(propuesta.solicitud.folio),
                        pedido=str(propuesta.solicitud.folio),
                        folio=str(propuesta.id),
                        institucion_destino=propuesta.solicitud.institucion_solicitante,
                        usuario=usuario
                    )

                    lote_ubicacion.cantidad = cantidad_nueva_ubicacion
                    lote_ubicacion.cantidad_reservada = max(0, lote_ubicacion.cantidad_reservada - cantidad_surtida)
                    lote_ubicacion.save(update_fields=['cantidad', 'cantidad_reservada'])

                    cantidad_total_ubicaciones = sum(lu.cantidad for lu in lote.ubicaciones_detalle.all())
                    lote.cantidad_disponible = cantidad_total_ubicaciones
                    lote.cantidad_reservada = max(0, lote.cantidad_reservada - cantidad_surtida)
                    lote.save(update_fields=['cantidad_disponible', 'cantidad_reservada'])
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
