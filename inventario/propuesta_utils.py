"""
Utilidades para gestionar propuestas de suministro con sistema de reserva de cantidades.

Este módulo proporciona funciones para:
1. Reservar cantidades cuando se asignan lotes a una propuesta
2. Liberar cantidades cuando se cancela una propuesta (rollback)
3. Validar disponibilidad considerando cantidades reservadas
4. Actualizar cantidades al completar el surtimiento
"""

from django.db import transaction
from django.utils import timezone
from .pedidos_models import PropuestaPedido, ItemPropuesta, LoteAsignado, LogPropuesta
from .models import Lote, LoteUbicacion


def reservar_cantidad_lote(lote_ubicacion, cantidad):
    """
    Reserva una cantidad en un lote sin afectar cantidad_disponible.
    Se incrementa cantidad_reservada para que otras propuestas no lo consideren.
    
    Args:
        lote_ubicacion: Instancia de LoteUbicacion
        cantidad: Cantidad a reservar
    
    Returns:
        bool: True si se reservó exitosamente, False si no hay suficiente cantidad disponible
    """
    lote = lote_ubicacion.lote
    cantidad_realmente_disponible = lote.cantidad_disponible - lote.cantidad_reservada
    
    if cantidad_realmente_disponible < cantidad:
        return False
    
    # Incrementar cantidad_reservada
    lote.cantidad_reservada += cantidad
    lote.save(update_fields=['cantidad_reservada'])
    
    return True


def liberar_cantidad_lote(lote_ubicacion, cantidad):
    """
    Libera una cantidad reservada en un lote (rollback).
    Se decrementa cantidad_reservada.
    
    Args:
        lote_ubicacion: Instancia de LoteUbicacion
        cantidad: Cantidad a liberar
    """
    lote = lote_ubicacion.lote
    
    # Decrementar cantidad_reservada (no puede ser menor a 0)
    lote.cantidad_reservada = max(0, lote.cantidad_reservada - cantidad)
    lote.save(update_fields=['cantidad_reservada'])


def cancelar_propuesta(propuesta_id, usuario=None):
    """
    Cancela una propuesta de suministro y libera todas las cantidades reservadas.
    Hace un rollback completo de la propuesta.
    
    Args:
        propuesta_id: ID de la propuesta a cancelar
        usuario: Usuario que realiza la cancelación (para auditoría)
    
    Returns:
        dict: {'exito': bool, 'mensaje': str, 'propuesta': PropuestaPedido}
    """
    try:
        propuesta = PropuestaPedido.objects.get(id=propuesta_id)
        
        # Solo se pueden cancelar propuestas en ciertos estados
        estados_cancelables = ['GENERADA', 'REVISADA', 'EN_SURTIMIENTO']
        if propuesta.estado not in estados_cancelables:
            return {
                'exito': False,
                'mensaje': f'No se puede cancelar una propuesta en estado {propuesta.get_estado_display()}'
            }
        
        with transaction.atomic():
            # Liberar todas las cantidades reservadas
            for item in propuesta.items.all():
                for lote_asignado in item.lotes_asignados.all():
                    liberar_cantidad_lote(
                        lote_asignado.lote_ubicacion,
                        lote_asignado.cantidad_asignada
                    )
            
            # Cambiar estado a 'GENERADA' para que se pueda editar
            propuesta.estado = 'GENERADA'
            propuesta.save(update_fields=['estado'])
            
            # La solicitud vuelve a 'VALIDADA' para que se pueda generar otra propuesta
            solicitud = propuesta.solicitud
            solicitud.estado = 'VALIDADA'
            solicitud.save(update_fields=['estado'])
            
            # Registrar en el log de la propuesta
            LogPropuesta.objects.create(
                propuesta=propuesta,
                usuario=usuario,
                accion=\"PROPUESTA CANCELADA\",
                detalles=f\"La propuesta fue cancelada por {usuario.username}. Las cantidades han sido liberadas y la solicitud ha vuelto al estado VALIDADA.\"
            )
        
        return {
            'exito': True,
            'mensaje': f'Propuesta {propuesta.solicitud.folio} cancelada exitosamente. Cantidades liberadas.',
            'propuesta': propuesta
        }
    
    except PropuestaPedido.DoesNotExist:
        return {
            'exito': False,
            'mensaje': 'Propuesta no encontrada'
        }
    except Exception as e:
        return {
            'exito': False,
            'mensaje': f'Error al cancelar propuesta: {str(e)}'
        }


