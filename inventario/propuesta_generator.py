"""
Lógica de negocio para generar propuestas de pedido automáticamente.

Este módulo contiene las funciones necesarias para:
1. Verificar disponibilidad de inventario considerando ubicaciones.
2. Seleccionar lotes óptimos (considerando caducidad y ubicaciones).
3. Generar una propuesta de surtimiento con información de ubicaciones.
"""

from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone

from .pedidos_models import (
    SolicitudPedido,
    PropuestaPedido,
    ItemPropuesta,
    LoteAsignado
)
from .models import Lote, LoteUbicacion


class PropuestaGenerator:
    """
    Clase que encapsula la lógica para generar una propuesta de pedido.
    Ahora considera las ubicaciones de cada lote.
    """
    
    def __init__(self, solicitud_id, usuario):
        """
        Inicializa el generador con la solicitud y el usuario que genera.
        """
        self.solicitud = SolicitudPedido.objects.get(id=solicitud_id)
        self.usuario = usuario
        self.propuesta = None

    @transaction.atomic
    def generate(self):
        """
        Genera la propuesta de pedido completa.
        """
        if self.solicitud.estado != 'VALIDADA':
            raise ValueError("La solicitud debe estar en estado VALIDADA para generar una propuesta.")

        # Crear la propuesta principal
        self.propuesta = PropuestaPedido.objects.create(
            solicitud=self.solicitud,
            usuario_generacion=self.usuario,
            total_solicitado=sum(item.cantidad_aprobada for item in self.solicitud.items.all())
        )

        # Generar items de la propuesta (solo los que tienen cantidad_aprobada > 0)
        for item_solicitud in self.solicitud.items.filter(cantidad_aprobada__gt=0):
            self._generate_item_propuesta(item_solicitud)

        # Actualizar totales de la propuesta
        self.propuesta.total_disponible = sum(item.cantidad_disponible for item in self.propuesta.items.all())
        self.propuesta.total_propuesto = sum(item.cantidad_propuesta for item in self.propuesta.items.all())
        self.propuesta.save()

        return self.propuesta

    def _generate_item_propuesta(self, item_solicitud):
        """
        Genera un item de la propuesta, buscando lotes disponibles con sus ubicaciones.
        Considera la cantidad reservada en otros lotes.
        """
        from .propuesta_utils import reservar_cantidad_lote
        
        cantidad_requerida = item_solicitud.cantidad_aprobada
        producto = item_solicitud.producto
        
        # Crear el item de la propuesta
        item_propuesta = ItemPropuesta.objects.create(
            propuesta=self.propuesta,
            item_solicitud=item_solicitud,
            producto=producto,
            cantidad_solicitada=cantidad_requerida
        )

        # Buscar lotes disponibles que no estén caducados
        # Considerar que deben tener al menos 60 días de vida útil
        import logging
        logger = logging.getLogger(__name__)
        
        fecha_minima = date.today() + timedelta(days=60)
        lotes_disponibles = Lote.objects.filter(
            producto=producto,
            fecha_caducidad__gte=fecha_minima,
            estado=1  # Solo lotes disponibles
        ).select_related('producto').order_by(
            'fecha_caducidad'  # Priorizar lotes que caducan antes
        )

        # Calcular cantidad total disponible (considerando reservas)
        cantidad_total_disponible = sum(
            max(0, lote.cantidad_disponible - lote.cantidad_reservada) 
            for lote in lotes_disponibles
        )
        
        logger.warning(f"[GENERAR_PROPUESTA] Clave: {producto.clave_cnis} | Requerido: {cantidad_requerida} | Fecha minima: {fecha_minima} | Lotes encontrados: {lotes_disponibles.count()} | Total disponible: {cantidad_total_disponible}")
        for lote in lotes_disponibles:
            disp = lote.cantidad_disponible - lote.cantidad_reservada
            logger.warning(f"  - Lote {lote.numero_lote}: Disponible={lote.cantidad_disponible}, Reservado={lote.cantidad_reservada}, Neto={disp}, Caducidad={lote.fecha_caducidad}")

        item_propuesta.cantidad_disponible = cantidad_total_disponible

        # Asignar lotes
        cantidad_asignada_total = 0
        for lote in lotes_disponibles:
            if cantidad_asignada_total >= cantidad_requerida:
                break

            # Calcular cantidad real disponible (sin reservas) a nivel de lote
            cantidad_real_disponible_lote = max(0, lote.cantidad_disponible - lote.cantidad_reservada)
            
            if cantidad_real_disponible_lote <= 0:
                continue

            # Calcular cuánto necesitamos aún
            cantidad_faltante = cantidad_requerida - cantidad_asignada_total
            
            # No podemos asignar más de lo disponible en el lote
            cantidad_maxima_a_asignar = min(
                cantidad_real_disponible_lote,
                cantidad_faltante
            )

            if cantidad_maxima_a_asignar <= 0:
                continue

            # Distribuir la reserva entre las ubicaciones del lote
            # Esto permite que el almacenista sepa exactamente de qué ubicación tomar
            # Solo considerar ubicaciones del almacén con id=1
            ubicaciones_disponibles = lote.ubicaciones_detalle.filter(
                cantidad__gt=0,
                ubicacion__almacen_id=1  # Solo ubicaciones del almacén con id=1
            ).order_by('-cantidad')  # Priorizar ubicaciones con más cantidad
            
            # Calcular la cantidad total disponible en todas las ubicaciones del lote
            cantidad_total_disponible_ubicaciones = sum(
                max(0, lu.cantidad - lu.cantidad_reservada) 
                for lu in ubicaciones_disponibles
            )
            
            # No podemos asignar más de lo disponible en las ubicaciones
            cantidad_maxima_por_ubicaciones = min(
                cantidad_total_disponible_ubicaciones,
                cantidad_maxima_a_asignar
            )
            
            if cantidad_maxima_por_ubicaciones <= 0:
                logger.warning(f"  - Lote {lote.numero_lote}: No hay suficiente disponible en ubicaciones (lote: {cantidad_real_disponible_lote}, ubicaciones: {cantidad_total_disponible_ubicaciones})")
                continue
            
            cantidad_pendiente_reservar = cantidad_maxima_por_ubicaciones
            ubicaciones_asignadas = []  # Para crear LoteAsignado después
            cantidad_total_reservada_en_iteracion = 0  # Para validar que no excedamos
            
            # Distribuir la reserva entre ubicaciones
            for lote_ubicacion in ubicaciones_disponibles:
                if cantidad_pendiente_reservar <= 0:
                    break
                
                # Calcular cuánto podemos reservar de esta ubicación
                # Considerar: cantidad en ubicación - cantidad ya reservada en ubicación
                cantidad_disponible_ubicacion = max(0, lote_ubicacion.cantidad - lote_ubicacion.cantidad_reservada)
                
                if cantidad_disponible_ubicacion <= 0:
                    continue
                
                cantidad_a_reservar_ubicacion = min(
                    cantidad_disponible_ubicacion,
                    cantidad_pendiente_reservar
                )
                
                # Validación adicional: asegurar que no excedamos la cantidad disponible del lote
                if cantidad_total_reservada_en_iteracion + cantidad_a_reservar_ubicacion > cantidad_real_disponible_lote:
                    cantidad_a_reservar_ubicacion = max(0, cantidad_real_disponible_lote - cantidad_total_reservada_en_iteracion)
                
                if cantidad_a_reservar_ubicacion > 0:
                    # Reservar en la ubicación
                    lote_ubicacion.cantidad_reservada += cantidad_a_reservar_ubicacion
                    lote_ubicacion.save(update_fields=['cantidad_reservada'])
                    
                    # También actualizar la reserva a nivel de lote
                    lote.cantidad_reservada += cantidad_a_reservar_ubicacion
                    lote.save(update_fields=['cantidad_reservada'])
                    
                    # Guardar para crear LoteAsignado después
                    ubicaciones_asignadas.append({
                        'lote_ubicacion': lote_ubicacion,
                        'cantidad': cantidad_a_reservar_ubicacion
                    })
                    
                    cantidad_pendiente_reservar -= cantidad_a_reservar_ubicacion
                    cantidad_total_reservada_en_iteracion += cantidad_a_reservar_ubicacion
                    cantidad_asignada_total += cantidad_a_reservar_ubicacion
                    
                    logger.warning(f"  - Lote {lote.numero_lote} Ubicación {lote_ubicacion.ubicacion.codigo}: Reservando {cantidad_a_reservar_ubicacion} (Disponible ubicación: {cantidad_disponible_ubicacion}, Disponible lote: {cantidad_real_disponible_lote})")
                else:
                    break
            
            # Validación final: verificar que no hayamos excedido la cantidad disponible del lote
            if cantidad_total_reservada_en_iteracion > cantidad_real_disponible_lote:
                logger.error(f"  - ERROR: Se reservó {cantidad_total_reservada_en_iteracion} pero solo había {cantidad_real_disponible_lote} disponible en lote {lote.numero_lote}")
                # Revertir las reservas si excedimos
                for asignacion in ubicaciones_asignadas:
                    lote_ubicacion = asignacion['lote_ubicacion']
                    cantidad = asignacion['cantidad']
                    lote_ubicacion.cantidad_reservada = max(0, lote_ubicacion.cantidad_reservada - cantidad)
                    lote_ubicacion.save(update_fields=['cantidad_reservada'])
                    lote.cantidad_reservada = max(0, lote.cantidad_reservada - cantidad)
                lote.save(update_fields=['cantidad_reservada'])
                ubicaciones_asignadas = []
                continue
            
            # Si se pudo reservar todo (o parte), crear los registros LoteAsignado
            if ubicaciones_asignadas:
                for asignacion in ubicaciones_asignadas:
                    LoteAsignado.objects.create(
                        item_propuesta=item_propuesta,
                        lote_ubicacion=asignacion['lote_ubicacion'],
                        cantidad_asignada=asignacion['cantidad']
                    )
                logger.warning(f"  - Lote {lote.numero_lote}: Total reservado en esta iteración: {cantidad_total_reservada_en_iteracion} de {cantidad_real_disponible_lote} disponible")
            else:
                # Si no se pudo reservar nada, continuar con el siguiente lote
                logger.warning(f"  - No se pudo reservar ninguna cantidad del lote {lote.numero_lote}")
                continue

        # Actualizar estado y cantidad propuesta
        item_propuesta.cantidad_propuesta = cantidad_asignada_total
        if cantidad_asignada_total == 0:
            item_propuesta.estado = 'NO_DISPONIBLE'
            item_propuesta.observaciones = "No hay lotes disponibles que cumplan con las reglas de caducidad."
        elif cantidad_asignada_total < cantidad_requerida:
            item_propuesta.estado = 'PARCIAL'
            item_propuesta.observaciones = f"Solo se encontraron {cantidad_asignada_total} de {cantidad_requerida} unidades."
        else:
            item_propuesta.estado = 'DISPONIBLE'
        
        item_propuesta.save()
