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
from .models import Institucion, Almacen, Producto, Lote, UbicacionAlmacen

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
    observaciones_solicitud = models.TextField(blank=True, verbose_name="Folio del Pedido")
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



class PropuestaPedido(models.Model):
    """
    Representa una propuesta de surtimiento generada automáticamente basada en 
    la disponibilidad de inventario y las reglas de validación.
    
    Se genera automáticamente cuando una solicitud es validada.
    El personal de almacén la revisa y surte según esta propuesta.
    """
    ESTADO_CHOICES = [
        ('GENERADA', 'Propuesta Generada'),
        ('REVISADA', 'Revisada por Almacén'),
        ('EN_SURTIMIENTO', 'En Proceso de Surtimiento'),
        ('SURTIDA', 'Completamente Surtida'),
        ('PARCIAL', 'Parcialmente Surtida'),
        ('NO_DISPONIBLE', 'No Disponible'),
        ('CANCELADA', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    solicitud = models.OneToOneField(
        SolicitudPedido, 
        on_delete=models.CASCADE, 
        related_name='propuesta_pedido',
        verbose_name="Solicitud de Pedido"
    )
    
    # Información de generación
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Generación")
    usuario_generacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='propuestas_generadas',
        verbose_name="Usuario que Generó"
    )
    
    # Estado del surtimiento
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='GENERADA',
        verbose_name="Estado de la Propuesta"
    )
    
    # Información de revisión
    fecha_revision = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Revisión")
    usuario_revision = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='propuestas_revisadas',
        null=True, blank=True,
        verbose_name="Usuario que Revisó"
    )
    observaciones_revision = models.TextField(blank=True, verbose_name="Observaciones de Revisión")
    
    # Información de surtimiento
    fecha_surtimiento = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Surtimiento")
    usuario_surtimiento = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='propuestas_surtidas',
        null=True, blank=True,
        verbose_name="Usuario que Surtió"
    )
    
    # Resumen de disponibilidad
    total_solicitado = models.PositiveIntegerField(default=0, verbose_name="Total Solicitado")
    total_disponible = models.PositiveIntegerField(default=0, verbose_name="Total Disponible")
    total_propuesto = models.PositiveIntegerField(default=0, verbose_name="Total Propuesto")
    
    class Meta:
        verbose_name = "Propuesta de Pedido"
        verbose_name_plural = "Propuestas de Pedidos"
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"Propuesta {self.solicitud.folio} - {self.get_estado_display()}"

    @property
    def porcentaje_disponibilidad(self):
        """Calcula el porcentaje de disponibilidad"""
        if self.total_solicitado == 0:
            return 0
        return round((self.total_disponible / self.total_solicitado) * 100, 2)


class ItemPropuesta(models.Model):
    """
    Representa un item específico dentro de una propuesta de pedido.
    Incluye información de disponibilidad y lotes sugeridos.
    """
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('PARCIAL', 'Disponible Parcialmente'),
        ('NO_DISPONIBLE', 'No Disponible'),
        ('SURTIDO', 'Surtido'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    propuesta = models.ForeignKey(
        PropuestaPedido, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name="Propuesta de Pedido"
    )
    item_solicitud = models.ForeignKey(
        ItemSolicitud,
        on_delete=models.CASCADE,
        related_name='items_propuesta',
        verbose_name="Item de Solicitud"
    )
    
    # Información del producto
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.PROTECT,
        verbose_name="Producto"
    )
    
    # Cantidades
    cantidad_solicitada = models.PositiveIntegerField(verbose_name="Cantidad Solicitada")
    cantidad_disponible = models.PositiveIntegerField(default=0, verbose_name="Cantidad Disponible")
    cantidad_propuesta = models.PositiveIntegerField(default=0, verbose_name="Cantidad Propuesta")
    cantidad_surtida = models.PositiveIntegerField(default=0, verbose_name="Cantidad Surtida")
    
    # Estado
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='NO_DISPONIBLE',
        verbose_name="Estado de Disponibilidad"
    )
    
    # Observaciones
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    class Meta:
        verbose_name = "Item de Propuesta"
        verbose_name_plural = "Items de Propuesta"
        ordering = ['producto__clave_cnis']

    def __str__(self):
        return f"{self.producto.clave_cnis} - {self.cantidad_propuesta} Unidades"


class LoteAsignado(models.Model):
    """
    Registra qué lotes específicos se asignan para surtir cada item de la propuesta.
    Permite trazabilidad completa del surtimiento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_propuesta = models.ForeignKey(
        ItemPropuesta,
        on_delete=models.CASCADE,
        related_name='lotes_asignados',
        verbose_name="Item de Propuesta"
    )
    lote_ubicacion = models.ForeignKey(
        'LoteUbicacion',
        on_delete=models.PROTECT,
        related_name='asignaciones_propuesta',
        verbose_name="Ubicación del Lote Asignado"
    )

    cantidad_asignada = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad Asignada"
    )
    
    # Estado del surtimiento
    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Asignación")
    fecha_surtimiento = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Surtimiento")
    surtido = models.BooleanField(default=False, verbose_name="¿Fue Surtido?")
    
    class Meta:
        verbose_name = "Lote Asignado"
        verbose_name_plural = "Lotes Asignados"
        ordering = ['lote_ubicacion__lote__fecha_caducidad']

    def __str__(self):
        return f"{self.lote_ubicacion.lote.numero_lote} - {self.cantidad_asignada} Unidades"


class LogPropuesta(models.Model):
    """
    Registra los cambios de estado y acciones importantes en una propuesta.
    """
    propuesta = models.ForeignKey(PropuestaPedido, on_delete=models.CASCADE, related_name='logs')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=255)
    detalles = models.TextField(blank=True, null=True)

    class Meta:
        ordering = [\'-timestamp\']

    def __str__(self):
        return f'{self.timestamp} - {self.propuesta.solicitud.folio} - {self.accion}'
