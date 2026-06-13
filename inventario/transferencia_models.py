"""
Entradas por transferencia (otros almacenes / entidades).
Independiente de citas y proveedores; impacta inventario como una entrada normal.
"""

from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from decimal import Decimal

Usuario = get_user_model()


def _generar_folio_transferencia():
    from datetime import datetime

    año = datetime.now().year
    prefijo = f'TE-{año}-'
    ultimo = (
        TransferenciaEntrada.objects.filter(folio__startswith=prefijo)
        .order_by('-folio')
        .values_list('folio', flat=True)
        .first()
    )
    if ultimo:
        try:
            siguiente = int(ultimo.split('-')[-1]) + 1
        except (TypeError, ValueError):
            siguiente = 1
    else:
        siguiente = 1
    return f'{prefijo}{siguiente:06d}'


class TransferenciaEntrada(models.Model):
    """Recepción de mercancía transferida desde otro almacén o entidad."""

    ESTADO_CHOICES = [
        ('EN_RECEPCION', 'En Recepción'),
        ('UBICACION', 'Asignando Ubicación'),
        ('APROBADA', 'Aprobada'),
        ('CANCELADA', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    folio = models.CharField(max_length=50, unique=True, db_index=True)
    remision = models.CharField(max_length=100, verbose_name='Remisión')
    almacen_destino = models.ForeignKey(
        'inventario.Almacen',
        on_delete=models.PROTECT,
        related_name='transferencias_recibidas',
        verbose_name='Almacén destino',
    )
    entidad_origen = models.CharField(
        max_length=255,
        verbose_name='Almacén / entidad origen',
        help_text='Ej. Almacén Vallejo, Jalisco, etc.',
    )
    estado_origen = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Estado (origen)',
    )
    fecha_recepcion = models.DateTimeField(default=timezone.now, verbose_name='Fecha de recepción')
    numero_piezas_recibidas = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Piezas recibidas (total)',
    )
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='EN_RECEPCION')
    usuario_aprobacion = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferencias_aprobadas',
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transferencias_creadas',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Entrada por transferencia'
        verbose_name_plural = 'Entradas por transferencia'
        permissions = [
            ('aprobar_transferenciaentrada', 'Puede aprobar entradas por transferencia'),
        ]

    def __str__(self):
        return f'{self.folio} — {self.remision}'

    def save(self, *args, **kwargs):
        if not self.folio:
            self.folio = _generar_folio_transferencia()
        super().save(*args, **kwargs)

    def puede_editar(self):
        return self.estado == 'EN_RECEPCION'

    def puede_aprobar(self):
        return self.estado == 'EN_RECEPCION' and self.items.exists()


class ItemTransferenciaEntrada(models.Model):
    """Clave / lote capturado en una remisión de transferencia."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    transferencia = models.ForeignKey(
        TransferenciaEntrada,
        on_delete=models.CASCADE,
        related_name='items',
    )
    producto = models.ForeignKey('inventario.Producto', on_delete=models.PROTECT)
    clave = models.CharField(max_length=150, verbose_name='Clave CNIS')
    descripcion = models.TextField(blank=True)
    numero_lote = models.CharField(max_length=100, verbose_name='Número de lote')
    fecha_caducidad = models.DateField(null=True, blank=True)
    cantidad_recibida = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad recibida',
    )
    unidad_medida = models.CharField(max_length=50, default='Pieza')
    precio_unitario_sin_iva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    porcentaje_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    precio_unitario_con_iva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    importe_iva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    importe_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    lote_creado = models.OneToOneField(
        'inventario.Lote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_transferencia',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_creacion']
        unique_together = [['transferencia', 'numero_lote', 'clave']]
        verbose_name = 'Ítem de transferencia'
        verbose_name_plural = 'Ítems de transferencia'

    def __str__(self):
        return f'{self.clave} — lote {self.numero_lote}'

    @property
    def descripcion_mostrar(self):
        if self.descripcion:
            return self.descripcion
        if self.producto_id:
            return self.producto.descripcion
        return ''

    def calcular_iva_automatico(self):
        """Misma regla que ItemLlegada: claves 060/080/130/379 → 16%, resto 0%."""
        if self.clave and self.clave.startswith(('060', '080', '130', '379')):
            return Decimal('16.00')
        return Decimal('0.00')

    def calcular_precios(self):
        """Precio con/sin IVA y totales por cantidad recibida (igual que llegadas)."""
        if self.porcentaje_iva == 0:
            self.porcentaje_iva = self.calcular_iva_automatico()

        if not self.precio_unitario_sin_iva:
            self.precio_unitario_con_iva = None
            self.subtotal = None
            self.importe_iva = None
            self.importe_total = None
            return

        porcentaje_iva_decimal = Decimal(str(self.porcentaje_iva or 0))
        factor_iva = Decimal('1') + (porcentaje_iva_decimal / Decimal('100'))
        self.precio_unitario_con_iva = self.precio_unitario_sin_iva * factor_iva
        cantidad = Decimal(str(self.cantidad_recibida or 0))
        self.subtotal = self.precio_unitario_sin_iva * cantidad
        self.importe_iva = self.subtotal * (porcentaje_iva_decimal / Decimal('100'))
        self.importe_total = self.subtotal + self.importe_iva

    def save(self, *args, **kwargs):
        self.calcular_precios()
        super().save(*args, **kwargs)
