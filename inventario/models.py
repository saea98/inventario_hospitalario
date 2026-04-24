from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import date, timedelta
import re
from django.utils import timezone

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import AbstractUser
from django.conf import settings




class User(AbstractUser):
    clue = models.CharField(max_length=50, null=True, blank=True)
    almacen = models.ForeignKey(
        'Almacen',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        verbose_name='Almacén Asignado'
    )

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
    
    # Estado de la ubicacion
    ESTADOS_UBICACION = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('bloqueada', 'Bloqueada'),
        ('cuarentena', 'Cuarentena'),
        ('caducados', 'Caducados'),
        ('devoluciones', 'Devoluciones'),
    ]
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_UBICACION,
        default='disponible',
        verbose_name='Estado'
    )
    
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
    
    # IVA aplicable al producto (porcentaje)
    iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=16,
        verbose_name="IVA (%)",
        help_text="Porcentaje de IVA aplicable al producto (ej: 0 para medicamentos, 16 para insumos)"
    )
    
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
    rfc = models.CharField(max_length=20, unique=True, verbose_name="RFC")
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
    numero_orden = models.CharField(max_length=200, unique=True)
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
    cantidad_reservada = models.PositiveIntegerField(default=0, verbose_name="Cantidad Reservada en Propuestas")
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

    #def __str__(self):
        #return f"Lote {self.numero_lote} - {self.producto.clave_cnis}"

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

    def sincronizar_cantidad_disponible(self):
        """
        Sincroniza cantidad_disponible con la suma de todas las ubicaciones (LoteUbicacion).
        Esto asegura que el total del lote sea consistente con sus ubicaciones.
        """
        from django.db.models import Sum
        
        # Calcular suma de todas las ubicaciones
        cantidad_total = LoteUbicacion.objects.filter(lote=self).aggregate(
            total=Sum('cantidad')
        )['total'] or 0
        
        # Actualizar solo si hay diferencia
        if self.cantidad_disponible != cantidad_total:
            self.cantidad_disponible = cantidad_total
            self.save(update_fields=['cantidad_disponible'])
            return True
        return False

    def save(self, *args, **kwargs):
        if self.cantidad_inicial and self.precio_unitario:
            self.valor_total = self.cantidad_inicial * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        desc = self.descripcion_saica or self.producto.descripcion
        return f"{self.numero_lote} — {desc}"





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
        ('AJUSTE_DATOS_LOTE', 'Ajuste a datos de lote'),
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

    # ✅ Propiedad de conveniencia (no nombrar 'estado' para no ocultar el campo IntegerField)
    @property
    def estado_display(self):
        return "Anulado" if self.anulado else "Vigente"

    @property
    def es_salida_surtimiento_pedido(self):
        """
        Salida originada al surtir propuesta (folio comercial en observaciones de la solicitud).
        """
        if self.tipo_movimiento != 'SALIDA':
            return False
        return 'Suministro de Pedido' in (self.motivo or '')

    @property
    def folio_pedido_lista_movimientos(self):
        """
        Valor de la columna «Folio del pedido»: proviene de ``pedido`` (poblado desde
        ``SolicitudPedido.observaciones_solicitud`` al generar el surtimiento). Solo
        aplica a salidas por surtimiento; en cualquier otro movimiento, '-'.
        """
        if not self.es_salida_surtimiento_pedido:
            return '-'
        t = (self.pedido or '').strip()
        if t:
            return t
        m = re.search(r'Pedido:\s*([^\.\n|]+)', self.motivo or '', re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return '-'

    @property
    def mostrar_bloque_destino_pedido_lista(self):
        """Surtimiento: se muestran CLUE e institución destino del pedido; si no aplica, solo '-'."""
        return self.es_salida_surtimiento_pedido and self.institucion_destino_id is not None


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
    
    # Productos no procesados en esta carga
    productos_no_procesados = models.JSONField(blank=True, null=True, default=list, help_text="Lista de claves CNIS no procesadas")
    total_no_procesados = models.PositiveIntegerField(default=0)
    total_productos_sistema = models.PositiveIntegerField(default=0)

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



# ============================================================================
# NUEVOS MODELOS PARA SISTEMA DE INVENTARIO MEJORADO
# ============================================================================

class TipoRed(models.Model):
    """Catálogo de tipos de red (abierto para edición)"""
    codigo = models.CharField(max_length=10, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Red"
        verbose_name_plural = "Tipos de Red"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class TipoEntrega(models.Model):
    """Catálogo de tipos de entrega (abierto para edición)"""
    codigo = models.CharField(max_length=10, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    prefijo_folio = models.CharField(max_length=5, default="", blank=True, verbose_name="Prefijo para Folio")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Entrega"
        verbose_name_plural = "Tipos de Entrega"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Folio(models.Model):
    """Gestión de folios consecutivos por tipo de entrega"""
    tipo_entrega = models.OneToOneField(TipoEntrega, on_delete=models.CASCADE, related_name='folio')
    numero_consecutivo = models.IntegerField(default=0, verbose_name="Número Consecutivo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Folio"
        verbose_name_plural = "Folios"

    def __str__(self):
        return f"Folio {self.tipo_entrega.codigo}: {self.numero_consecutivo}"

    def generar_folio(self):
        """Genera el próximo folio incrementando el consecutivo"""
        self.numero_consecutivo += 1
        self.save()
        prefijo = self.tipo_entrega.prefijo_folio or self.tipo_entrega.codigo
        return f"{prefijo}{str(self.numero_consecutivo).zfill(6)}"


class CitaProveedor(models.Model):
    """Registro de citas con proveedores para recepción de mercancía"""
    ESTADOS_CITA = [
        ('programada', 'Programada'),
        ('autorizada', 'Autorizada'),
        ('completada', 'Completada'),
        ('rechazada', 'Rechazada'),   # Insumo no cumplió criterios; se recibió al proveedor pero se rechazó
        ('cancelada', 'Cancelada'),   # Cita cancelada por otro motivo (sin recepción o por logística)
    ]

    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='citas')
    fecha_cita = models.DateTimeField(verbose_name="Fecha y Hora de Cita")
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, verbose_name="Almacén")
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CITA,
        default='programada',
        verbose_name="Estado"
    )
    
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    
    # Folio único para la cita (formato: IB-YYYY-000001)
    folio = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
        verbose_name="Folio"
    )
    
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='citas_creadas',
        verbose_name="Usuario que Crea"
    )
    
    # Campos de autorización
    fecha_autorizacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Autorización",
        help_text="Fecha y hora cuando se autorizó la cita"
    )
    
    usuario_autorizacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='citas_autorizadas',
        verbose_name="Usuario que Autoriza",
        help_text="Usuario que autorizó la cita"
    )
    
    # Campos de cancelación
    fecha_cancelacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Cancelación",
        help_text="Fecha y hora cuando se canceló la cita"
    )
    
    usuario_cancelacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='citas_canceladas',
        verbose_name="Usuario que Cancela",
        help_text="Usuario que canceló la cita"
    )
    
    razon_cancelacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Razón de Cancelación",
        help_text="Motivo por el cual se canceló la cita"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Campos para carga masiva desde órdenes de suministro
    numero_orden_suministro = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Número de Orden de Suministro"
    )
    numero_contrato = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Número de Contrato"
    )
    clave_medicamento = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Clave de Medicamento (CNIS)"
    )
    tipo_transporte = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Tipo de Transporte"
    )
    fecha_expedicion = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha de Expedición"
    )
    fecha_limite_entrega = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha Límite de Entrega"
    )
    numero_orden_remision = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Número de Orden de Remisión"
    )
    
    # Detalles de la cita en formato JSON (múltiples remisiones y claves)
    detalles_json = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Detalles de la Cita",
        help_text="Lista de detalles con remisión y clave de producto en formato JSON"
    )
    
    # Tipo de entrega con nomenclatura de folios
    TIPOS_ENTREGA = [
        ('entrega_directa', 'Entrega Directa', 'IB'),
        ('operador_logistico', 'Operador Logístico', 'IB'),
        ('sedesa', 'Sedesa', 'S'),
        ('transferencia', 'Transferencia', 'T'),
        ('canje', 'Canje', 'C'),
        ('donacion', 'Donación', 'D'),
    ]
    
    tipo_entrega = models.CharField(
        max_length=20,
        choices=[(t[0], t[1]) for t in TIPOS_ENTREGA],
        default='entrega_directa',
        verbose_name="Tipo de Entrega"
    )
    
    # Bandera: no es material médico (visible como check/interruptor en detalle de cita)
    no_es_material_medico = models.BooleanField(
        default=False,
        verbose_name="No es material médico",
        help_text="Marcar cuando la cita corresponde a material que no es médico"
    )
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cita de Proveedor"
        verbose_name_plural = "Citas de Proveedores"
        ordering = ['-fecha_cita']
        permissions = [
            ('validar_entrada_cita', 'Puede validar entrada de cita'),
        ]

    def __str__(self):
        folio_str = f" [{self.folio}]" if self.folio else ""
        return f"Cita {self.proveedor.razon_social} - {self.fecha_cita.strftime('%d/%m/%Y %H:%M')}{folio_str}"


