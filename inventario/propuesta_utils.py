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
    Libera todas las cantidades reservadas y devuelve la propuesta al estado GENERADA (editable).
    Permite cambiar los ítems de suministro y generar una nueva propuesta.
    
    Args:
        propuesta_id: ID de la propuesta a liberar
        usuario: Usuario que realiza la acción (para auditoría)
    
    Returns:
        dict: {'exito': bool, 'mensaje': str, 'propuesta': PropuestaPedido, 'cantidad_liberada': int}
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
            # Contar cantidad total a liberar
            cantidad_total_liberada = 0
            detalles_liberacion = []
            
            # Liberar todas las cantidades reservadas
            for item in propuesta.items.all():
                for lote_asignado in item.lotes_asignados.all():
                    cantidad = lote_asignado.cantidad_asignada
                    cantidad_total_liberada += cantidad
                    
                    # Registrar detalles de lo que se libera
                    detalles_liberacion.append(
                        f"Lote {lote_asignado.lote_ubicacion.lote.numero_lote}: {cantidad} unidades"
                    )
                    
                    liberar_cantidad_lote(
                        lote_asignado.lote_ubicacion,
                        cantidad
                    )
            
            # Guardar estado anterior para el log
            estado_anterior = propuesta.get_estado_display()
            
            # Cambiar estado a 'GENERADA' para que sea editable
            propuesta.estado = 'GENERADA'
            propuesta.save(update_fields=['estado'])
            
            # La solicitud permanece en 'VALIDADA' para poder editar la propuesta
            solicitud = propuesta.solicitud
            # No cambiar el estado de la solicitud, ya está en VALIDADA
            
            # Registrar en el log de la propuesta con detalles completos
            detalles_completos = f"""Propuesta liberada por {usuario.username if usuario else 'Sistema'}.
 Estado anterior: {estado_anterior}
 Cantidad total liberada: {cantidad_total_liberada} unidades
 Detalles de liberación:
 - {chr(10).join(detalles_liberacion)}
 La propuesta ha vuelto al estado GENERADA y puede ser editada para cambiar los ítems de suministro."""
            
            LogPropuesta.objects.create(
                propuesta=propuesta,
                usuario=usuario,
                accion="PROPUESTA LIBERADA Y DEVUELTA A EDICIÓN",
                detalles=detalles_completos
            )
        
        return {
            'exito': True,
            'mensaje': f'Propuesta {propuesta.solicitud.folio} liberada exitosamente. Se liberaron {cantidad_total_liberada} unidades y la propuesta está lista para editar.',
            'propuesta': propuesta,
            'cantidad_liberada': cantidad_total_liberada
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
    Valida si hay suficiente cantidad disponible para una nueva propuesta.
    Suma el total disponible de TODOS los lotes del producto, considerando:
    - cantidad_disponible total del producto
    - cantidad_reservada total del producto
    
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
    from django.db.models import Sum
    
    # Obtener lotes disponibles del producto
    query = Lote.objects.filter(
        producto_id=producto_id,
        estado=1  # Solo lotes disponibles
    ).order_by('fecha_caducidad')
    
    if institucion_id:
        query = query.filter(institucion_id=institucion_id)
    
    # Calcular totales del producto
    totales = query.aggregate(
        total_cantidad_disponible=Sum('cantidad_disponible'),
        total_cantidad_reservada=Sum('cantidad_reservada')
    )
    
    total_disponible = totales['total_cantidad_disponible'] or 0
    total_reservada = totales['total_cantidad_reservada'] or 0
    cantidad_total_disponible = total_disponible - total_reservada
    
    # Construir lista de lotes para referencia
    lotes_disponibles = []
    for lote in query:
        cantidad_real = obtener_cantidad_disponible_real(lote)
        if cantidad_real > 0:
            lotes_disponibles.append({
                'lote_id': lote.id,
                'numero_lote': lote.numero_lote,
                'cantidad_disponible': cantidad_real,
                'fecha_caducidad': lote.fecha_caducidad
            })
    
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


def validar_disponibilidad_solicitud(solicitud_id):
    """
    Valida si hay suficiente disponibilidad para TODOS los items de una solicitud.
    Útil para determinar si una solicitud PENDIENTE puede ser validada.
    
    Args:
        solicitud_id: ID de la solicitud
    
    Returns:
        dict: {
            'disponible': bool,
            'items_con_error': list de dicts con detalles de items sin disponibilidad,
            'mensaje_resumen': str con resumen del problema
        }
    """
    from .pedidos_models import SolicitudPedido
    
    try:
        solicitud = SolicitudPedido.objects.prefetch_related('items__producto').get(id=solicitud_id)
    except SolicitudPedido.DoesNotExist:
        return {
            'disponible': False,
            'items_con_error': [],
            'mensaje_resumen': 'Solicitud no encontrada'
        }
    
    items_con_error = []
    todos_disponibles = True
    
    for item in solicitud.items.all():
        if item.cantidad_solicitada > 0:
            resultado = validar_disponibilidad_para_propuesta(
                item.producto.id,
                item.cantidad_solicitada,
                solicitud.institucion_solicitante.id
            )
            
            if not resultado['disponible']:
                todos_disponibles = False
                items_con_error.append({
                    'clave': item.producto.clave_cnis,
                    'descripcion': item.producto.descripcion,
                    'cantidad_solicitada': item.cantidad_solicitada,
                    'cantidad_disponible': resultado['cantidad_disponible'],
                    'diferencia': item.cantidad_solicitada - resultado['cantidad_disponible']
                })
    
    if todos_disponibles:
        mensaje_resumen = 'Todos los productos tienen disponibilidad suficiente'
    else:
        cantidad_items_error = len(items_con_error)
        mensaje_resumen = f'{cantidad_items_error} producto(s) sin disponibilidad suficiente'
    
    return {
        'disponible': todos_disponibles,
        'items_con_error': items_con_error,
        'mensaje_resumen': mensaje_resumen
    }
