"""
Lógica de negocio para generar propuestas de pedido automáticamente.

Este módulo contiene las funciones necesarias para:
1. Verificar disponibilidad de inventario.
2. Seleccionar lotes óptimos (considerando caducidad).
3. Generar una propuesta de surtimiento.
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
from .models import Lote


class PropuestaGenerator:
    """
    Clase que encapsula la lógica para generar una propuesta de pedido.
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

        # Generar items de la propuesta
        for item_solicitud in self.solicitud.items.all():
            self._generate_item_propuesta(item_solicitud)

        # Actualizar totales de la propuesta
        self.propuesta.total_disponible = sum(item.cantidad_disponible for item in self.propuesta.items.all())
        self.propuesta.total_propuesto = sum(item.cantidad_propuesta for item in self.propuesta.items.all())
        self.propuesta.save()

        return self.propuesta

    def _generate_item_propuesta(self, item_solicitud):
        """
        Genera un item de la propuesta, buscando lotes disponibles.
        """
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
        lotes_disponibles = Lote.objects.filter(
            producto=producto,
            cantidad_disponible__gt=0,
            fecha_caducidad__gte=date.today() + timedelta(days=60),
            estado=1  # Solo lotes disponibles
        ).order_by(
            'fecha_caducidad'  # Priorizar lotes que caducan antes
        )

        cantidad_total_disponible = sum(lote.cantidad_disponible for lote in lotes_disponibles)
        item_propuesta.cantidad_disponible = cantidad_total_disponible

        # Asignar lotes
        cantidad_asignada_total = 0
        for lote in lotes_disponibles:
            if cantidad_asignada_total >= cantidad_requerida:
                break

            cantidad_a_asignar = min(
                lote.cantidad_disponible,
                cantidad_requerida - cantidad_asignada_total
            )

            LoteAsignado.objects.create(
                item_propuesta=item_propuesta,
                lote=lote,
                cantidad_asignada=cantidad_a_asignar,
                fecha_caducidad_lote=lote.fecha_caducidad,
                dias_para_caducar=(lote.fecha_caducidad - date.today()).days
            )
            cantidad_asignada_total += cantidad_a_asignar

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