class OrdenTraslado(models.Model):
    """Orden de traslado de mercancía entre almacenes"""
    ESTADOS_TRASLADO = [
        ('creada', 'Creada'),
        ('logistica_asignada', 'Logística Asignada'),
        ('en_transito', 'En Tránsito'),
        ('recibida', 'Recibida'),
        ('completada', 'Completada'),
    ]

    folio = models.CharField(max_length=20, unique=True, verbose_name="Folio")
    almacen_origen = models.ForeignKey(
        Almacen,
        on_delete=models.CASCADE,
        related_name='traslados_origen',
        verbose_name="Almacén Origen"
    )
    almacen_destino = models.ForeignKey(
        Almacen,
        on_delete=models.CASCADE,
        related_name='traslados_destino',
        verbose_name="Almacén Destino"
    )
    
    # Datos de logística
    vehiculo_placa = models.CharField(max_length=20, blank=True, null=True, verbose_name="Placa del Vehículo")
    chofer_nombre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del Chofer")
    chofer_cedula = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula del Chofer")
    ruta = models.CharField(max_length=200, blank=True, null=True, verbose_name="Ruta")
    
    fecha_salida = models.DateTimeField(blank=True, null=True, verbose_name="Fecha/Hora de Salida")
    fecha_llegada_estimada = models.DateTimeField(blank=True, null=True, verbose_name="Fecha/Hora Llegada Estimada")
    fecha_llegada_real = models.DateTimeField(blank=True, null=True, verbose_name="Fecha/Hora Llegada Real")
    
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS_TRASLADO,
        default='creada',
        verbose_name="Estado"
    )
    
    
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='traslados_creados',
        verbose_name="Usuario que Crea"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Orden de Traslado"
        verbose_name_plural = "Órdenes de Traslado"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Traslado {self.folio} - {self.almacen_origen.nombre} → {self.almacen_destino.nombre}"


