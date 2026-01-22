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

            # Calcular cantidad real disponible (sin reservas)
            cantidad_real_disponible = max(0, lote.cantidad_disponible - lote.cantidad_reservada)
            
            if cantidad_real_disponible <= 0:
                continue

            cantidad_a_asignar = min(
                cantidad_real_disponible,
                cantidad_requerida - cantidad_asignada_total
            )

            if cantidad_a_asignar > 0:
                # Distribuir la reserva entre las ubicaciones del lote
                # Esto permite que el almacenista sepa exactamente de qué ubicación tomar
                ubicaciones_disponibles = lote.ubicaciones_detalle.filter(
                    cantidad__gt=0
                ).order_by('-cantidad')  # Priorizar ubicaciones con más cantidad
                
                cantidad_pendiente_reservar = cantidad_a_asignar
                ubicaciones_asignadas = []  # Para crear LoteAsignado después
                
                # Verificar primero que tenemos suficiente disponible a nivel de lote
                if cantidad_real_disponible < cantidad_a_asignar:
                    logger.warning(f"  - No hay suficiente disponible en lote {lote.numero_lote}: requiere {cantidad_a_asignar}, disponible {cantidad_real_disponible}")
                    continue
                
                # Distribuir la reserva entre ubicaciones
                for lote_ubicacion in ubicaciones_disponibles:
                    if cantidad_pendiente_reservar <= 0:
                        break
                    
                    # Calcular cuánto podemos reservar de esta ubicación
                    # Considerar: cantidad en ubicación - cantidad ya reservada en ubicación
                    cantidad_disponible_ubicacion = lote_ubicacion.cantidad - lote_ubicacion.cantidad_reservada
                    
                    if cantidad_disponible_ubicacion <= 0:
                        continue
                    
                    cantidad_a_reservar_ubicacion = min(
                        cantidad_disponible_ubicacion,
                        cantidad_pendiente_reservar
                    )
                    
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
                        cantidad_asignada_total += cantidad_a_reservar_ubicacion
                
                # Si se pudo reservar todo (o parte), crear los registros LoteAsignado
                if ubicaciones_asignadas:
                    for asignacion in ubicaciones_asignadas:
                        LoteAsignado.objects.create(
                            item_propuesta=item_propuesta,
                            lote_ubicacion=asignacion['lote_ubicacion'],
                            cantidad_asignada=asignacion['cantidad']
                        )
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
