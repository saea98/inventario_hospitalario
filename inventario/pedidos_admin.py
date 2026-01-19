"""
Configuración de Admin para modelos de Pedidos
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .pedidos_models import LogErrorPedido


@admin.register(LogErrorPedido)
class LogErrorPedidoAdmin(admin.ModelAdmin):
    """
    Admin para gestionar los logs de errores en carga masiva de pedidos.
    """
    
    list_display = (
        'clave_solicitada',
        'tipo_error_display',
        'cantidad_solicitada',
        'usuario_display',
        'institucion_display',
        'fecha_error_display',
        'alerta_status'
    )
    
    list_filter = (
        'tipo_error',
        'fecha_error',
        'alerta_enviada',
        'institucion',
        'usuario'
    )
    
    search_fields = (
        'clave_solicitada',
        'descripcion_error',
        'usuario__username',
        'institucion__nombre'
    )
    
    readonly_fields = (
        'id',
        'fecha_error',
        'fecha_alerta',
        'descripcion_error_display'
    )
    
    fieldsets = (
        ('Información del Error', {
            'fields': (
                'id',
                'tipo_error',
                'clave_solicitada',
                'cantidad_solicitada',
                'descripcion_error_display'
            )
        }),
        ('Usuario y Contexto', {
            'fields': (
                'usuario',
                'institucion',
                'almacen'
            )
        }),
        ('Alertas', {
            'fields': (
                'alerta_enviada',
                'fecha_alerta'
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_error',
            )
        }),
    )
    
    actions = [
        'marcar_alerta_enviada',
        'marcar_alerta_no_enviada'
    ]
    
    def tipo_error_display(self, obj):
        """Muestra el tipo de error con color según el tipo"""
        colors = {
            'CLAVE_NO_EXISTE': '#dc3545',      # Rojo
            'SIN_EXISTENCIA': '#ffc107',       # Amarillo
            'CANTIDAD_INVALIDA': '#fd7e14',    # Naranja
            'OTRO': '#6c757d'                  # Gris
        }
        
        color = colors.get(obj.tipo_error, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_error_display()
        )
    tipo_error_display.short_description = 'Tipo de Error'
    
    def usuario_display(self, obj):
        """Muestra el usuario con su nombre completo"""
        if obj.usuario:
            return f"{obj.usuario.username} ({obj.usuario.get_full_name()})"
        return "N/A"
    usuario_display.short_description = 'Usuario'
    
    def institucion_display(self, obj):
        """Muestra la institución"""
        return obj.institucion.nombre if obj.institucion else "N/A"
    institucion_display.short_description = 'Institución'
    
    def fecha_error_display(self, obj):
        """Muestra la fecha del error formateada"""
        return obj.fecha_error.strftime("%d/%m/%Y %H:%M:%S")
    fecha_error_display.short_description = 'Fecha del Error'
    
    def alerta_status(self, obj):
        """Muestra el estado de la alerta"""
        if obj.alerta_enviada:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Enviada</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ No enviada</span>'
            )
    alerta_status.short_description = 'Estado de Alerta'
    
    def descripcion_error_display(self, obj):
        """Muestra la descripción del error en un campo de solo lectura"""
        return obj.descripcion_error
    descripcion_error_display.short_description = 'Descripción del Error'
    
    def marcar_alerta_enviada(self, request, queryset):
        """Acción para marcar errores como alerta enviada"""
        from django.utils import timezone
        updated = queryset.update(
            alerta_enviada=True,
            fecha_alerta=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} error(es) marcado(s) como alerta enviada.'
        )
    marcar_alerta_enviada.short_description = 'Marcar como alerta enviada'
    
    def marcar_alerta_no_enviada(self, request, queryset):
        """Acción para marcar errores como alerta no enviada"""
        updated = queryset.update(
            alerta_enviada=False,
            fecha_alerta=None
        )
        self.message_user(
            request,
            f'{updated} error(es) marcado(s) como alerta no enviada.'
        )
    marcar_alerta_no_enviada.short_description = 'Marcar como alerta no enviada'
    
    def get_queryset(self, request):
        """Optimizar queryset con select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'usuario',
            'institucion',
            'almacen'
        )
    
    def has_add_permission(self, request):
        """No permitir agregar errores manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo permitir eliminar si es superusuario"""
        return request.user.is_superuser
    
    class Media:
        css = {
            'all': ('admin/css/pedidos_admin.css',)
        }
