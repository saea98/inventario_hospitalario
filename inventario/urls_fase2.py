"""
URLs para FASE 2: Gestión Logística
Incluye: Citas, Traslados y Conteo Físico
"""

from django.urls import path
from . import views_fase2

app_name = 'inventario'

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
    path('traslados/', views_fase2.lista_traslados, name='lista_traslados'),
    path('traslados/crear/', views_fase2.crear_traslado, name='crear_traslado'),
    path('traslados/<int:pk>/', views_fase2.detalle_traslado, name='detalle_traslado'),
    path('traslados/<int:pk>/asignar-logistica/', views_fase2.asignar_logistica_traslado, name='asignar_logistica_traslado'),
    
    # ========================================================================
    # CONTEO FÍSICO
    # ========================================================================
    path('conteos/', views_fase2.lista_conteos, name='lista_conteos'),
    path('conteos/iniciar/', views_fase2.iniciar_conteo, name='iniciar_conteo'),
    path('conteos/<int:pk>/capturar/', views_fase2.capturar_conteo, name='capturar_conteo'),
    path('conteos/<int:pk>/', views_fase2.detalle_conteo, name='detalle_conteo'),
]
