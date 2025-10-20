from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import date

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import AbstractUser
from django.conf import settings




class User(AbstractUser):
    clue = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.username

class Alcaldia(models.Model):
    """Modelo para las alcaldías/demarcaciones territoriales"""
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Alcaldía"
        verbose_name_plural = "Alcaldías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre



class TipoInstitucion(models.Model):
    """Tipos de instituciones de salud"""
    TIPOS_CHOICES = [
        ('HOSPITAL_PEDIATRICO', 'Hospital Pediátrico'),
        ('HOSPITAL_MATERNO_INFANTIL', 'Hospital Materno Infantil'),
        ('HOSPITAL_GENERAL', 'Hospital General'),
        ('CENTRO_SALUD_T1', 'Centro de Salud T-I'),
        ('CENTRO_SALUD_T2', 'Centro de Salud T-II'),
        ('CENTRO_SALUD_T3', 'Centro de Salud T-III'),
        ('OTRO', 'Otro'),
    ]

    tipo = models.CharField(max_length=50, choices=TIPOS_CHOICES, unique=True)
    descripcion = models.TextField(max_length=255,blank=True, null=True)

    class Meta:
        verbose_name = "Tipo de Institución"
        verbose_name_plural = "Tipos de Instituciones"
        ordering = ['tipo']

    def __str__(self):
        return self.get_tipo_display()

class Institucion(models.Model):
    """Modelo para las instituciones de salud (CLUES)"""
    clue = models.CharField(max_length=20, unique=True, verbose_name="CLUE")
    ib_clue = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="IB CLUE",
        blank=True,
        null=True
    )
    denominacion = models.CharField(max_length=200, verbose_name="Denominación")
    estado = models.CharField(max_length=100, verbose_name="Estado", null=True, blank=True)
    municipio = models.CharField(max_length=100, verbose_name="Municipio", null=True, blank=True)
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la institución", null=True, blank=True)
    alcaldia = models.ForeignKey(Alcaldia, on_delete=models.CASCADE, null=True, blank=True)
    tipo_institucion = models.ForeignKey(TipoInstitucion, on_delete=models.CASCADE, default=1, verbose_name="Tipo de institución")
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Institución"
        verbose_name_plural = "Instituciones"
        ordering = ['denominacion']

    def __str__(self):
        return f"{self.clue} - {self.denominacion}"


class Almacen(models.Model):
    institucion = models.ForeignKey(
        'Institucion',
        on_delete=models.CASCADE,
        verbose_name="Institución (CLUE)"
    )
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=50, unique=True)
    direccion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.institucion.clue})"




class UbicacionAlmacen(models.Model):
    """Ubicaciones físicas dentro de un almacén (Rack, Pasillo, Nivel, etc.)"""
    almacen = models.ForeignKey('Almacen', on_delete=models.CASCADE, related_name='ubicaciones')
    codigo = models.CharField(max_length=50, verbose_name="Código de ubicación")
    descripcion = models.CharField(max_length=150, verbose_name="Descripción de la ubicación", blank=True, null=True)
    nivel = models.CharField(max_length=50, blank=True, null=True)
    pasillo = models.CharField(max_length=50, blank=True, null=True)
    rack = models.CharField(max_length=50, blank=True, null=True)
    seccion = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Ubicación de Almacén"
        verbose_name_plural = "Ubicaciones de Almacén"
        unique_together = ['almacen', 'codigo']
        ordering = ['almacen', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.almacen.nombre}"