class ItemTraslado(models.Model):
    """Items dentro de una orden de traslado"""
    ESTADOS_ITEM = [
        ('pendiente', 'Pendiente'),
        ('en_transito', 'En Tránsito'),
        ('recibido', 'Recibido'),
    ]

    orden_traslado = models.ForeignKey(
        OrdenTraslado,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Orden de Traslado"
    )
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, verbose_name="Lote")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad a Trasladar")
    cantidad_recibida = models.PositiveIntegerField(default=0, verbose_name="Cantidad Recibida")
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_ITEM,
        default='pendiente',
        verbose_name="Estado"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item de Traslado"
        verbose_name_plural = "Items de Traslado"

    def __str__(self):
        return f"{self.lote} - {self.cantidad} unidades"


class ConteoFisico(models.Model):
    """Sesión de conteo físico de inventario"""
    ESTADOS_CONTEO = [
        ('iniciado', 'Iniciado'),
        ('en_progreso', 'En Progreso'),
        ('completado', 'Completado'),
        ('validado', 'Validado'),
        ('ajustado', 'Ajustado'),
    ]

    folio = models.CharField(max_length=20, unique=True, verbose_name="Folio")
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, verbose_name="Almacén")
    
    fecha_inicio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Inicio")
    fecha_fin = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Finalización")
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CONTEO,
        default='iniciado',
        verbose_name="Estado"
    )
    
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conteos_creados',
        verbose_name="Usuario que Crea"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conteo Físico"
        verbose_name_plural = "Conteos Físicos"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Conteo {self.folio} - {self.almacen.nombre}"


class ItemConteoFisico(models.Model):
    """Items contados en una sesión de conteo físico"""
    ESTADOS_DIFERENCIA = [
        ('coincide', 'Coincide'),
        ('falta', 'Falta'),
        ('exceso', 'Exceso'),
    ]

    conteo = models.ForeignKey(
        ConteoFisico,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Conteo Físico"
    )
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, verbose_name="Lote")
    ubicacion = models.ForeignKey(
        UbicacionAlmacen,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ubicación"
    )
    
    cantidad_teorica = models.PositiveIntegerField(verbose_name="Cantidad Teórica")
    cantidad_fisica = models.PositiveIntegerField(verbose_name="Cantidad Física")
    
    estado_diferencia = models.CharField(
        max_length=20,
        choices=ESTADOS_DIFERENCIA,
        verbose_name="Estado de Diferencia"
    )
    
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item de Conteo Físico"
        verbose_name_plural = "Items de Conteo Físico"

    @property
    def diferencia(self):
        """Calcula la diferencia entre cantidad física y teórica"""
        return self.cantidad_fisica - self.cantidad_teorica

    def __str__(self):
        return f"{self.lote} - Diferencia: {self.diferencia}"



# ============================================================================
# CATÁLOGO DE ESTADOS DE CITA
# ============================================================================

class EstadoCita(models.Model):
    """
    Catálogo de estados para citas de proveedores.
    Permite que los administradores modifiquen los estados disponibles.
    """
    
    TIPOS_ESTADO = [
        ('pendiente', 'Pendiente'),
        ('autorizada', 'Autorizada'),
        ('rechazada', 'Rechazada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código del Estado",
        help_text="Identificador único del estado (ej: pendiente, autorizada)"
    )
    
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Estado",
        help_text="Nombre descriptivo del estado"
    )
    
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción detallada del estado"
    )
    
    # Color para UI (Bootstrap)
    color = models.CharField(
        max_length=20,
        default='secondary',
        verbose_name="Color Badge",
        choices=[
            ('primary', 'Azul'),
            ('secondary', 'Gris'),
            ('success', 'Verde'),
            ('danger', 'Rojo'),
            ('warning', 'Amarillo'),
            ('info', 'Celeste'),
            ('light', 'Claro'),
            ('dark', 'Oscuro'),
        ],
        help_text="Color del badge en la interfaz"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Si está desactivado, no aparecerá en los formularios"
    )
    
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de aparición en listas"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Estado de Cita"
        verbose_name_plural = "Estados de Cita"
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"



# ============================================================================
# MODELO DE CONFIGURACIÓN DE NOTIFICACIONES
# ============================================================================