def obtener_cantidad_disponible_real(lote):
    """
    Calcula la cantidad realmente disponible considerando las reservas.
    
    Args:
        lote: Instancia de Lote
    
    Returns:
        int: Cantidad disponible sin considerar reservas
    """
    return lote.cantidad_disponible - lote.cantidad_reservada


def validar_disponibilidad_para_propuesta(producto_id, cantidad_requerida, institucion_id=None):
    """
    Valida si hay suficiente cantidad disponible (sin reservas) para una nueva propuesta.
    
    Args:
        producto_id: ID del producto
        cantidad_requerida: Cantidad que se necesita
        institucion_id: ID de la institución (opcional, para filtrar por institución)
    
    Returns:
        dict: {
            'disponible': bool,
            'cantidad_disponible': int,
            'lotes': list de lotes disponibles con cantidad real
        }
    """
    from .models import Lote
    
    # Obtener lotes disponibles
    query = Lote.objects.filter(
        producto_id=producto_id,
        estado=1  # Solo lotes disponibles
    ).order_by('fecha_caducidad')
    
    if institucion_id:
        query = query.filter(institucion_id=institucion_id)
    
    lotes_disponibles = []
    cantidad_total_disponible = 0
    
    for lote in query:
        cantidad_real = obtener_cantidad_disponible_real(lote)
        if cantidad_real > 0:
            lotes_disponibles.append({
                'lote_id': lote.id,
                'numero_lote': lote.numero_lote,
                'cantidad_disponible': cantidad_real,
                'fecha_caducidad': lote.fecha_caducidad
            })
            cantidad_total_disponible += cantidad_real
    
    return {
        'disponible': cantidad_total_disponible >= cantidad_requerida,
        'cantidad_disponible': cantidad_total_disponible,
        'lotes': lotes_disponibles
    }


def completar_surtimiento_propuesta(propuesta_id):
    """
    Completa el surtimiento de una propuesta.
    Decrementa cantidad_disponible y cantidad_reservada de los lotes.
    
    Args:
        propuesta_id: ID de la propuesta
    
    Returns:
        dict: {'exito': bool, 'mensaje': str}
    """
    try:
        propuesta = PropuestaPedido.objects.get(id=propuesta_id)
        
        if propuesta.estado != 'SURTIDA':
            return {
                'exito': False,
                'mensaje': 'La propuesta debe estar en estado SURTIDA para completar el surtimiento'
            }
        
        with transaction.atomic():
            for item in propuesta.items.all():
                for lote_asignado in item.lotes_asignados.all():
                    if lote_asignado.surtido:
                        lote = lote_asignado.lote_ubicacion.lote
                        cantidad = lote_asignado.cantidad_asignada
                        
                        # Decrementar cantidad_disponible
                        lote.cantidad_disponible = max(0, lote.cantidad_disponible - cantidad)
                        
                        # Decrementar cantidad_reservada
                        lote.cantidad_reservada = max(0, lote.cantidad_reservada - cantidad)
                        
                        lote.save(update_fields=['cantidad_disponible', 'cantidad_reservada'])
        
        return {
            'exito': True,
            'mensaje': 'Surtimiento completado. Cantidades actualizadas en inventario.'
        }
    
    except PropuestaPedido.DoesNotExist:
        return {
            'exito': False,
            'mensaje': 'Propuesta no encontrada'
        }
    except Exception as e:
        return {
            'exito': False,
            'mensaje': f'Error al completar surtimiento: {str(e)}'
        }