def carga_masiva_instituciones(request):
    errores = []
    cargadas = 0

    if request.method == "POST":
        form = CargaMasivaInstitucionForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            wb = openpyxl.load_workbook(archivo)
            sheet = wb.active

            for i, fila in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    # Esperamos estas columnas en el Excel
                    # CLUE | IB CLUE | Denominación | Alcaldía | Tipo Institución | Dirección | Teléfono | Email
                    clue, ib_clue, denominacion, alcaldia_nombre, tipo_nombre, direccion, telefono, email = fila[:8]

                    # Validar datos obligatorios
                    if not clue or not denominacion:
                        errores.append(f"Fila {i}: Falta CLUE o denominación.")
                        continue

                    # Buscar Alcaldía
                    alcaldia = Alcaldia.objects.filter(nombre__iexact=alcaldia_nombre).first()
                    if not alcaldia:
                        errores.append(f"Fila {i}: Alcaldía '{alcaldia_nombre}' no encontrada.")
                        continue

                    # Buscar Tipo de Institución
                    tipo = TipoInstitucion.objects.filter(tipo__iexact=tipo_nombre).first()
                    if not tipo:
                        errores.append(f"Fila {i}: Tipo de institución '{tipo_nombre}' no encontrado.")
                        continue

                    # Crear o actualizar registro
                    institucion, created = Institucion.objects.update_or_create(
                        clue=clue,
                        defaults={
                            'ib_clue': ib_clue,
                            'denominacion': denominacion,
                            'alcaldia': alcaldia,
                            'tipo_institucion': tipo,
                            'direccion': direccion,
                            'telefono': telefono,
                            'email': email,
                            'activo': True,
                        }
                    )
                    if created:
                        cargadas += 1

                except Exception as e:
                    errores.append(f"Fila {i}: Error al procesar ({str(e)})")

            if errores:
                messages.warning(request, f"Se cargaron {cargadas} instituciones, pero {len(errores)} filas tuvieron errores.")
            else:
                messages.success(request, f"Se cargaron correctamente {cargadas} instituciones.")

            return render(request, 'inventario/carga_masiva_instituciones.html', {'form': form, 'errores': errores})

    else:
        form = CargaMasivaInstitucionForm()

    return render(request, 'inventario/carga_masiva_instituciones.html', {'form': form})