class ConfiguracionNotificaciones(models.Model):
    """
    Configuración centralizada para notificaciones por Email y Telegram.
    
    Permite gestionar:
    - Configuración de Email (SMTP)
    - Configuración de Telegram (Token, Bot, Chat ID)
    - Destinatarios de notificaciones
    - Eventos que generan notificaciones
    """
    
    # ========================================================================
    # CONFIGURACIÓN DE EMAIL
    # ========================================================================
    email_habilitado = models.BooleanField(
        default=True,
        verbose_name="Email Habilitado",
        help_text="Activar/desactivar notificaciones por email"
    )
    
    email_remitente = models.EmailField(
        verbose_name="Email Remitente",
        help_text="Dirección de correo desde la cual se enviarán notificaciones",
        blank=True,
        null=True
    )
    
    email_destinatarios = models.TextField(
        verbose_name="Emails Destinatarios",
        help_text="Direcciones de correo separadas por comas (ej: admin@hospital.com, jefe@hospital.com)",
        blank=True,
        null=True
    )
    
    # ========================================================================
    # CONFIGURACIÓN DE TELEGRAM
    # ========================================================================
    telegram_habilitado = models.BooleanField(
        default=False,
        verbose_name="Telegram Habilitado",
        help_text="Activar/desactivar notificaciones por Telegram"
    )
    
    telegram_token = models.CharField(
        max_length=255,
        verbose_name="Token del Bot de Telegram",
        help_text="Token del bot obtenido de BotFather (@BotFather en Telegram)",
        blank=True,
        null=True
    )
    
    telegram_chat_id = models.CharField(
        max_length=255,
        verbose_name="Chat ID de Telegram",
        help_text="ID del chat/grupo donde se enviarán notificaciones",
        blank=True,
        null=True
    )
    
    # ========================================================================
    # CONFIGURACIÓN DE EVENTOS
    # ========================================================================
    notificar_cita_creada = models.BooleanField(
        default=True,
        verbose_name="Notificar Cita Creada"
    )
    
    notificar_cita_autorizada = models.BooleanField(
        default=True,
        verbose_name="Notificar Cita Autorizada"
    )
    
    notificar_cita_cancelada = models.BooleanField(
        default=True,
        verbose_name="Notificar Cita Cancelada"
    )
    
    notificar_traslado_creado = models.BooleanField(
        default=True,
        verbose_name="Notificar Traslado Creado"
    )
    
    notificar_traslado_completado = models.BooleanField(
        default=True,
        verbose_name="Notificar Traslado Completado"
    )
    
    notificar_conteo_iniciado = models.BooleanField(
        default=True,
        verbose_name="Notificar Conteo Iniciado"
    )
    
    notificar_conteo_completado = models.BooleanField(
        default=True,
        verbose_name="Notificar Conteo Completado"
    )
    
    # ========================================================================
    # AUDITORÍA
    # ========================================================================
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='config_notificaciones_creadas',
        verbose_name="Usuario Creación"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha Creación"
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha Actualización"
    )
    
    class Meta:
        verbose_name = "Configuración de Notificaciones"
        verbose_name_plural = "Configuración de Notificaciones"
        ordering = ['-fecha_actualizacion']
    
    def __str__(self):
        return "Configuración de Notificaciones del Sistema"
    
    def obtener_emails_destinatarios(self):
        """Retorna lista de emails destinatarios"""
        if not self.email_destinatarios:
            return []
        return [email.strip() for email in self.email_destinatarios.split(',')]
    
    def validar_configuracion_telegram(self):
        """Valida que la configuración de Telegram sea válida"""
        if self.telegram_habilitado:
            if not self.telegram_token or not self.telegram_chat_id:
                return False, "Token y Chat ID de Telegram son requeridos"
        return True, "Configuración válida"
    
    def validar_configuracion_email(self):
        """Valida que la configuración de Email sea válida"""
        if self.email_habilitado:
            if not self.email_remitente or not self.email_destinatarios:
                return False, "Email remitente y destinatarios son requeridos"
        return True, "Configuración válida"


class LogNotificaciones(models.Model):
    """
    Registro de todas las notificaciones enviadas.
    
    Permite auditar:
    - Qué notificaciones se enviaron
    - A quién se enviaron
    - Cuándo se enviaron
    - Si fueron exitosas
    """
    
    TIPO_NOTIFICACION = [
        ('email', 'Email'),
        ('telegram', 'Telegram'),
        ('ambos', 'Email y Telegram'),
    ]
    
    ESTADO_NOTIFICACION = [
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('error', 'Error'),
        ('fallida', 'Fallida'),
    ]
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_NOTIFICACION,
        verbose_name="Tipo de Notificación"
    )
    
    evento = models.CharField(
        max_length=100,
        verbose_name="Evento",
        help_text="Evento que generó la notificación (ej: cita_creada, traslado_completado)"
    )
    
    asunto = models.CharField(
        max_length=255,
        verbose_name="Asunto"
    )
    
    mensaje = models.TextField(
        verbose_name="Mensaje"
    )
    
    destinatarios = models.TextField(
        verbose_name="Destinatarios",
        help_text="Destinatarios a los que se intentó enviar"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_NOTIFICACION,
        default='pendiente',
        verbose_name="Estado"
    )
    
    respuesta = models.TextField(
        blank=True,
        null=True,
        verbose_name="Respuesta del Servidor",
        help_text="Respuesta o error del servidor de notificaciones"
    )
    
    fecha_envio = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Envío"
    )
    
    fecha_entrega = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Entrega"
    )
    
    usuario_relacionado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones_recibidas',
        verbose_name="Usuario Relacionado"
    )
    
    class Meta:
        verbose_name = "Log de Notificaciones"
        verbose_name_plural = "Logs de Notificaciones"
        ordering = ['-fecha_envio']
        indexes = [
            models.Index(fields=['evento', '-fecha_envio']),
            models.Index(fields=['estado', '-fecha_envio']),
        ]
    
    def __str__(self):
        return f"{self.evento} - {self.estado} ({self.fecha_envio.strftime('%d/%m/%Y %H:%M')})"





