'''
Modelos de datos para el módulo de Gestión de Pedidos (Fase 2.2.1)

Estos modelos se han separado para facilitar el mantenimiento y la claridad.
'''

import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import datetime

# Importaciones de modelos existentes
from .models import Institucion, Almacen, Producto, Lote

# ============================================================================
# MODELOS PARA GESTIÓN DE PEDIDOS
# ============================================================================

class SolicitudPedido(models.Model):
    """
    Representa una solicitud de insumos médicos de un área o institución 
    hacia el almacén central.
    """
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente de Validación'),
        ('VALIDADA', 'Validada y Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('EN_PREPARACION', 'En Preparación (Surtimiento)'),
        ('PREPARADA', 'Preparada para Entrega'),
        ('ENTREGADA', 'Entregada'),
        ('CANCELADA', 'Cancelada por Usuario'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folio = models.CharField(max_length=50, unique=True, editable=False, verbose_name="Folio de Solicitud")
    
    # Relaciones principales
    institucion_solicitante = models.ForeignKey(
        Institucion, 
        on_delete=models.PROTECT, 
        related_name='solicitudes_realizadas',
        verbose_name="Institución Solicitante"
    )
    almacen_destino = models.ForeignKey(
        Almacen, 
        on_delete=models.PROTECT, 
        related_name='solicitudes_recibidas',
        verbose_name="Almacén Destino"
    )
    
    # Usuarios involucrados
    usuario_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='pedidos_solicitados',
        verbose_name="Usuario Solicitante"
    )
    usuario_validacion = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='pedidos_validados',
        null=True, blank=True,
        verbose_name="Usuario de Validación"
    )

    # Fechas clave
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")
    fecha_validacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Validación")
    fecha_entrega_programada = models.DateField(verbose_name="Fecha de Entrega Programada")

    # Estado y observaciones
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', verbose_name="Estado")
    observaciones_solicitud = models.TextField(blank=True, verbose_name="Observaciones de la Solicitud")
    observaciones_validacion = models.TextField(blank=True, verbose_name="Observaciones de la Validación")

    class Meta:
        verbose_name = "Solicitud de Pedido"
        verbose_name_plural = "Solicitudes de Pedidos"
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"{self.folio} - {self.institucion_solicitante.nombre}"

    def save(self, *args, **kwargs):
        if not self.folio:
            # Generar un folio único y legible
            timestamp = self.fecha_solicitud.strftime('%Y%m%d') if self.fecha_solicitud else timezone.now().strftime('%Y%m%d')
            self.folio = f"SOL-{timestamp}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


class ItemSolicitud(models.Model):
    """
    Representa un producto específico dentro de una Solicitud de Pedido.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    solicitud = models.ForeignKey(SolicitudPedido, on_delete=models.CASCADE, related_name='items', verbose_name="Solicitud")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='items_solicitados', verbose_name="Producto")
    
    # Cantidades
    cantidad_solicitada = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad Solicitada")
    cantidad_aprobada = models.PositiveIntegerField(default=0, verbose_name="Cantidad Aprobada")

    # Justificación en caso de cambios
    justificacion_cambio = models.CharField(max_length=255, blank=True, verbose_name="Justificación del Cambio")

    class Meta:
        verbose_name = "Item de Solicitud"
        verbose_name_plural = "Items de la Solicitud"
        unique_together = ('solicitud', 'producto') # Evitar duplicados del mismo producto en una solicitud

    def __str__(self):
        return f"{self.producto.clave_cnis} - {self.cantidad_solicitada} Unidades"

