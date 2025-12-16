"""
URLs para FASE 2: Gestión Logística
Incluye: Citas, Traslados y Conteo Físico
"""

from django.urls import path, include
from . import views_fase2, views_telegram_test, views_traslados_completo, views_conteo_fisico_v2

app_name = 'logistica'

urlpatterns = [
    # ========================================================================
    # CITAS DE PROVEEDORES
    # ========================================================================
    path('citas/', views_fase2.lista_citas, name='lista_citas'),
    path('citas/crear/', views_fase2.crear_cita, name='crear_cita'),
    path('citas/<int:pk>/', views_fase2.detalle_cita, name='detalle_cita'),
    path('citas/<int:pk>/editar/', views_fase2.editar_cita, name='editar_cita'),
    path('citas/<int:pk>/autorizar/', views_fase2.autorizar_cita, name='autorizar_cita'),
    path('citas/<int:pk>/cancelar/', views_fase2.cancelar_cita, name='cancelar_cita'),
    
    # ========================================================================
    # TRASLADOS
    # ========================================================================
    path('traslados/', views_traslados_completo.lista_traslados, name='lista_traslados'),
    path('traslados/crear/', views_traslados_completo.crear_traslado, name='crear_traslado'),
    path('traslados/<int:pk>/', views_traslados_completo.detalle_traslado, name='detalle_traslado'),
    path('traslados/<int:pk>/editar/', views_traslados_completo.editar_traslado, name='editar_traslado'),
    path('traslados/<int:pk>/asignar-logistica/', views_traslados_completo.asignar_logistica_traslado, name='asignar_logistica_traslado'),
    path('traslados/<int:pk>/iniciar-transito/', views_traslados_completo.iniciar_transito_traslado, name='iniciar_transito_traslado'),
    path('traslados/<int:pk>/confirmar-recepcion/', views_traslados_completo.confirmar_recepcion_traslado, name='confirmar_recepcion_traslado'),
    path('traslados/<int:pk>/completar/', views_traslados_completo.completar_traslado, name='completar_traslado'),
    path('traslados/<int:pk>/cancelar/', views_traslados_completo.cancelar_traslado, name='cancelar_traslado'),
    
    # ========================================================================
    # CONTEO FÍSICO - Validación de Existencias (NUEVA VERSIÓN)
    # Basado en formato IMSS-Bienestar con tres conteos
    # ========================================================================
    # Búsqueda de lote por CLAVE (CNIS)
    path('conteos/buscar/', views_conteo_fisico_v2.buscar_lote_conteo, name='buscar_lote_conteo'),
    
    # Seleccionar lote cuando hay múltiples
    path('conteos/seleccionar/', views_conteo_fisico_v2.seleccionar_lote_conteo, name='seleccionar_lote_conteo'),
    
    # Capturar conteos de un lote específico
    path('conteos/lotes/<int:lote_id>/capturar/', views_conteo_fisico_v2.capturar_conteo_lote, name='capturar_conteo_lote'),
    
    # Crear nuevo lote si no existe
    path('conteos/crear-lote/', views_conteo_fisico_v2.crear_lote_conteo, name='crear_lote_conteo'),
    
    # Historial de conteos realizados
    path('conteos/historial/', views_conteo_fisico_v2.historial_conteos, name='historial_conteos'),
    
    # Detalle de un movimiento de conteo
    path('conteos/movimientos/<int:movimiento_id>/', views_conteo_fisico_v2.detalle_movimiento_conteo, name='detalle_movimiento_conteo'),
    
    # API AJAX para obtener información del lote
    path('api/conteos/lote-info/', views_conteo_fisico_v2.api_obtener_lote_info, name='api_lote_info'),
    
    # ========================================================================
    # PRUEBA DE TELEGRAM
    # ========================================================================
    path('test-telegram/', views_telegram_test.test_telegram, name='test_telegram'),
    path('api/telegram/chat-id/', views_telegram_test.obtener_chat_id_desde_updates, name='api_telegram_chat_id'),
]
