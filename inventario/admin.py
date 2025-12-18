from django.contrib import admin
#from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from .models import (
    Alcaldia, TipoInstitucion, Institucion, CategoriaProducto, 
    Producto, Proveedor, FuenteFinanciamiento, OrdenSuministro,
    Lote, MovimientoInventario, AlertaCaducidad, CargaInventario, 
    EstadoInsumo, Almacen, UbicacionAlmacen,
    TipoRed, TipoEntrega, Folio, CitaProveedor, EstadoCita,
    OrdenTraslado, ItemTraslado, ConteoFisico, ItemConteoFisico,
    ConfiguracionNotificaciones, LogNotificaciones
)


@admin.register(Alcaldia)
class AlcaldiaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo']
    search_fields = ['nombre', 'codigo']
    ordering = ['nombre']


@admin.register(TipoInstitucion)
class TipoInstitucionAdmin(admin.ModelAdmin):
    list_display = ['get_tipo_display', 'descripcion']
    list_filter = ['tipo']


@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ['clue', 'ib_clue', 'denominacion', 'alcaldia', 'tipo_institucion', 'activo']
    list_filter = ['alcaldia', 'tipo_institucion', 'activo']
    search_fields = ['clue', 'ib_clue', 'denominacion']
    ordering = ['denominacion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'institucion', 'activo']
    list_filter = ['activo', 'institucion']
    search_fields = ['codigo', 'nombre', 'institucion__denominacion']
    ordering = ['codigo']


@admin.register(UbicacionAlmacen)
class UbicacionAlmacenAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'almacen', 'descripcion', 'nivel', 'pasillo', 
        'rack', 'seccion', 'estado', 'activo'
    ]
    list_filter = ['activo', 'estado', 'almacen', 'nivel', 'pasillo']
    search_fields = ['codigo', 'descripcion', 'almacen__nombre']
    ordering = ['almacen', 'codigo']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('almacen', 'codigo', 'descripcion', 'activo')
        }),
        ('Detalles de Ubicación', {
            'fields': ('nivel', 'pasillo', 'rack', 'seccion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'descripcion']
    search_fields = ['nombre', 'codigo']
    ordering = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['clave_cnis', 'descripcion', 'categoria', 'unidad_medida', 'iva', 'es_insumo_cpm', 'activo']
    list_filter = ['categoria', 'unidad_medida', 'es_insumo_cpm', 'activo']
    search_fields = ['clave_cnis', 'descripcion']
    ordering = ['clave_cnis']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['rfc', 'razon_social', 'telefono', 'email', 'activo']
    list_filter = ['activo']
    search_fields = ['rfc', 'razon_social']
    ordering = ['razon_social']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(FuenteFinanciamiento)
class FuenteFinanciamientoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'descripcion']
    search_fields = ['nombre', 'codigo']
    ordering = ['nombre']


@admin.register(OrdenSuministro)
class OrdenSuministroAdmin(admin.ModelAdmin):
    list_display = ['numero_orden', 'proveedor', 'fuente_financiamiento', 'fecha_orden', 'activo']
    list_filter = ['fuente_financiamiento', 'activo', 'fecha_orden']
    search_fields = ['numero_orden', 'proveedor__razon_social']
    ordering = ['-fecha_orden']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = [
        'numero_lote', 'producto', 'institucion', 'cantidad_disponible', 
        'fecha_caducidad', 'estado', 'dias_para_caducidad'
    ]
    list_filter = ['estado', 'institucion', 'producto__categoria', 'fecha_caducidad']
    search_fields = ['numero_lote', 'producto__clave_cnis', 'institucion__denominacion']
    ordering = ['fecha_caducidad', '-fecha_recepcion']
    readonly_fields = [
        'uuid', 'valor_total', 'fecha_creacion', 'fecha_actualizacion',
        'dias_para_caducidad', 'esta_proximo_a_caducar', 'esta_caducado'
    ]
    
    def dias_para_caducidad(self, obj):
        return obj.dias_para_caducidad
    dias_para_caducidad.short_description = 'Días para caducidad'


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = [
        'lote', 'tipo_movimiento', 'cantidad', 'cantidad_anterior', 
        'cantidad_nueva', 'fecha_movimiento', 'usuario'
    ]
    list_filter = ['tipo_movimiento', 'fecha_movimiento', 'lote__institucion']
    search_fields = ['lote__numero_lote', 'motivo', 'documento_referencia']
    ordering = ['-fecha_movimiento']
    readonly_fields = ['fecha_movimiento']


@admin.register(AlertaCaducidad)
class AlertaCaducidadAdmin(admin.ModelAdmin):
    list_display = ['lote', 'tipo_alerta', 'fecha_alerta', 'vista', 'fecha_vista']
    list_filter = ['tipo_alerta', 'vista', 'fecha_alerta']
    search_fields = ['lote__numero_lote', 'lote__producto__clave_cnis']
    ordering = ['-fecha_alerta']
    readonly_fields = ['fecha_alerta']


@admin.register(CargaInventario)
class CargaInventarioAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_archivo', 'estado', 'total_registros', 'registros_exitosos', 
        'registros_con_error', 'fecha_carga', 'usuario'
    ]
    list_filter = ['estado', 'fecha_carga']
    search_fields = ['nombre_archivo']
    ordering = ['-fecha_carga']
    readonly_fields = ['fecha_carga', 'fecha_procesamiento']


@admin.register(EstadoInsumo)
class EstadoInsumoAdmin(admin.ModelAdmin):
    list_display = ('id_estado', 'descripcion')


# ============================================================
# REGISTRAR USER PERSONALIZADO Y GROUP
# ============================================================
# NO usar importaciones de django.contrib.auth.models para User
# En su lugar, importar el User personalizado de tu app
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from .models import User  # Importa TU User personalizado

# Desregistrar Group si ya está registrado (evita duplicados)
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

# Registrar TU User personalizado
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'clue', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'groups']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'clue']
    
    # Agrega el campo 'clue' a los fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('clue', 'almacen')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información Adicional', {'fields': ('clue', 'almacen')}),
    )

