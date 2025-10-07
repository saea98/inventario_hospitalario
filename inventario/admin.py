from django.contrib import admin
from .models import (
    Alcaldia, TipoInstitucion, Institucion, CategoriaProducto, 
    Producto, Proveedor, FuenteFinanciamiento, OrdenSuministro,
    Lote, MovimientoInventario, AlertaCaducidad, CargaInventario, EstadoInsumo
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


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'descripcion']
    search_fields = ['nombre', 'codigo']
    ordering = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['clave_cnis', 'descripcion', 'categoria', 'unidad_medida', 'es_insumo_cpm', 'activo']
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