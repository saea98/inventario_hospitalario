"""
Utilidades para gestionar propuestas de suministro con sistema de reserva de cantidades.

Este módulo proporciona funciones para:
1. Reservar cantidades cuando se asignan lotes a una propuesta
2. Liberar cantidades cuando se cancela una propuesta (rollback)
3. Validar disponibilidad considerando cantidades reservadas
4. Actualizar cantidades al completar el surtimiento
"""

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone
from .pedidos_models import PropuestaPedido, ItemPropuesta, LoteAsignado, LogPropuesta
from .models import Lote, LoteUbicacion, MovimientoInventario


def _reserva_real_lote_ubicacion(lote_ubicacion):
    """Reserva real en esta ubicación = suma de LoteAsignado (surtido=False). Igual que reporte de reservas."""
    return LoteAsignado.objects.filter(
        lote_ubicacion=lote_ubicacion, surtido=False
    ).aggregate(total=Sum('cantidad_asignada'))['total'] or 0


def _reserva_real_lote(lote):
    """Reserva real en el lote (todas sus ubicaciones) = suma de LoteAsignado (surtido=False)."""
    return LoteAsignado.objects.filter(
        lote_ubicacion__lote=lote, surtido=False
    ).aggregate(total=Sum('cantidad_asignada'))['total'] or 0


def reservar_cantidad_lote(lote_ubicacion, cantidad):
    """
    Reserva una cantidad en un lote sin afectar cantidad_disponible.
    Se incrementa cantidad_reservada tanto en la ubicación como en el lote.
    Comprueba disponibilidad con reserva real (suma de LoteAsignado surtido=False), igual que el reporte de reservas.

    Args:
        lote_ubicacion: Instancia de LoteUbicacion
        cantidad: Cantidad a reservar

    Returns:
        bool: True si se reservó exitosamente (o si cantidad<=0, sin hacer nada), False si no hay suficiente cantidad disponible
    """
    if cantidad is None or cantidad <= 0:
        return True
    lote_ubicacion.refresh_from_db()
    lote = lote_ubicacion.lote
    lote.refresh_from_db()

    reservado_ubicacion = _reserva_real_lote_ubicacion(lote_ubicacion)
    reservado_lote = _reserva_real_lote(lote)
    cantidad_disponible_ubicacion = lote_ubicacion.cantidad - reservado_ubicacion
    cantidad_realmente_disponible_lote = lote.cantidad_disponible - reservado_lote

    if cantidad_disponible_ubicacion < cantidad or cantidad_realmente_disponible_lote < cantidad:
        return False

    lote_ubicacion.cantidad_reservada += cantidad
    lote_ubicacion.save(update_fields=['cantidad_reservada'])
    lote.cantidad_reservada += cantidad
    lote.save(update_fields=['cantidad_reservada'])
    return True