class CategoriaProducto(models.Model):
    """Categorías de productos médicos"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(max_length=255, blank=True, null=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True)
    tipo = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Tipo de categoría, por ejemplo: Medicamento, Insumo, Equipo Médico"
    )
    origen_datos = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Fuente original de la categoría (CNIS, SAICA, etc.)"
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría de Producto"
        verbose_name_plural = "Categorías de Productos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre



class Producto(models.Model):
    """Modelo para productos/medicamentos/insumos médicos"""
    clave_cnis = models.CharField(max_length=150, unique=True, verbose_name="Clave/CNIS")
    descripcion = models.TextField(verbose_name="Descripción")
    categoria = models.ForeignKey('CategoriaProducto', on_delete=models.CASCADE)
    unidad_medida = models.CharField(max_length=120, default="PIEZA")
    es_insumo_cpm = models.BooleanField(default=False, verbose_name="Insumo en CPM")
    
    precio_unitario_referencia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        blank=True,
        null=True,
        verbose_name="Precio Unitario de Referencia"
    )
    
    clave_saica = models.CharField(max_length=150, blank=True, null=True, verbose_name="Clave SAICA")
    descripcion_saica = models.TextField(blank=True, null=True, verbose_name="Descripción SAICA")
    unidad_medida_saica = models.CharField(max_length=150, blank=True, null=True)
    
    proveedor = models.CharField(max_length=255, blank=True, null=True)
    rfc_proveedor = models.CharField(max_length=13, blank=True, null=True)
    partida_presupuestal = models.CharField(max_length=150, blank=True, null=True)
    
    marca = models.CharField(max_length=255, null=True, blank=True)
    fabricante = models.CharField(max_length=255, null=True, blank=True)
    
    cantidad_disponible = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        default=0,
        verbose_name="Cantidad Disponible"
    )
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['clave_cnis']

    def __str__(self):
        return f"{self.clave_cnis} - {self.descripcion[:50]}..."



class Proveedor(models.Model):
    """Modelo para proveedores"""
    rfc = models.CharField(max_length=13, unique=True, verbose_name="RFC")
    razon_social = models.CharField(max_length=200, verbose_name="Razón Social")
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    contacto_principal = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['razon_social']

    def __str__(self):
        return f"{self.rfc} - {self.razon_social}"


class FuenteFinanciamiento(models.Model):
    """Fuentes de financiamiento"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(max_length=255, blank=True, null=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = "Fuente de Financiamiento"
        verbose_name_plural = "Fuentes de Financiamiento"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class OrdenSuministro(models.Model):
    """Órdenes de suministro"""
    numero_orden = models.CharField(max_length=50, unique=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    fuente_financiamiento = models.ForeignKey(FuenteFinanciamiento, on_delete=models.SET_NULL, null=True, blank=True)
    partida_presupuestal = models.CharField(max_length=20)
    fecha_orden = models.DateField()
    fecha_entrega_programada = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Orden de Suministro"
        verbose_name_plural = "Órdenes de Suministro"
        ordering = ['-fecha_orden']

    def __str__(self):
        return f"{self.numero_orden} - {self.proveedor.razon_social if self.proveedor else 'Sin proveedor'}"


class Lote(models.Model):
    """Modelo para lotes de productos"""
    ESTADOS_CHOICES = [
        (1, 'Disponible'),
        (4, 'Suspendido'),
        (5, 'Deteriorado'),
        (6, 'Caducado'),
    ]

    numero_lote = models.CharField(max_length=50)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    institucion = models.ForeignKey('Institucion', on_delete=models.CASCADE)
    almacen = models.ForeignKey('Almacen', on_delete=models.SET_NULL, null=True, blank=True)
    ubicacion = models.ForeignKey('UbicacionAlmacen', on_delete=models.SET_NULL, null=True, blank=True)
    orden_suministro = models.ForeignKey('OrdenSuministro', on_delete=models.SET_NULL, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    # Información del lote
    cantidad_inicial = models.PositiveIntegerField(verbose_name="Cantidad Inicial")
    cantidad_disponible = models.PositiveIntegerField(verbose_name="Cantidad Disponible")
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    # Fechas importantes
    fecha_fabricacion = models.DateField(null=True, blank=True)
    fecha_caducidad = models.DateField(null=True, blank=True)
    fecha_recepcion = models.DateField()

    # Estado del lote
    estado = models.IntegerField(choices=ESTADOS_CHOICES, default=1)
    motivo_cambio_estado = models.TextField(blank=True, null=True)
    fecha_cambio_estado = models.DateTimeField(blank=True, null=True)
    usuario_cambio_estado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='cambios_estado_lote'
    )

    # === NUEVOS CAMPOS PARA INTEGRACIÓN SAICA / COMPLEMENTO DE DATOS ===
    cns = models.CharField(max_length=50, blank=True, null=True, verbose_name="CNS")
    proveedor = models.CharField(max_length=150, blank=True, null=True, verbose_name="Proveedor")
    rfc_proveedor = models.CharField(max_length=50, blank=True, null=True, verbose_name="RFC Proveedor")
    partida = models.CharField(max_length=50, blank=True, null=True, verbose_name="Partida")
    clave_saica = models.CharField(max_length=150, blank=True, null=True, verbose_name="Clave SAICA")
    descripcion_saica = models.TextField(blank=True, null=True, verbose_name="Descripción SAICA")
    unidad_saica = models.CharField(max_length=150, blank=True, null=True, verbose_name="Unidad de Medida (SAICA)")
    fuente_datos = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fuente de Datos")
    
    # 🔹 Campos adicionales del CSV 🔹
    contrato = models.CharField(max_length=100, blank=True, null=True)
    folio = models.CharField(max_length=50, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    iva = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    importe_total = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    licitacion = models.CharField(max_length=150, blank=True, null=True)
    pedido = models.CharField(max_length=100, blank=True, null=True)
    remision = models.CharField(max_length=50, blank=True, null=True)
    responsable = models.CharField(max_length=100, blank=True, null=True)
    reviso = models.CharField(max_length=100, blank=True, null=True)
    tipo_entrega = models.CharField(max_length=100, blank=True, null=True)
    tipo_red = models.CharField(max_length=100, blank=True, null=True)
    epa = models.CharField(max_length=50, blank=True, null=True)
    fecha_fabricacion_csv = models.DateField(blank=True, null=True, verbose_name="Fecha de Fabricación CSV")

    # Metadatos
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='lotes_creados'
    )

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ['-fecha_recepcion', 'fecha_caducidad']
        unique_together = ['numero_lote', 'producto', 'institucion']

    def __str__(self):
        return f"Lote {self.numero_lote} - {self.producto.clave_cnis}"

    @property
    def nombre_institucion(self):
        return self.institucion.denominacion if self.institucion else ""

    @property
    def dias_para_caducidad(self):
        if self.fecha_caducidad:
            delta = self.fecha_caducidad - date.today()
            return delta.days
        return None

    @property
    def esta_proximo_a_caducar(self):
        dias = self.dias_para_caducidad
        return dias is not None and dias <= 90

    @property
    def esta_caducado(self):
        dias = self.dias_para_caducidad
        return dias is not None and dias < 0

    def save(self, *args, **kwargs):
        if self.cantidad_inicial and self.precio_unitario:
            self.valor_total = self.cantidad_inicial * self.precio_unitario
        super().save(*args, **kwargs)




class MovimientoInventario(models.Model):
    """Registro de movimientos de inventario"""
    TIPOS_MOVIMIENTO = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE_POSITIVO', 'Ajuste Positivo'),
        ('AJUSTE_NEGATIVO', 'Ajuste Negativo'),
        ('TRANSFERENCIA_ENTRADA', 'Transferencia Entrada'),
        ('TRANSFERENCIA_SALIDA', 'Transferencia Salida'),
        ('CADUCIDAD', 'Caducidad'),
        ('DETERIORO', 'Deterioro'),
    ]

    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name="movimientos")
    tipo_movimiento = models.CharField(max_length=30, choices=TIPOS_MOVIMIENTO)
    cantidad = models.PositiveIntegerField()
    cantidad_anterior = models.PositiveIntegerField()
    cantidad_nueva = models.PositiveIntegerField()

    motivo = models.TextField()
    documento_referencia = models.CharField(max_length=100, blank=True, null=True)
    institucion_destino = models.ForeignKey(
        Institucion,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='movimientos_destino'
    )
    contrato = models.CharField(max_length=255, null=True, blank=True)
    remision = models.CharField(max_length=255, null=True, blank=True)
    pedido = models.CharField(max_length=255, null=True, blank=True)
    folio = models.CharField(max_length=255, null=True, blank=True)
    tipo_entrega = models.CharField(max_length=255, null=True, blank=True)
    licitacion = models.CharField(max_length=255, null=True, blank=True)
    tipo_red = models.CharField(max_length=255, null=True, blank=True)
    responsable = models.CharField(max_length=255, null=True, blank=True)
    reviso = models.CharField(max_length=255, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    iva = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    importe_total = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    estado = models.IntegerField(default=1)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    # 🔽 NUEVOS CAMPOS PARA ANULACIÓN 🔽
    anulado = models.BooleanField(default=False)
    fecha_anulacion = models.DateTimeField(blank=True, null=True)
    usuario_anulacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_anulados'
    )

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha_movimiento']

    # ✅ Validación antes de guardar
    def save(self, *args, **kwargs):
        if self.cantidad_nueva < 0:
            raise ValueError("La cantidad resultante no puede ser negativa.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.lote} - {self.cantidad}"

    # ✅ Propiedad de conveniencia
    @property
    def estado(self):
        return "Anulado" if self.anulado else "Vigente"




class AlertaCaducidad(models.Model):
    """Alertas de productos próximos a caducar"""
    TIPOS_ALERTA = [
        ('30_DIAS', '30 días'),
        ('60_DIAS', '60 días'),
        ('90_DIAS', '90 días'),
        ('CADUCADO', 'Caducado'),
    ]

    lote = models.ForeignKey(Lote, on_delete=models.CASCADE)
    tipo_alerta = models.CharField(max_length=20, choices=TIPOS_ALERTA)
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    vista = models.BooleanField(default=False)
    fecha_vista = models.DateTimeField(blank=True, null=True)
    usuario_vista = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = "Alerta de Caducidad"
        verbose_name_plural = "Alertas de Caducidad"
        ordering = ['-fecha_alerta']
        unique_together = ['lote', 'tipo_alerta']

    def __str__(self):
        return f"Alerta {self.tipo_alerta} - {self.lote}"


class CargaInventario(models.Model):
    """Registro de cargas de inventario desde archivos Excel"""
    ESTADOS_CARGA = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'),
        ('COMPLETADA', 'Completada'),
        ('ERROR', 'Error'),
    ]

    archivo = models.FileField(upload_to='cargas_inventario/')
    nombre_archivo = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=ESTADOS_CARGA, default='PENDIENTE')

    total_registros = models.PositiveIntegerField(default=0)
    registros_procesados = models.PositiveIntegerField(default=0)
    registros_exitosos = models.PositiveIntegerField(default=0)
    registros_con_error = models.PositiveIntegerField(default=0)

    # JSON para guardar errores fila por fila
    log_errores = models.JSONField(blank=True, null=True)

    fecha_carga = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_procesamiento = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Carga de Inventario"
        verbose_name_plural = "Cargas de Inventario"
        ordering = ['-fecha_carga']

    def __str__(self):
        return f"Carga {self.nombre_archivo} - {self.estado}"

