"""
Fase 5 - Movimientos de Suministro de Pedido
Funciones auxiliares para generar movimientos de inventario automáticamente
cuando se marca una propuesta como surtida.
"""

from django.db import transaction
from django.utils import timezone
import logging
from .models import MovimientoInventario, Lote
from .pedidos_models import PropuestaPedido

logger = logging.getLogger(__name__)


def generar_movimientos_suministro(propuesta_id, usuario):
    """
    Genera movimientos de inventario cuando una propuesta se marca como SURTIDA.
    
    Args:
        propuesta_id: UUID de la propuesta
        usuario: Usuario que realizó el surtimiento
        
    Returns:
        dict: Información sobre los movimientos creados
    """
    try:
        logger.info(f"Iniciando generación de movimientos para propuesta {propuesta_id}")
        propuesta = PropuestaPedido.objects.get(id=propuesta_id)
        movimientos_creados = 0
        
        with transaction.atomic():
            # Iterar sobre los items de la propuesta
            for item in propuesta.items.all():
                logger.info(f"Procesando item {item.id} de propuesta {propuesta_id}")
                # Iterar sobre los lotes asignados surtidos
                lotes_surtidos = item.lotes_asignados.filter(surtido=True)
                logger.info(f"Lotes surtidos encontrados: {lotes_surtidos.count()}")
                for lote_asignado in lotes_surtidos:
                    lote = lote_asignado.lote
                    cantidad_surtida = lote_asignado.cantidad_asignada
                    
                    # Obtener cantidad anterior
                    cantidad_anterior = lote.cantidad_disponible
                    cantidad_nueva = cantidad_anterior - cantidad_surtida
                    
                    # Validar que no quede negativa
                    if cantidad_nueva < 0:
                        raise ValueError(
                            f"Cantidad insuficiente en lote {lote.numero_lote}. "
                            f"Disponible: {cantidad_anterior}, Solicitado: {cantidad_surtida}"
                        )
                    
                    # Crear movimiento de inventario
                    logger.info(f"Creando movimiento para lote {lote.numero_lote}: {cantidad_surtida} unidades")
                    movimiento = MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento='SALIDA',
                        cantidad=cantidad_surtida,
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=cantidad_nueva,
                        motivo=f"Suministro de Pedido - Propuesta {propuesta.solicitud.folio}",
                        documento_referencia=str(propuesta.solicitud.folio),
                        pedido=str(propuesta.solicitud.folio),
                        folio=str(propuesta.id),
                        usuario=usuario
                    )
                    logger.info(f"Movimiento creado: {movimiento.id}")
                    
                    # Actualizar cantidad disponible y reservada del lote
                    lote.cantidad_disponible = cantidad_nueva
                    lote.cantidad_reservada = max(0, lote.cantidad_reservada - cantidad_surtida)
                    lote.save()
                    
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
    except Exception as e:
        logger.error(f"Error al generar movimientos para propuesta {propuesta_id}: {str(e)}", exc_info=True)
        return {
            'exito': False,
            'mensaje': f'Error al generar movimientos: {str(e)}'
        }