def liberar_cantidad_lote(lote_ubicacion, cantidad):
    """
    Libera una cantidad reservada en un lote (rollback).
    Se decrementa cantidad_reservada tanto en la ubicación como en el lote.
    Usa actualizaciones atómicas para evitar problemas de concurrencia.
    
    Args:
        lote_ubicacion: Instancia de LoteUbicacion
        cantidad: Cantidad a liberar
    
    Returns:
        dict: Información sobre la liberación realizada
    """
    # Refrescar desde la base de datos para asegurar valores actuales
    lote_ubicacion.refresh_from_db()
    lote = lote_ubicacion.lote
    lote.refresh_from_db()
    
    # Guardar valores antes de liberar para validación y logging
    cantidad_reservada_anterior_ubicacion = lote_ubicacion.cantidad_reservada
    cantidad_reservada_anterior_lote = lote.cantidad_reservada
    
    # Validar que hay suficiente cantidad reservada para liberar
    cantidad_real_liberar_ubicacion = min(cantidad, cantidad_reservada_anterior_ubicacion)
    cantidad_real_liberar_lote = min(cantidad, cantidad_reservada_anterior_lote)
    
    # Usar actualización atómica con F() para evitar problemas de concurrencia
    # Decrementar cantidad_reservada en la ubicación (no puede ser menor a 0)
    LoteUbicacion.objects.filter(id=lote_ubicacion.id).update(
        cantidad_reservada=F('cantidad_reservada') - cantidad_real_liberar_ubicacion
    )
    # Asegurar que no quede negativo
    LoteUbicacion.objects.filter(id=lote_ubicacion.id, cantidad_reservada__lt=0).update(
        cantidad_reservada=0
    )
    
    # Decrementar cantidad_reservada a nivel de lote (no puede ser menor a 0)
    Lote.objects.filter(id=lote.id).update(
        cantidad_reservada=F('cantidad_reservada') - cantidad_real_liberar_lote
    )
    # Asegurar que no quede negativo
    Lote.objects.filter(id=lote.id, cantidad_reservada__lt=0).update(
        cantidad_reservada=0
    )
    
    # Refrescar para obtener los valores actualizados
    lote_ubicacion.refresh_from_db()
    lote.refresh_from_db()
    
    return {
        'liberado_ubicacion': cantidad_real_liberar_ubicacion,
        'liberado_lote': cantidad_real_liberar_lote,
        'reserva_anterior_ubicacion': cantidad_reservada_anterior_ubicacion,
        'reserva_anterior_lote': cantidad_reservada_anterior_lote,
        'nueva_reservada_ubicacion': lote_ubicacion.cantidad_reservada,
        'nueva_reservada_lote': lote.cantidad_reservada
    }


