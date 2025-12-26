"""
URLs para Conteo Físico - Validación de Existencias

Basado en el formato IMSS-Bienestar que captura tres conteos:
1. Primer Conteo (validación inicial)
2. Segundo Conteo (validación de diferencias)
3. Tercer Conteo (valor definitivo que se usa como nueva existencia)
"""

from django.urls import path
from . import views_conteo_fisico_v2

app_name = 'conteo_fisico'

urlpatterns = [
    # Búsqueda de lote por CLAVE
    path('buscar/', views_conteo_fisico_v2.buscar_lote_conteo, name='buscar_lote'),
    
    # Seleccionar lote cuando hay múltiples
    path('seleccionar/', views_conteo_fisico_v2.seleccionar_lote_conteo, name='seleccionar_lote'),
    
    # Capturar conteos de un lote específico
    path('lotes/<int:lote_id>/capturar/', views_conteo_fisico_v2.capturar_conteo_lote, name='capturar_conteo'),
    
    # Crear nuevo lote si no existe
    path('crear-lote/', views_conteo_fisico_v2.crear_lote_conteo, name='crear_lote'),
    
    # Historial de conteos realizados
    path('historial/', views_conteo_fisico_v2.historial_conteospath(
        "lotes/<int:lote_id>/cambiar-ubicacion/",
        views_conteo_fisico_v2.cambiar_ubicacion_conteo,
        name="cambiar_ubicacion_conteo",
    ),
    path(
        "lotes/<int:lote_id>/fusionar/",
        views_conteo_fisico_v2.fusionar_ubicaciones_conteo,
        name="fusionar_ubicaciones_conteo",
    ),
    path(
        "lotes/<int:lote_id>/asignar-ubicacion/",
        views_conteo_fisico_v2.asignar_ubicacion_conteo,
        name="asignar_ubicacion_conteo",
    ),    # Detalle de un movimiento de conteo
    path('movimientos/<int:movimiento_id>/', views_conteo_fisico_v2.detalle_movimiento_conteo, name='detalle_movimiento'),
    
    # API AJAX para obtener información del lote
    path('api/lote-info/', views_conteo_fisico_v2.api_obtener_lote_info, name='api_lote_info'),
]
