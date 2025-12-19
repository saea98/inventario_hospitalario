"""
Modelo para gestionar salidas de existencias del almacén
"""

class SalidaExistencias(models.Model):
    """Modelo para gestionar salidas de existencias del almacén"""
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folio = models.CharField(max_length=50, unique=True, verbose_name="Folio")
    
    # Información de la salida
    institucion_destino = models.ForeignKey(Institucion, on_delete=models.PROTECT, verbose_name="Institución Destino")
    almacen_origen = models.ForeignKey(Almacen, on_delete=models.PROTECT, db_column='almacen_origen_id', verbose_name="Almacén Origen")
    
    # Datos de la salida
    fecha_salida = models.DateTimeField(verbose_name="Fecha de Salida")
    nombre_receptor = models.CharField(max_length=200, verbose_name="Nombre del Receptor")
    firma_receptor = models.TextField(verbose_name="Firma del Receptor")
    
    # Solicitud relacionada
    solicitud = models.OneToOneField('SolicitudInventario', on_delete=models.PROTECT, verbose_name="Solicitud")
    
    # Observaciones
    observaciones = models.TextField(verbose_name="Observaciones")
    
    # Autorización
    usuario_autoriza = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='salidas_autorizadas', db_column='usuario_autoriza_id', verbose_name="Usuario que Autoriza")
    
    class Meta:
        db_table = 'inventario_salidaexistencias'
        verbose_name = 'Salida de Existencias'
        verbose_name_plural = 'Salidas de Existencias'
        ordering = ['-fecha_salida']
    
    def __str__(self):
        return f"Salida {self.folio} - {self.nombre_receptor}"


class ItemSalidaExistencias(models.Model):
    """Modelo para los items incluidos en una salida de existencias"""
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    salida = models.ForeignKey(SalidaExistencias, on_delete=models.CASCADE, related_name='itemsalidaexistencias_set')
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, verbose_name="Lote")
    
    # Información del item
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventario_itemsalidaexistencias'
        verbose_name = 'Item de Salida'
        verbose_name_plural = 'Items de Salida'
    
    def __str__(self):
        return f"Item {self.lote.numero_lote} - Cantidad: {self.cantidad}"
    
    @property
    def subtotal(self):
        """Subtotal del item"""
        return self.cantidad * self.precio_unitario


class DistribucionArea(models.Model):
    """Modelo para gestionar la distribución de salidas a diferentes áreas"""
    
    # Estados posibles
    ESTADOS_DISTRIBUCION = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_TRANSITO', 'En Tránsito'),
        ('ENTREGADA', 'Entregada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    salida = models.ForeignKey(SalidaExistencias, on_delete=models.CASCADE, related_name='distribuciones')
    
    # Información del área
    area_destino = models.CharField(max_length=100, verbose_name="Área de Destino")
    responsable_area = models.CharField(max_length=100, verbose_name="Responsable del Área")
    telefono_responsable = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email_responsable = models.EmailField(blank=True, verbose_name="Email")
    
    # Estado de la distribución
    estado = models.CharField(max_length=20, choices=ESTADOS_DISTRIBUCION, default='PENDIENTE', verbose_name="Estado")
    fecha_entrega_estimada = models.DateField(verbose_name="Fecha de Entrega Estimada")
    fecha_entrega_real = models.DateField(blank=True, null=True, verbose_name="Fecha de Entrega Real")
    
    # Información de entrega
    recibido_por = models.CharField(max_length=100, blank=True, verbose_name="Recibido por")
    firma_recibido = models.TextField(blank=True, verbose_name="Firma (Base64)")
    observaciones_entrega = models.TextField(blank=True, verbose_name="Observaciones de Entrega")
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='distribuciones_creadas')
    
    class Meta:
        db_table = 'inventario_distribucionarea'
        verbose_name = 'Distribución a Área'
        verbose_name_plural = 'Distribuciones a Áreas'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Distribución a {self.area_destino} - {self.estado}"
    
    @property
    def total_items(self):
        """Total de items distribuidos a esta área"""
        return self.itemdistribucion_set.aggregate(total=models.Sum('cantidad'))['total'] or 0
    
    @property
    def total_valor(self):
        """Valor total de items distribuidos"""
        return self.itemdistribucion_set.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('precio_unitario'), output_field=models.DecimalField())
        )['total'] or Decimal('0.00')


class ItemDistribucion(models.Model):
    """Modelo para los items distribuidos a cada área"""
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    distribucion = models.ForeignKey(DistribucionArea, on_delete=models.CASCADE, related_name='itemdistribucion_set')
    item_salida = models.ForeignKey(ItemSalidaExistencias, on_delete=models.PROTECT, verbose_name="Item de Salida")
    
    # Información del item distribuido
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad Distribuida")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventario_itemdistribucion'
        verbose_name = 'Item de Distribución'
        verbose_name_plural = 'Items de Distribución'
    
    def __str__(self):
        return f"Distribución de {self.item_salida.lote.numero_lote} - Cantidad: {self.cantidad}"
    
    @property
    def subtotal(self):
        """Subtotal del item distribuido"""
        return self.cantidad * self.precio_unitario