# ============================================================================
# FASE 2.2.1: GESTIÓN DE PEDIDOS (MODELOS RECONSTRUIDOS)
# ============================================================================
from .pedidos_models import SolicitudPedido, ItemSolicitud


# ============================================================================
# FASE 2.2.2: LLEGADA DE PROVEEDORES
# ============================================================================
from .llegada_models import LlegadaProveedor, ItemLlegada, DocumentoLlegada


# ============================================================================
# FASE 2.4: DEVOLUCIONES DE PROVEEDORES
# ============================================================================

class DevolucionProveedor(models.Model):
    """Modelo para registrar devoluciones a proveedores"""
    
    ESTADOS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('AUTORIZADA', 'Autorizada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    MOTIVOS_CHOICES = [
        ('DEFECTUOSO', 'Producto Defectuoso'),
        ('CADUCADO', 'Producto Caducado'),
        ('INCORRECTO', 'Producto Incorrecto'),
        ('CANTIDAD_INCORRECTA', 'Cantidad Incorrecta'),
        ('EMBALAJE_DAÑADO', 'Embalaje Dañado'),
        ('NO_CONFORME', 'No Conforme con Especificaciones'),
        ('SOLICITUD_CLIENTE', 'Solicitud del Cliente'),
        ('OTROS', 'Otros'),
    ]
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folio = models.CharField(max_length=50, unique=True)
    
    # Relaciones
    institucion = models.ForeignKey(Institucion, on_delete=models.PROTECT)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    lotes = models.ManyToManyField(Lote, through='ItemDevolucion', related_name='devoluciones')
    
    # Información de la devolución
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='PENDIENTE')
    motivo_general = models.CharField(max_length=20, choices=MOTIVOS_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    
    # Información de contacto
    contacto_proveedor = models.CharField(max_length=100, blank=True)
    telefono_proveedor = models.CharField(max_length=20, blank=True)
    email_proveedor = models.EmailField(blank=True)
    
    # Información de autorización
    numero_autorizacion = models.CharField(max_length=50, blank=True, null=True)
    fecha_autorizacion = models.DateTimeField(blank=True, null=True)
    usuario_autorizo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='devoluciones_autorizadas')
    
    # Información de entrega
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    fecha_entrega_real = models.DateField(blank=True, null=True)
    numero_guia = models.CharField(max_length=100, blank=True, null=True)
    empresa_transporte = models.CharField(max_length=100, blank=True, null=True)
    
    # Información de nota de crédito
    numero_nota_credito = models.CharField(max_length=50, blank=True, null=True)
    fecha_nota_credito = models.DateField(blank=True, null=True)
    monto_nota_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='devoluciones_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventario_devolucionproveedor'
        verbose_name = 'Devolución a Proveedor'
        verbose_name_plural = 'Devoluciones a Proveedores'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['folio']),
            models.Index(fields=['estado', '-fecha_creacion']),
            models.Index(fields=['proveedor', '-fecha_creacion']),
            models.Index(fields=['institucion', '-fecha_creacion']),
        ]
    
    def __str__(self):
        return f"Devolución {self.folio} - {self.proveedor.razon_social}"
    
    def save(self, *args, **kwargs):
        """Generar folio automáticamente si no existe"""
        if not self.folio:
            # Formato: DEV-YYYYMMDD-XXXXXX
            fecha = timezone.now()
            contador = DevolucionProveedor.objects.filter(
                fecha_creacion__date=fecha.date()
            ).count() + 1
            self.folio = f"DEV-{fecha.strftime('%Y%m%d')}-{str(contador).zfill(6)}"
        
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        """Total de items en la devolución"""
        return self.itemdevolucion_set.aggregate(total=models.Sum('cantidad'))['total'] or 0
    
    @property
    def total_valor(self):
        """Valor total de la devolución"""
        return self.itemdevolucion_set.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('precio_unitario'), output_field=models.DecimalField())
        )['total'] or 0