class EstadoInsumo(models.Model):
    ESTADOS = [
        (1, "Disponible"),
        (4, "Suspendido"),
        (5, "Deteriorado"),
        (6, "Caducado"),
    ]

    id_estado = models.PositiveSmallIntegerField(choices=ESTADOS, primary_key=True)
    descripcion = models.CharField(max_length=150, editable=False)

    def save(self, *args, **kwargs):
        # Mantener la descripción sincronizada con el choice
        self.descripcion = dict(self.ESTADOS).get(self.id_estado, "Desconocido")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_estado} - {self.descripcion}"
    
# inventario/models.py

class SolicitudInventario(models.Model):
    fecha_generacion = models.DateField(auto_now_add=True)  # fecha de carga/generación
    entidad_federativa = models.CharField(max_length=100)
    clues = models.CharField(max_length=20)
    orden_suministro = models.CharField(max_length=100, blank=True, null=True)
    rfc_proveedor = models.CharField(max_length=20, blank=True, null=True)
    fuente_financiamiento = models.CharField(max_length=50, blank=True, null=True)
    partida_presupuestal = models.CharField(max_length=50, blank=True, null=True)
    concatenar = models.CharField(max_length=100, blank=True, null=True)
    clave_cnis = models.CharField(max_length=50)
    descripcion = models.TextField(max_length=255)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insumo_en_cpm = models.CharField(max_length=50, blank=True, null=True)
    estado_insumo = models.ForeignKey('EstadoInsumo', on_delete=models.PROTECT)
    inventario_disponible = models.IntegerField(default=0)
    unidad_medida = models.CharField(max_length=120, blank=True, null=True)
    lote = models.CharField(max_length=50, blank=True, null=True)
    fecha_caducidad = models.DateField(blank=True, null=True)
    fecha_fabricacion = models.DateField(blank=True, null=True)
    fecha_recepcion = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.fecha_generacion} - {self.clues} - {self.clave_cnis}"