# Registrar Group de Django (para permisos)
@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    pass


# Registrar SolicitudInventario que falta en tu admin actual
from .models import SolicitudInventario

@admin.register(SolicitudInventario)
class SolicitudInventarioAdmin(admin.ModelAdmin):
    list_display = ['fecha_generacion', 'clues', 'clave_cnis', 'descripcion', 'inventario_disponible']
    list_filter = ['fecha_generacion', 'clues']
    search_fields = ['clues', 'clave_cnis', 'descripcion']
    ordering = ['-fecha_generacion']

# ============================================================
# NUEVOS MODELOS PARA SISTEMA MEJORADO
# ============================================================

@admin.register(TipoRed)
class TipoRedAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'descripcion', 'activo']
    list_filter = ['activo']
    search_fields = ['codigo', 'nombre']
    ordering = ['nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(TipoEntrega)
class TipoEntregaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'prefijo_folio', 'descripcion', 'activo']
    list_filter = ['activo']
    search_fields = ['codigo', 'nombre']
    ordering = ['nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(Folio)
class FolioAdmin(admin.ModelAdmin):
    list_display = ['tipo_entrega', 'numero_consecutivo']
    search_fields = ['tipo_entrega__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(CitaProveedor)
class CitaProveedorAdmin(admin.ModelAdmin):
    list_display = ['proveedor', 'fecha_cita', 'almacen', 'estado', 'usuario_creacion']
    list_filter = ['estado', 'fecha_cita', 'almacen']
    search_fields = ['proveedor__razon_social', 'observaciones']
    ordering = ['-fecha_cita']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(OrdenTraslado)
class OrdenTrasladoAdmin(admin.ModelAdmin):
    list_display = ['folio', 'almacen_origen', 'almacen_destino', 'estado', 'fecha_salida']
    list_filter = ['estado', 'fecha_creacion', 'almacen_origen', 'almacen_destino']
    search_fields = ['folio', 'vehiculo_placa', 'chofer_nombre']
    ordering = ['-fecha_creacion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Informacion Principal', {
            'fields': ('folio', 'almacen_origen', 'almacen_destino', 'estado')
        }),
        ('Logistica', {
            'fields': ('vehiculo_placa', 'chofer_nombre', 'chofer_cedula', 'ruta')
        }),
        ('Fechas', {
            'fields': ('fecha_salida', 'fecha_llegada_estimada', 'fecha_llegada_real')
        }),
        ('Auditoria', {
            'fields': ('usuario_creacion', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


class ItemTrasladoInline(admin.TabularInline):
    model = ItemTraslado
    extra = 1
    fields = ['lote', 'cantidad', 'cantidad_recibida', 'estado']


@admin.register(ConteoFisico)
class ConteoFisicoAdmin(admin.ModelAdmin):
    list_display = ['folio', 'almacen', 'estado', 'fecha_inicio', 'fecha_fin']
    list_filter = ['estado', 'fecha_inicio', 'almacen']
    search_fields = ['folio', 'almacen__nombre']
    ordering = ['-fecha_inicio']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Informacion Principal', {
            'fields': ('folio', 'almacen', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Auditoria', {
            'fields': ('usuario_creacion', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ItemConteoFisico)
class ItemConteoFisicoAdmin(admin.ModelAdmin):
    list_display = ['conteo', 'lote', 'cantidad_teorica', 'cantidad_fisica', 'estado_diferencia']
    list_filter = ['estado_diferencia', 'conteo__almacen']
    search_fields = ['lote__numero_lote', 'conteo__folio']
    ordering = ['-conteo__fecha_inicio']
    readonly_fields = ['fecha_creacion']



@admin.register(EstadoCita)
class EstadoCitaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'color', 'activo', 'orden']
    list_filter = ['activo', 'color']
    search_fields = ['codigo', 'nombre']
    ordering = ['orden', 'nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('codigo', 'nombre', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('color', 'activo', 'orden')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )



# ============================================================================
# CONFIGURACIÓN DE NOTIFICACIONES
# ============================================================================

@admin.register(ConfiguracionNotificaciones)
class ConfiguracionNotificacionesAdmin(admin.ModelAdmin):
    list_display = [
        'email_habilitado', 'telegram_habilitado', 
        'email_remitente', 'fecha_actualizacion'
    ]
    list_filter = ['email_habilitado', 'telegram_habilitado']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Configuración de Email', {
            'fields': (
                'email_habilitado', 'email_remitente', 
                'email_destinatarios', 'notificar_cita_creada',
                'notificar_cita_autorizada', 'notificar_cita_cancelada',
                'notificar_traslado_creado', 'notificar_traslado_completado',
                'notificar_conteo_iniciado', 'notificar_conteo_completado'
            ),
            'description': 'Configurar notificaciones por correo electrónico'
        }),
        ('Configuración de Telegram', {
            'fields': (
                'telegram_habilitado', 'telegram_token', 'telegram_chat_id'
            ),
            'description': 'Configurar notificaciones por Telegram'
        }),
        ('Auditoría', {
            'fields': ('usuario_creacion', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Solo permitir una configuración"""
        return not ConfiguracionNotificaciones.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar la configuración"""
        return False


@admin.register(LogNotificaciones)
class LogNotificacionesAdmin(admin.ModelAdmin):
    list_display = [
        'evento', 'tipo', 'estado', 'destinatarios', 'fecha_envio'
    ]
    list_filter = ['tipo', 'estado', 'evento', 'fecha_envio']
    search_fields = ['asunto', 'evento', 'destinatarios']
    readonly_fields = [
        'tipo', 'evento', 'asunto', 'mensaje', 'destinatarios',
        'respuesta', 'fecha_envio', 'fecha_entrega', 'usuario_relacionado'
    ]
    ordering = ['-fecha_envio']
    
    fieldsets = (
        ('Información de Notificación', {
            'fields': ('tipo', 'evento', 'asunto', 'mensaje')
        }),
        ('Destinatarios y Estado', {
            'fields': ('destinatarios', 'estado', 'usuario_relacionado')
        }),
        ('Respuesta del Servidor', {
            'fields': ('respuesta',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_envio', 'fecha_entrega'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """No permitir agregar logs manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar logs"""
        return False