class ItemDevolucion(models.Model):
    """Modelo para los items incluidos en una devolución"""
    
    # Identificadores
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devolucion = models.ForeignKey(DevolucionProveedor, on_delete=models.CASCADE)
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT)
    
    # Información del item
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    motivo_especifico = models.TextField(blank=True)
    
    # Información de inspección
    inspeccionado = models.BooleanField(default=False)
    fecha_inspeccion = models.DateTimeField(blank=True, null=True)
    usuario_inspeccion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='items_devolucion_inspeccionados')
    observaciones_inspeccion = models.TextField(blank=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventario_itemdevolucion'
        verbose_name = 'Item de Devolución'
        verbose_name_plural = 'Items de Devolución'
        unique_together = ['devolucion', 'lote']
    
    def __str__(self):
        return f"Item {self.lote.numero_lote} - Cantidad: {self.cantidad}"
    
    @property
    def subtotal(self):
        """Subtotal del item"""
        return self.cantidad * self.precio_unitario


# ============================================================
# FASE 4: GESTIÓN DE SALIDAS Y DISTRIBUCIÓN
# ============================================================

class SalidaExistencias(models.Model):
    """Modelo para gestionar salidas de existencias del almacén"""
    
    # Estados posibles
    ESTADOS_SALIDA = [
        ('PENDIENTE', 'Pendiente'),
        ('AUTORIZADA', 'Autorizada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
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
        unique_together = ['salida', 'lote']
    
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



# ============================================================
# MODELO PARA CONFIGURACIÓN DE MENÚ POR ROLES
# ============================================================

class MenuItemRol(models.Model):
    """
    Modelo para definir qué opciones de menú pueden ver los usuarios según sus roles.
    Permite configurar el acceso al menú sin tocar código.
    Soporta creación dinámica de menús sin restricciones de MENU_CHOICES.
    """
    
    menu_item = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Opción de Menú',
        help_text='Identificador único del menú (ej: gestion_proveedores, administracion)'
    )
    
    
    nombre_mostrado = models.CharField(
        max_length=100,
        verbose_name='Nombre Mostrado',
        help_text='Nombre que se muestra en el menú'
    )
    
    icono = models.CharField(
        max_length=50,
        default='fas fa-circle',
        verbose_name='Icono Font Awesome',
        help_text='Clase Font Awesome para el icono (ej: fas fa-home)'
    )
    
    url_name = models.CharField(
        max_length=100,
        verbose_name='Nombre de URL',
        help_text='Nombre de la URL en urls.py (ej: dashboard, lista_productos)'
    )
    
    roles_permitidos = models.ManyToManyField(
        'auth.Group',
        verbose_name='Roles Permitidos',
        help_text='Selecciona los roles que pueden ver esta opción'
    )
    
    orden = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición en el menú'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    
    es_submenu = models.BooleanField(
        default=False,
        verbose_name='Es Submenú',
        help_text='Marcar si es un elemento de submenú'
    )
    
    menu_padre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submenus',
        verbose_name='Menú Padre',
        help_text='Si es un submenú, selecciona el menú padre'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Menú por Rol'
        verbose_name_plural = 'Configuraciones de Menú por Rol'
        ordering = ['orden', 'nombre_mostrado']
    
    def __str__(self):
        return f"{self.nombre_mostrado} ({self.menu_item})"
    
    def puede_ver_usuario(self, usuario):
        """Verifica si un usuario puede ver esta opción de menú"""
        if usuario.is_superuser:
            return True
        
        # Obtener los roles del usuario
        roles_usuario = usuario.groups.all()
        
        # Verificar si alguno de sus roles está en los roles permitidos
        return self.roles_permitidos.filter(id__in=roles_usuario.values_list('id', flat=True)).exists()

    def clean(self):
        """Validación del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar que menu_item no esté vacío
        if not self.menu_item or not self.menu_item.strip():
            raise ValidationError({'menu_item': 'El identificador del menú no puede estar vacío'})
        
        # Validar que menu_item sea único (excepto para este objeto)
        duplicados = MenuItemRol.objects.filter(menu_item=self.menu_item).exclude(id=self.id)
        if duplicados.exists():
            raise ValidationError({'menu_item': f'Ya existe un menú con el identificador "{self.menu_item}"'})
        
        # Validar que no se cree una referencia circular
        if self.menu_padre:
            if self.menu_padre.id == self.id:
                raise ValidationError({'menu_padre': 'Un menú no puede ser su propio padre'})
            
            # Verificar que no haya referencias circulares
            padre_actual = self.menu_padre
            mientras_count = 0
            while padre_actual and mientras_count < 100:
                if padre_actual.id == self.id:
                    raise ValidationError({'menu_padre': 'No se permiten referencias circulares en los menús'})
                padre_actual = padre_actual.menu_padre
                mientras_count += 1
    
    def save(self, *args, **kwargs):
        """Guardar con validación"""
        self.clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def crear_menu_raiz(cls, menu_item, nombre_mostrado, icono='fas fa-folder', url_name=None, orden=0):
        """
        Crea un menú raíz (sin padre) de forma sencilla
        
        Ejemplo:
            MenuItemRol.crear_menu_raiz(
                menu_item='gestion_proveedores',
                nombre_mostrado='Gestión de Proveedores',
                icono='fas fa-truck',
                url_name='gestion_proveedores'
            )
        """
        return cls.objects.create(
            menu_item=menu_item,
            nombre_mostrado=nombre_mostrado,
            icono=icono,
            url_name=url_name or menu_item,
            orden=orden,
            activo=True,
            menu_padre=None
        )
    
    @classmethod
    def crear_submenu(cls, menu_item, nombre_mostrado, menu_padre, icono='fas fa-circle', url_name=None, orden=0):
        """
        Crea un submenú bajo un menú padre
        
        Ejemplo:
            padre = MenuItemRol.objects.get(nombre_mostrado='Gestión de Proveedores')
            MenuItemRol.crear_submenu(
                menu_item='lista_proveedores',
                nombre_mostrado='Listar Proveedores',
                menu_padre=padre,
                icono='fas fa-list',
                url_name='lista_proveedores'
            )
        """
        return cls.objects.create(
            menu_item=menu_item,
            nombre_mostrado=nombre_mostrado,
            icono=icono,
            url_name=url_name or menu_item,
            orden=orden,
            activo=True,
            menu_padre=menu_padre
        )



class LoteUbicacion(models.Model):
    """
    Modelo para almacenar la relación entre un lote y sus ubicaciones.
    Permite que un lote sea distribuido en múltiples ubicaciones con diferentes cantidades.
    """
    lote = models.ForeignKey(
        'Lote',
        on_delete=models.CASCADE,
        related_name='ubicaciones_detalle',
        verbose_name='Lote'
    )
    ubicacion = models.ForeignKey(
        'UbicacionAlmacen',
        on_delete=models.PROTECT,
        verbose_name='Ubicación'
    )
    cantidad = models.PositiveIntegerField(
        verbose_name='Cantidad',
        validators=[MinValueValidator(1)]
    )
    cantidad_reservada = models.PositiveIntegerField(
        default=0,
        verbose_name='Cantidad Reservada en Propuestas'
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_asignacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asignaciones_ubicacion'
    )

    class Meta:
        verbose_name = "Ubicación de Lote"
        verbose_name_plural = "Ubicaciones de Lotes"
        unique_together = ('lote', 'ubicacion')
        ordering = ['lote', 'ubicacion']

    def __str__(self):
        return f"Lote {self.lote.numero_lote} - {self.ubicacion.codigo} ({self.cantidad} unidades)"



class LogSistema(models.Model):
    """Modelo para almacenar logs del sistema"""
    
    NIVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Información'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Crítico'),
    ]
    
    TIPO_CHOICES = [
        ('ESTATICO', 'Archivo Estático'),
        ('BASE_DATOS', 'Base de Datos'),
        ('AUTENTICACION', 'Autenticación'),
        ('NEGOCIO', 'Lógica de Negocio'),
        ('SISTEMA', 'Sistema'),
        ('SEGURIDAD', 'Seguridad'),
        ('OTRO', 'Otro'),
    ]
    
    nivel = models.CharField(
        max_length=10,
        choices=NIVEL_CHOICES,
        default='INFO',
        db_index=True
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='OTRO',
        db_index=True
    )
    
    titulo = models.CharField(max_length=255, db_index=True)
    
    mensaje = models.TextField()
    
    # Detalles adicionales en JSON
    detalles = models.JSONField(default=dict, blank=True)
    
    # Usuario que causó el error (opcional)
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_sistema'
    )
    
    # URL donde ocurrió el error
    url = models.CharField(max_length=500, blank=True, null=True)
    
    # IP del cliente
    ip_cliente = models.GenericIPAddressField(blank=True, null=True)
    
    # User Agent
    user_agent = models.TextField(blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Para marcar como resuelto
    resuelto = models.BooleanField(default=False, db_index=True)
    
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    
    notas_resolucion = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Log del Sistema'
        verbose_name_plural = 'Logs del Sistema'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['-fecha_creacion', 'nivel']),
            models.Index(fields=['-fecha_creacion', 'tipo']),
            models.Index(fields=['resuelto', '-fecha_creacion']),
        ]
    
    def __str__(self):
        return f"[{self.nivel}] {self.titulo} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def crear_log(cls, nivel, tipo, titulo, mensaje, usuario=None, url=None, 
                  ip_cliente=None, user_agent=None, detalles=None):
        """Método helper para crear logs fácilmente"""
        return cls.objects.create(
            nivel=nivel,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            usuario=usuario,
            url=url,
            ip_cliente=ip_cliente,
            user_agent=user_agent,
            detalles=detalles or {}
        )
    
    @classmethod
    def error_estatico(cls, archivo, razon, usuario=None, url=None, ip_cliente=None, user_agent=None):
        """Log para errores de archivos estáticos"""
        return cls.crear_log(
            nivel='ERROR',
            tipo='ESTATICO',
            titulo=f'Error al cargar: {archivo}',
            mensaje=f'No se pudo cargar el archivo estático: {archivo}. Razón: {razon}',
            usuario=usuario,
            url=url,
            ip_cliente=ip_cliente,
            user_agent=user_agent,
            detalles={'archivo': archivo, 'razon': razon}
        )
    
    def marcar_resuelto(self, notas=''):
        """Marcar el log como resuelto"""
        self.resuelto = True
        self.fecha_resolucion = timezone.now()
        self.notas_resolucion = notas
        self.save()



class RegistroConteoFisico(models.Model):
    """
    Registro de conteos físicos parciales.
    
    Permite guardar los conteos 1, 2 y 3 de forma independiente,
    permitiendo que el usuario regrese y complete el conteo en múltiples sesiones.
    
    El MovimientoInventario solo se crea cuando se guarda el tercer conteo.
    """
    
    lote_ubicacion = models.OneToOneField(
        LoteUbicacion,
        on_delete=models.CASCADE,
        related_name='registro_conteo',
        verbose_name="Lote Ubicación"
    )
    
    # Conteos parciales
    primer_conteo = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Primer Conteo"
    )
    
    segundo_conteo = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Segundo Conteo"
    )
    
    tercer_conteo = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tercer Conteo (Definitivo)"
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    
    # Control de estado
    completado = models.BooleanField(
        default=False,
        verbose_name="Conteo Completado",
        help_text="Se marca como completado cuando se guarda el tercer conteo"
    )
    
    # Auditoría
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registros_conteo_creados',
        verbose_name="Usuario Creación"
    )
    
    usuario_ultima_actualizacion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros_conteo_actualizados',
        verbose_name="Usuario Última Actualización"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha Creación"
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha Actualización"
    )
    
    class Meta:
        verbose_name = "Registro de Conteo Físico"
        verbose_name_plural = "Registros de Conteo Físico"
        ordering = ['-fecha_actualizacion']
    
    def __str__(self):
        return f"Conteo: {self.lote_ubicacion} - Completado: {self.completado}"
    
    @property
    def conteo_definitivo(self):
        """Retorna el tercer conteo (valor definitivo)"""
        return self.tercer_conteo
    
    @property
    def progreso(self):
        """Retorna el porcentaje de progreso (1/3, 2/3, 3/3)"""
        conteos_capturados = sum([
            1 if self.primer_conteo is not None else 0,
            1 if self.segundo_conteo is not None else 0,
            1 if self.tercer_conteo is not None else 0,
        ])
        return f"{conteos_capturados}/3"


class ListaRevision(models.Model):
    """
    Lista de Revisión para validar entrada de citas.
    Se genera cuando se inicia el proceso de validación de una cita.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    cita = models.OneToOneField(CitaProveedor, on_delete=models.CASCADE, related_name='lista_revision')
    folio = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Información de documento
    tipo_documento = models.CharField(
        max_length=20,
        choices=[('factura', 'Factura'), ('remision', 'Remisión')],
        default='factura'
    )
    numero_documento = models.CharField(max_length=100, blank=True)
    fecha_documento = models.DateField(null=True, blank=True)
    
    # Información del proveedor
    proveedor = models.CharField(max_length=255)
    numero_control = models.CharField(max_length=100, blank=True)
    numero_prealta = models.CharField(max_length=100, blank=True)
    numero_alta = models.CharField(max_length=100, blank=True)
    numero_contrato = models.CharField(max_length=100, blank=True)
    pedido = models.CharField(max_length=100, blank=True)
    
    # Origen
    origen = models.CharField(
        max_length=20,
        choices=[('imss', 'IMSS Bienestar'), ('transferencia', 'Transferencia'), ('otro', 'Otro')],
        default='imss'
    )
    
    # Estado de la revisión
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Justificación en caso de rechazo
    justificacion_rechazo = models.TextField(blank=True, null=True)
    
    # Información de usuario
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='listas_revision_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    usuario_validacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='listas_revision_validadas')
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    
    # Observaciones
    observaciones = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Lista de Revisión'
        verbose_name_plural = 'Listas de Revisión'
    
    def __str__(self):
        return f"Lista de Revisión - {self.folio}"


class ItemRevision(models.Model):
    """
    Cada criterio de revisión en la lista de revisión.
    """
    RESULTADO_CHOICES = [
        ('si', 'SI'),
        ('no', 'NO'),
        ('na', 'N/A'),
    ]
    
    TIPO_CONTROL_CHOICES = [
        ('radio', 'Radio Button (SI/NO/N/A)'),
        ('checkbox', 'Checkbox (Aplica/No Aplica)'),
    ]
    
    lista_revision = models.ForeignKey(ListaRevision, on_delete=models.CASCADE, related_name='items')
    
    # Descripción del criterio
    descripcion = models.CharField(max_length=500)
    
    # Tipo de control (radio o checkbox)
    tipo_control = models.CharField(
        max_length=20,
        choices=TIPO_CONTROL_CHOICES,
        default='radio'
    )
    
    # Resultado de la revisión
    resultado = models.CharField(max_length=10, choices=RESULTADO_CHOICES, default='si')
    
    # Observaciones específicas
    observaciones = models.TextField(blank=True)
    
    # Orden de presentación
    orden = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['orden']
        verbose_name = 'Item de Revisión'
        verbose_name_plural = 'Items de Revisión'
    
    def __str__(self):
        return f"{self.descripcion} - {self.get_resultado_display()}"
