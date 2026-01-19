"""
Modelos para la Fase 2.2.2: Llegada de Proveedores

Flujo:
1. Recepción (Almacenero) - Captura datos verdes
2. Control de Calidad - Valida y firma
3. Facturación - Captura datos de facturación
4. Supervisión - Valida todo y firma
5. Almacén - Asigna ubicación
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from uuid import uuid4
from datetime import timedelta

from django.contrib.auth import get_user_model

Usuario = get_user_model()


class LlegadaProveedor(models.Model):
    """
    Registro de llegada física del proveedor y captura de datos iniciales.
    Rol: Almacenero (Recepción)
    """
    
    ESTADO_CHOICES = [
        ('EN_RECEPCION', 'En Recepción'),
        ('CONTROL_CALIDAD', 'En Control de Calidad'),
        ('FACTURACION', 'En Facturación'),
        ('VALIDACION', 'En Validación'),
        ('UBICACION', 'Asignando Ubicación'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    folio = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Relaciones
    cita = models.OneToOneField('inventario.CitaProveedor', on_delete=models.PROTECT, related_name='llegada_proveedor')
    proveedor = models.ForeignKey('inventario.Proveedor', on_delete=models.PROTECT)
    
    # Datos de Llegada (Captura Almacenero - CAMPOS VERDES)
    folio_validacion = models.CharField(max_length=50, blank=True, null=True)  # Folio heredado de validación
    fecha_llegada_real = models.DateTimeField(default=timezone.now)
    remision = models.CharField(max_length=100)
    numero_piezas_emitidas = models.IntegerField(validators=[MinValueValidator(1)])
    numero_piezas_recibidas = models.IntegerField(validators=[MinValueValidator(0)])
    almacen = models.ForeignKey('inventario.Almacen', on_delete=models.PROTECT, related_name='llegadas_proveedor')
    tipo_red = models.CharField(
        max_length=20,
        choices=[
            ('FRIA', 'Red Fría'),
            ('SECA', 'Red Seca'),
        ],
        blank=True,
        null=True
    )
    observaciones_recepcion = models.TextField(blank=True, null=True)
    
    # Control de Calidad (CAMPOS VERDES)
    estado_calidad = models.CharField(
        max_length=20,
        choices=[('APROBADO', 'Aprobado'), ('RECHAZADO', 'Rechazado')],
        blank=True,
        null=True
    )
    observaciones_calidad = models.TextField(blank=True, null=True)
    usuario_calidad = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llegadas_validadas_calidad'
    )
    fecha_validacion_calidad = models.DateTimeField(blank=True, null=True)
    firma_calidad = models.CharField(max_length=255, blank=True)  # Firma digital
    
    # Facturación (Captura Facturación)
    numero_factura = models.CharField(max_length=100, blank=True)
    numero_orden_suministro = models.CharField(max_length=100, blank=True)
    numero_contrato = models.CharField(max_length=100, blank=True)
    numero_procedimiento = models.CharField(max_length=100, blank=True)
    programa_presupuestario = models.CharField(max_length=100, blank=True)
    tipo_compra = models.CharField(max_length=100, blank=True)
    usuario_facturacion = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llegadas_facturadas'
    )
    fecha_facturacion = models.DateTimeField(blank=True, null=True)
    
    # Supervisión (Validación final)
    estado_supervision = models.CharField(
        max_length=20,
        choices=[('VALIDADO', 'Validado'), ('RECHAZADO', 'Rechazado')],
        blank=True,
        null=True
    )
    observaciones_supervision = models.TextField(blank=True, null=True)
    usuario_supervision = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llegadas_supervisadas'
    )
    fecha_supervision = models.DateTimeField(blank=True, null=True)
    firma_supervision = models.CharField(max_length=255, blank=True)
    
    # Almacén (Ubicación)
    usuario_ubicacion = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='llegadas_ubicadas'
    )
    fecha_ubicacion = models.DateTimeField(blank=True, null=True)
    
    # Estado general
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='EN_RECEPCION')
    
    # Auditoría
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='llegadas_creadas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['folio']),
            models.Index(fields=['estado']),
            models.Index(fields=['cita']),
        ]
    
    def __str__(self):
        return f"{self.folio} - {self.proveedor.nombre}"
    
    def save(self, *args, **kwargs):
        """Heredar folio y folio_validacion desde la cita"""
        # Heredar folio desde la cita si no existe
        if not self.folio and self.cita:
            self.folio = self.cita.folio
        
        # Heredar folio_validacion desde la cita si no existe
        if not self.folio_validacion and self.cita:
            self.folio_validacion = self.cita.folio
        
        super().save(*args, **kwargs)
    
    def puede_editar_recepcion(self):
        """Verifica si aún se puede editar la recepción"""
        return self.estado == 'EN_RECEPCION'
    
    def puede_validar_calidad(self):
        """Verifica si está lista para control de calidad"""
        return self.estado == 'EN_RECEPCION' and self.items.exists()
    
    def puede_facturar(self):
        """Verifica si está aprobada por calidad"""
        return self.estado_calidad == 'APROBADO'
    
    def puede_supervisar(self):
        """Verifica si está lista para supervisión"""
        return self.numero_factura and self.numero_procedimiento
    
    def puede_ubicar(self):
        """Verifica si está validada por supervisión"""
        return self.estado_supervision == 'VALIDADO'


class ItemLlegada(models.Model):
    """
    Items (productos) incluidos en la llegada del proveedor.
    Captura: Almacenero (Recepción)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    llegada = models.ForeignKey(LlegadaProveedor, on_delete=models.CASCADE, related_name='items')
    
    # Producto (CAMPOS VERDES)
    producto = models.ForeignKey('inventario.Producto', on_delete=models.PROTECT)
    clave = models.CharField(max_length=50)  # CNIS
    descripcion = models.TextField()
    unidad_medida = models.CharField(max_length=50)
    tipo_red = models.CharField(
        max_length=50,
        choices=[
            ('TEMPERATURA_AMBIENTE', 'Temperatura Ambiente'),
            ('RED_FRIA', 'Red Fría'),
        ]
    )
    tipo_insumo = models.CharField(
        max_length=50,
        choices=[
            ('MEDICAMENTO', 'Medicamento'),
            ('MATERIAL_CURACION', 'Material de Curación'),
        ]
    )
    grupo_terapeutico = models.CharField(max_length=100)
    
    # Lote (CAMPOS VERDES)
    numero_lote = models.CharField(max_length=100)
    fecha_caducidad = models.DateField()
    marca = models.CharField(max_length=100, blank=True)
    fabricante = models.CharField(max_length=100, blank=True)
    fecha_elaboracion = models.DateField(blank=True, null=True)
    
    # Cantidades (CAMPOS VERDES)
    cantidad_emitida = models.IntegerField(validators=[MinValueValidator(1)])
    cantidad_recibida = models.IntegerField(validators=[MinValueValidator(0)])
    piezas_por_lote = models.IntegerField(validators=[MinValueValidator(1)], default=1)  # Piezas por lote
    
    # Precios (Captura Facturación)
    precio_unitario_sin_iva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    porcentaje_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    precio_unitario_con_iva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    importe_iva = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    importe_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    
    # Lote creado (después de ubicación)
    lote_creado = models.OneToOneField(
        'inventario.Lote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_llegada'
    )
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['fecha_creacion']
        unique_together = [['llegada', 'numero_lote', 'producto']]
    
    def __str__(self):
        return f"{self.producto.descripcion} - Lote {self.numero_lote}"
    
    def calcular_iva_automatico(self):
        """Calcula el IVA automático según la clave"""
        if self.clave and self.clave.startswith(("060", "080", "130", "379")):
            return 16.00
        return 0.00
    
    def calcular_precios(self):
        """Calcula precios con IVA automáticamente"""
        # Calcular IVA automático si no está establecido
        if self.porcentaje_iva == 0:
            self.porcentaje_iva = self.calcular_iva_automatico()
        
        if self.precio_unitario_sin_iva:
            # Calcular precio con IVA
            factor_iva = 1 + (self.porcentaje_iva / 100)
            self.precio_unitario_con_iva = self.precio_unitario_sin_iva * factor_iva
            
            # Calcular totales
            self.subtotal = self.precio_unitario_sin_iva * self.piezas_por_lote
            self.importe_iva = self.subtotal * (self.porcentaje_iva / 100)
            self.importe_total = self.subtotal + self.importe_iva
    
    def es_caducidad_valida(self):
        """Verifica que la caducidad sea mayor a 60 días"""
        dias_restantes = (self.fecha_caducidad - timezone.now().date()).days
        return dias_restantes > 60
    
    def save(self, *args, **kwargs):
        """Calcula precios antes de guardar"""
        self.calcular_precios()
        super().save(*args, **kwargs)


class DocumentoLlegada(models.Model):
    """
    Documentos adjuntos a la llegada del proveedor.
    (Remisión, Factura, Certificado de Calidad, etc.)
    """
    
    TIPO_DOCUMENTO_CHOICES = [
        ('REMISION', 'Remisión'),
        ('FACTURA', 'Factura'),
        ('CERTIFICADO_CALIDAD', 'Certificado de Calidad'),
        ('OTRO', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    llegada = models.ForeignKey(LlegadaProveedor, on_delete=models.CASCADE, related_name='documentos')
    
    tipo_documento = models.CharField(max_length=50, choices=TIPO_DOCUMENTO_CHOICES)
    archivo = models.FileField(upload_to='llegada_proveedores/%Y/%m/%d/')
    descripcion = models.CharField(max_length=255, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['tipo_documento', 'fecha_creacion']
    
    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.llegada.folio}"