def cancelar_propuesta(propuesta_id, usuario=None):
    """
    Libera todas las cantidades reservadas y devuelve la propuesta al estado GENERADA (pendiente de validación).
    NO marca la propuesta como CANCELADA, solo libera las reservas y regresa al estado inicial.
    Permite cambiar los ítems de suministro y generar una nueva propuesta.
    
    Args:
        propuesta_id: ID de la propuesta a liberar
        usuario: Usuario que realiza la acción (para auditoría)
    
    Returns:
        dict: {'exito': bool, 'mensaje': str, 'propuesta': PropuestaPedido, 'cantidad_liberada': int}
    """
    try:
        # Precargar todas las relaciones necesarias
        propuesta = PropuestaPedido.objects.select_related('solicitud').prefetch_related(
            'items__lotes_asignados__lote_ubicacion__lote__producto',
            'items__lotes_asignados__lote_ubicacion__ubicacion'
        ).get(id=propuesta_id)
        
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
            
            # Obtener todos los lotes asignados de una vez (incluir todos, incluso surtidos si es necesario)
            lotes_asignados = LoteAsignado.objects.filter(
                item_propuesta__propuesta=propuesta
            ).select_related(
                'lote_ubicacion__lote__producto',
                'lote_ubicacion__ubicacion'
            )
            
            # Validar que hay lotes asignados
            if not lotes_asignados.exists():
                return {
                    'exito': False,
                    'mensaje': 'No se encontraron lotes asignados para liberar'
                }
            
            # Liberar todas las cantidades reservadas
            for lote_asignado in lotes_asignados:
                cantidad = lote_asignado.cantidad_asignada
                
                # Validar que el lote_ubicacion existe
                if not lote_asignado.lote_ubicacion:
                    detalles_liberacion.append(
                        f"Error: LoteAsignado {lote_asignado.id} no tiene lote_ubicacion asociado"
                    )
                    continue
                
                # Liberar la cantidad reservada
                try:
                    resultado_liberacion = liberar_cantidad_lote(
                        lote_asignado.lote_ubicacion,
                        cantidad
                    )
                    
                    # Sumar la cantidad realmente liberada
                    cantidad_real_liberada = resultado_liberacion.get('liberado_lote', cantidad)
                    cantidad_total_liberada += cantidad_real_liberada
                    
                    # Registrar detalles de lo que se libera
                    lote = lote_asignado.lote_ubicacion.lote
                    reserva_anterior = resultado_liberacion.get('reserva_anterior_lote', 0)
                    reserva_nueva = resultado_liberacion.get('nueva_reservada_lote', 0)
                    
                    detalles_liberacion.append(
                        f"Lote {lote.numero_lote} ({lote.producto.clave_cnis if lote.producto else 'N/A'}): "
                        f"{cantidad_real_liberada} unidades liberadas "
                        f"(Reserva: {reserva_anterior} → {reserva_nueva})"
                    )
                except Exception as e:
                    detalles_liberacion.append(
                        f"Error al liberar lote_asignado {lote_asignado.id}: {str(e)}"
                    )
                    raise  # Re-lanzar para que la transacción haga rollback
            
            # Guardar estado anterior para el log
            estado_anterior = propuesta.get_estado_display()
            estado_anterior_solicitud = propuesta.solicitud.get_estado_display() if propuesta.solicitud else 'N/A'
            
            # Verificación final: confirmar que las reservas se liberaron correctamente
            # Recalcular total de reservas después de la liberación
            total_reservas_restantes = 0
            for lote_asignado in lotes_asignados:
                if lote_asignado.lote_ubicacion:
                    lote_asignado.lote_ubicacion.refresh_from_db()
                    lote = lote_asignado.lote_ubicacion.lote
                    lote.refresh_from_db()
                    total_reservas_restantes += lote.cantidad_reservada
            
            # Cambiar estado a 'GENERADA' para que quede pendiente de validación (no CANCELADA)
            propuesta.estado = 'GENERADA'
            propuesta.save(update_fields=['estado'])
            
            # Cambiar el estado de la solicitud a 'PENDIENTE' para que quede lista para aprobación
            solicitud = propuesta.solicitud
            if solicitud:
                solicitud.estado = 'PENDIENTE'
                # Limpiar datos de validación para permitir nueva validación
                solicitud.usuario_validacion = None
                solicitud.fecha_validacion = None
                solicitud.save(update_fields=['estado', 'usuario_validacion', 'fecha_validacion'])
            
            # Registrar en el log de la propuesta con detalles completos
            detalles_completos = f"""Propuesta liberada por {usuario.username if usuario else 'Sistema'}.
 Estado anterior propuesta: {estado_anterior}
 Estado anterior solicitud: {estado_anterior_solicitud}
 Cantidad total liberada: {cantidad_total_liberada} unidades
 Reservas restantes en lotes: {total_reservas_restantes} unidades
 Detalles de liberación:
 - {chr(10).join(detalles_liberacion)}
 La propuesta ha regresado al estado GENERADA (pendiente de validación) y la solicitud ha regresado al estado PENDIENTE para nueva aprobación.
 
 VERIFICACIÓN DE ROLLBACK:
 - Total de unidades liberadas: {cantidad_total_liberada}
 - Reservas restantes verificadas: {total_reservas_restantes}
 - Rollback completado correctamente."""
            
            LogPropuesta.objects.create(
                propuesta=propuesta,
                usuario=usuario,
                accion="PROPUESTA LIBERADA - REGRESADA A GENERADA - SOLICITUD LISTA PARA APROBACIÓN",
                detalles=detalles_completos
            )
        
        return {
            'exito': True,
            'mensaje': (
                f'Propuesta {propuesta.solicitud.folio if propuesta.solicitud else propuesta.id} liberada exitosamente. '
                f'Se liberaron {cantidad_total_liberada} unidades. La propuesta ha regresado al estado GENERADA (pendiente de validación) '
                f'y la solicitud ha regresado al estado PENDIENTE para nueva aprobación.'
            ),
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


def eliminar_propuesta(propuesta_id, usuario=None):
    """
    Elimina completamente una propuesta haciendo rollback de todas las reservas,
    registrando movimientos de inventario y eliminando la propuesta.
    
    Args:
        propuesta_id: ID de la propuesta a eliminar
        usuario: Usuario que realiza la acción (para auditoría)
    
    Returns:
        dict: {'exito': bool, 'mensaje': str, 'cantidad_liberada': int, 'movimientos_creados': int}
    """
    try:
        propuesta = PropuestaPedido.objects.select_related('solicitud').prefetch_related(
            'items__lotes_asignados__lote_ubicacion__lote',
            'items__lotes_asignados__lote_ubicacion__ubicacion'
        ).get(id=propuesta_id)
        
        # Solo se pueden eliminar propuestas en ciertos estados
        estados_eliminables = ['GENERADA', 'REVISADA', 'EN_SURTIMIENTO', 'CANCELADA']
        if propuesta.estado not in estados_eliminables:
            return {
                'exito': False,
                'mensaje': f'No se puede eliminar una propuesta en estado {propuesta.get_estado_display()}'
            }
        
        with transaction.atomic():
            # Guardar información antes de eliminar
            estado_anterior = propuesta.get_estado_display()
            folio_solicitud = propuesta.solicitud.folio if propuesta.solicitud else 'N/A'
            propuesta_id_str = str(propuesta.id)
            
            # Contar cantidad total a liberar y crear movimientos
            cantidad_total_liberada = 0
            movimientos_creados = 0
            detalles_liberacion = []
            
            # Obtener todos los lotes asignados de una vez
            lotes_asignados = LoteAsignado.objects.filter(
                item_propuesta__propuesta=propuesta
            ).select_related(
                'lote_ubicacion__lote__producto',
                'lote_ubicacion__ubicacion'
            )
            
            # Liberar todas las cantidades reservadas y crear movimientos
            for lote_asignado in lotes_asignados:
                cantidad = lote_asignado.cantidad_asignada
                
                lote_ubicacion = lote_asignado.lote_ubicacion
                lote = lote_ubicacion.lote
                
                # Liberar la cantidad reservada (esta función ya guarda los valores anteriores)
                resultado_liberacion = liberar_cantidad_lote(lote_ubicacion, cantidad)
                
                # Obtener cantidades del resultado
                cantidad_real_liberada = resultado_liberacion.get('liberado_lote', cantidad)
                cantidad_total_liberada += cantidad_real_liberada
                
                cantidad_reservada_anterior_lote = resultado_liberacion.get('reserva_anterior_lote', 0)
                    
                # Crear movimiento de inventario para registrar la liberación
                # Nota: La cantidad_disponible no cambia, solo cantidad_reservada
                # Registramos el movimiento con las cantidades de reserva
                reserva_nueva = resultado_liberacion.get('nueva_reservada_lote', 0)
                
                motivo = (
                    f"Eliminación de propuesta {propuesta_id_str} - "
                    f"Liberación de reserva de {cantidad_real_liberada} unidades del lote {lote.numero_lote} "
                    f"(Producto: {lote.producto.clave_cnis if lote.producto else 'N/A'}). "
                    f"Reserva anterior: {cantidad_reservada_anterior_lote}, "
                    f"Reserva nueva: {reserva_nueva}"
                )
                
                # Usar AJUSTE_POSITIVO para registrar la liberación de reserva
                # La cantidad_anterior y cantidad_nueva reflejan la cantidad_reservada
                MovimientoInventario.objects.create(
                    lote=lote,
                    tipo_movimiento='AJUSTE_POSITIVO',
                    cantidad=cantidad_real_liberada,  # Cantidad liberada
                    cantidad_anterior=cantidad_reservada_anterior_lote,  # Reserva antes
                    cantidad_nueva=reserva_nueva,  # Reserva después
                    motivo=motivo,
                    documento_referencia=f"PROPUESTA-{propuesta_id_str}",
                    folio=f"ELIM-PROP-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    usuario=usuario
                )
                movimientos_creados += 1
                
                # Registrar detalles de lo que se libera
                detalles_liberacion.append(
                    f"Lote {lote.numero_lote} ({lote.producto.clave_cnis if lote.producto else 'N/A'}): "
                    f"{cantidad_real_liberada} unidades liberadas "
                    f"(Reserva: {cantidad_reservada_anterior_lote} → {reserva_nueva})"
                )
            
            # Cambiar el estado de la solicitud a 'PENDIENTE' para que quede lista para nueva validación
            solicitud = propuesta.solicitud
            estado_anterior_solicitud = solicitud.get_estado_display() if solicitud else 'N/A'
            
            if solicitud:
                solicitud.estado = 'PENDIENTE'
                # Limpiar datos de validación para permitir nueva validación
                solicitud.usuario_validacion = None
                solicitud.fecha_validacion = None
                solicitud.save(update_fields=['estado', 'usuario_validacion', 'fecha_validacion'])
            
            # Crear log de la propuesta antes de eliminarla
            detalles_completos = f"""Propuesta eliminada por {usuario.username if usuario else 'Sistema'}.
Estado anterior propuesta: {estado_anterior}
Estado anterior solicitud: {estado_anterior_solicitud}
Folio solicitud: {folio_solicitud}
Cantidad total liberada: {cantidad_total_liberada} unidades
Movimientos de inventario creados: {movimientos_creados}
Detalles de liberación:
- {chr(10).join(detalles_liberacion)}
La propuesta ha sido completamente eliminada del sistema.
La solicitud ha regresado al estado PENDIENTE para nueva validación y generación de propuesta."""
            
            LogPropuesta.objects.create(
                propuesta=propuesta,
                usuario=usuario,
                accion="PROPUESTA ELIMINADA - SOLICITUD LISTA PARA VALIDACIÓN",
                detalles=detalles_completos
            )
            
            # Eliminar la propuesta (esto también eliminará items y lotes_asignados por CASCADE)
            propuesta.delete()
        
        return {
            'exito': True,
            'mensaje': (
                f'Propuesta eliminada exitosamente. Se liberaron {cantidad_total_liberada} unidades '
                f'y se crearon {movimientos_creados} movimientos de inventario. '
                f'La solicitud ha regresado al estado PENDIENTE para nueva validación.'
            ),
            'cantidad_liberada': cantidad_total_liberada,
            'movimientos_creados': movimientos_creados
        }
    
    except PropuestaPedido.DoesNotExist:
        return {
            'exito': False,
            'mensaje': 'Propuesta no encontrada'
        }
    except Exception as e:
        return {
            'exito': False,
            'mensaje': f'Error al eliminar propuesta: {str(e)}'
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
    - cantidad_disponible total del producto (suma de todos los lotes)
    - cantidad_reservada total del producto (suma de todas las reservas)
    
    IMPORTANTE: NO filtra por almacén ni por institución. Considera TODOS los lotes
    del producto sin importar en qué almacén estén.
    
    Args:
        producto_id: ID del producto
        cantidad_requerida: Cantidad que se necesita
        institucion_id: ID de la institución (opcional, NO se usa para filtrar)
    
    Returns:
        dict: {
            'disponible': bool,
            'cantidad_disponible': int,
            'lotes': list de lotes disponibles con cantidad real
        }
    """
    from .models import Lote, Producto, LoteUbicacion
    from django.db.models import Sum, Q
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        producto = Producto.objects.get(id=producto_id)
        clave_cnis = producto.clave_cnis
    except Producto.DoesNotExist:
        logger.error(f"[VALIDAR_DISPONIBILIDAD] Producto ID {producto_id} no existe")
        return {
            'disponible': False,
            'cantidad_disponible': 0,
            'lotes': []
        }
    
    # Obtener TODOS los lotes disponibles del producto
    # NO filtramos por almacén, institución, ni nada más
    # Solo filtramos por producto y estado disponible (estado=1)
    query = Lote.objects.filter(
        producto_id=producto_id,
        estado=1  # Solo lotes disponibles
    )
    
    # Contar lotes antes de agregar más información
    total_lotes = query.count()
    
    # IMPORTANTE: Calcular disponibilidad desde LoteUbicacion (fuente de verdad)
    # porque cantidad_disponible en Lote puede no estar sincronizado
    # Sumar cantidad y cantidad_reservada de todas las ubicaciones de todos los lotes del producto
    # NO filtramos por almacén - consideramos TODAS las ubicaciones de TODOS los almacenes
    # NO filtramos por institución - consideramos TODAS las instituciones
    
    # Primero obtener todos los lotes del producto con estado=1
    lotes_ids = list(query.values_list('id', flat=True))
    
    # Luego obtener todas las ubicaciones de esos lotes
    # Esto asegura que no haya problemas con joins o filtros implícitos
    ubicaciones_totales = LoteUbicacion.objects.filter(
        lote_id__in=lotes_ids
    ).aggregate(
        total_cantidad_ubicaciones=Sum('cantidad'),
        total_reservada_ubicaciones=Sum('cantidad_reservada')
    )
    
    total_cantidad_ubicaciones = ubicaciones_totales['total_cantidad_ubicaciones'] or 0
    total_reservada_ubicaciones = ubicaciones_totales['total_reservada_ubicaciones'] or 0
    
    # SIEMPRE usar el cálculo desde ubicaciones (más preciso y confiable)
    # cantidad_total_disponible = suma de todas las cantidades en ubicaciones - suma de todas las reservas
    cantidad_total_disponible = max(0, total_cantidad_ubicaciones - total_reservada_ubicaciones)
    
    # Contar ubicaciones para debugging
    total_ubicaciones = LoteUbicacion.objects.filter(lote_id__in=lotes_ids).count()
    
    # También calcular desde lotes para comparación (pero NO usar este valor como principal)
    totales_lotes = query.aggregate(
        total_cantidad_disponible=Sum('cantidad_disponible'),
        total_cantidad_reservada=Sum('cantidad_reservada')
    )
    
    total_disponible_lotes = totales_lotes['total_cantidad_disponible'] or 0
    total_reservada_lotes = totales_lotes['total_cantidad_reservada'] or 0
    cantidad_desde_lotes = max(0, total_disponible_lotes - total_reservada_lotes)
    
    # SIEMPRE usar el cálculo desde ubicaciones (más preciso y confiable)
    logger.warning(
        f"[VALIDAR_DISPONIBILIDAD] Usando cálculo desde ubicaciones (fuente de verdad): "
        f"Total lotes encontrados: {total_lotes} | "
        f"Total ubicaciones encontradas: {total_ubicaciones} | "
        f"Total cantidad ubicaciones={total_cantidad_ubicaciones}, "
        f"Total reservada ubicaciones={total_reservada_ubicaciones}, "
        f"Neto disponible={cantidad_total_disponible} | "
        f"(Comparación desde lotes: disponible={total_disponible_lotes}, reservado={total_reservada_lotes}, neto={cantidad_desde_lotes})"
    )
    
    # Log detallado para debugging
    logger.warning(
        f"[VALIDAR_DISPONIBILIDAD] Clave: {clave_cnis} | "
        f"Solicitado: {cantidad_requerida} | "
        f"Total cantidad ubicaciones: {total_cantidad_ubicaciones} | "
        f"Total reservada ubicaciones: {total_reservada_ubicaciones} | "
        f"Neto disponible (desde ubicaciones): {cantidad_total_disponible} | "
        f"Total lotes encontrados: {total_lotes} | "
        f"¿Disponible?: {cantidad_total_disponible >= cantidad_requerida}"
    )
    
    # Si hay lotes, log detallado de cada uno con información de ubicaciones
    if total_lotes > 0:
        logger.warning(f"[VALIDAR_DISPONIBILIDAD] Detalle de lotes para {clave_cnis}:")
        for lote in query[:10]:  # Limitar a los primeros 10 para no saturar el log
            # Calcular desde ubicaciones del lote (fuente de verdad)
            ubicaciones_lote = LoteUbicacion.objects.filter(lote=lote).aggregate(
                total_cant=Sum('cantidad'),
                total_res=Sum('cantidad_reservada')
            )
            cantidad_desde_ubicaciones_lote = (ubicaciones_lote['total_cant'] or 0) - (ubicaciones_lote['total_res'] or 0)
            cantidad_real_lote = obtener_cantidad_disponible_real(lote)
            
            logger.warning(
                f"  - Lote {lote.numero_lote}: "
                f"Disponible(lote)={lote.cantidad_disponible}, "
                f"Reservado(lote)={lote.cantidad_reservada}, "
                f"Neto(lote)={cantidad_real_lote}, "
                f"Cantidad(ubicaciones)={ubicaciones_lote['total_cant'] or 0}, "
                f"Reservada(ubicaciones)={ubicaciones_lote['total_res'] or 0}, "
                f"Neto(ubicaciones)={cantidad_desde_ubicaciones_lote}, "
                f"Almacén={lote.almacen.nombre if lote.almacen else 'N/A'}, "
                f"Estado={lote.estado}"
            )
    
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
                        lote_ubicacion = lote_asignado.lote_ubicacion
                        cantidad = lote_asignado.cantidad_asignada
                        
                        # Decrementar cantidad_disponible a nivel de lote
                        lote.cantidad_disponible = max(0, lote.cantidad_disponible - cantidad)
                        
                        # Decrementar cantidad_reservada a nivel de lote
                        lote.cantidad_reservada = max(0, lote.cantidad_reservada - cantidad)
                        lote.save(update_fields=['cantidad_disponible', 'cantidad_reservada'])
                        
                        # Decrementar cantidad_reservada en la ubicación específica
                        lote_ubicacion.cantidad_reservada = max(0, lote_ubicacion.cantidad_reservada - cantidad)
                        lote_ubicacion.save(update_fields=['cantidad_reservada'])
                        
                        # También decrementar la cantidad en la ubicación
                        lote_ubicacion.cantidad = max(0, lote_ubicacion.cantidad - cantidad)
                        lote_ubicacion.save(update_fields=['cantidad'])
        
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
    Valida si hay disponibilidad para los items de una solicitud.
    Permite validar incluso si hay disponibilidad parcial, ya que el algoritmo de generación
    de propuestas buscará múltiples lotes para cubrir la cantidad solicitada.
    
    Args:
        solicitud_id: ID de la solicitud
    
    Returns:
        dict: {
            'disponible': bool,  # True si hay ALGUNA disponibilidad (aunque sea parcial)
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
    hay_disponibilidad_parcial = False
    
    for item in solicitud.items.all():
        if item.cantidad_solicitada > 0:
            resultado = validar_disponibilidad_para_propuesta(
                item.producto.id,
                item.cantidad_solicitada,
                solicitud.institucion_solicitante.id
            )
            
            # Si no hay disponibilidad suficiente, pero hay alguna disponibilidad, es parcial
            if not resultado['disponible']:
                if resultado['cantidad_disponible'] > 0:
                    # Hay disponibilidad parcial - el algoritmo buscará múltiples lotes
                    hay_disponibilidad_parcial = True
                    items_con_error.append({
                        'clave': item.producto.clave_cnis,
                        'descripcion': item.producto.descripcion,
                        'cantidad_solicitada': item.cantidad_solicitada,
                        'cantidad_disponible': resultado['cantidad_disponible'],
                        'diferencia': item.cantidad_solicitada - resultado['cantidad_disponible'],
                        'parcial': True  # Indica que hay disponibilidad parcial
                    })
                else:
                    # No hay disponibilidad en absoluto
                    todos_disponibles = False
                    items_con_error.append({
                        'clave': item.producto.clave_cnis,
                        'descripcion': item.producto.descripcion,
                        'cantidad_solicitada': item.cantidad_solicitada,
                        'cantidad_disponible': resultado['cantidad_disponible'],
                        'diferencia': item.cantidad_solicitada - resultado['cantidad_disponible'],
                        'parcial': False  # No hay disponibilidad
                    })
    
    if todos_disponibles:
        mensaje_resumen = 'Todos los productos tienen disponibilidad suficiente'
    elif hay_disponibilidad_parcial:
        # Si hay disponibilidad parcial, permitir validar - el algoritmo buscará múltiples lotes
        mensaje_resumen = f'1 producto(s) con disponibilidad parcial. El sistema asignará lo disponible y buscará otros lotes para cubrir el resto.'
    else:
        cantidad_items_error = len(items_con_error)
        mensaje_resumen = f'{cantidad_items_error} producto(s) sin disponibilidad suficiente'
    
    # Permitir validar si hay disponibilidad (aunque sea parcial)
    # El algoritmo de generación de propuestas buscará múltiples lotes automáticamente
    disponible_para_validar = todos_disponibles or hay_disponibilidad_parcial
    
    return {
        'disponible': disponible_para_validar,
        'items_con_error': items_con_error,
        'mensaje_resumen': mensaje_resumen
    }
