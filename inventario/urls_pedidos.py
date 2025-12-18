"""
URLs para Fase 2.2.1: Gestión de Pedidos y Salida de Mercancía
"""

from django.urls import path
from . import views_pedidos

urlpatterns = [
    # Solicitudes de Pedidos
    path('pedidos/solicitudes/', views_pedidos.lista_solicitudes, name='lista_solicitudes'),
    path('pedidos/crear/', views_pedidos.crear_solicitud, name='crear_solicitud'),
    path('pedidos/<uuid:solicitud_id>/items/', views_pedidos.agregar_items_solicitud, name='agregar_items_solicitud'),
    path('pedidos/<uuid:solicitud_id>/validar/', views_pedidos.validar_solicitud, name='validar_solicitud'),
    path('pedidos/<uuid:solicitud_id>/', views_pedidos.detalle_solicitud, name='detalle_solicitud'),
    
    # Órdenes de Surtimiento
    path('pedidos/orden/<uuid:orden_id>/imprimir/', views_pedidos.imprimir_orden_surtimiento, name='imprimir_orden_surtimiento'),
    
    # Salida de Existencias
    path('pedidos/<uuid:solicitud_id>/confirmar-salida/', views_pedidos.confirmar_salida, name='confirmar_salida'),
    path('pedidos/historial/', views_pedidos.historial_pedidos, name='historial_pedidos'),
    path('pedidos/salida/<uuid:salida_id>/', views_pedidos.detalle_salida, name='detalle_salida'),
]
