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
                    lote_ubicacion = lote_asignado.lote_ubicacion
                    lote = lote_ubicacion.lote
                    cantidad_surtida = lote_asignado.cantidad_asignada
                    
                    # Obtener cantidad anterior de la ubicación específica
                    cantidad_anterior_ubicacion = lote_ubicacion.cantidad
                    cantidad_nueva_ubicacion = cantidad_anterior_ubicacion - cantidad_surtida
                    
                    # Validar que no quede negativa
                    if cantidad_nueva_ubicacion < 0:
                        raise ValueError(
                            f"Cantidad insuficiente en lote {lote.numero_lote} ubicación {lote_ubicacion.ubicacion.codigo}. "
                            f"Disponible: {cantidad_anterior_ubicacion}, Solicitado: {cantidad_surtida}"
                        )
                    
                    # Obtener cantidad anterior del lote total
                    cantidad_anterior_lote = lote.cantidad_disponible
                    cantidad_nueva_lote = cantidad_anterior_lote - cantidad_surtida
                    
                    # Crear movimiento de inventario
                    logger.info(f"Creando movimiento para lote {lote.numero_lote}: {cantidad_surtida} unidades")
                    movimiento = MovimientoInventario.objects.create(
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
                    logger.info(f"Movimiento creado: {movimiento.id}")
                    
                    # Actualizar cantidad en la ubicación específica
                    lote_ubicacion.cantidad = cantidad_nueva_ubicacion
                    lote_ubicacion.save()
                    
                    # Actualizar cantidad disponible y reservada del lote (recalcular desde ubicaciones)
                    cantidad_total_ubicaciones = sum(lu.cantidad for lu in lote.ubicaciones_detalle.all())
                    lote.cantidad_disponible = cantidad_total_ubicaciones
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
