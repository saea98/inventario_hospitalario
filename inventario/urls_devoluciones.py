"""
URLs para la Fase 2.4: Devoluciones de Proveedores
"""

from django.urls import path
from . import views_devoluciones

urlpatterns = [
    # Dashboard
    path('', views_devoluciones.dashboard_devoluciones, name='dashboard_devoluciones'),
    
    # Lista
    path('lista/', views_devoluciones.lista_devoluciones, name='lista_devoluciones'),
    
    # Crear
    path('crear/', views_devoluciones.crear_devolucion, name='crear_devolucion'),
    
    # Detalle
    path('<uuid:devolucion_id>/', views_devoluciones.detalle_devolucion, name='detalle_devolucion'),
    
    # Autorizar
    path('<uuid:devolucion_id>/autorizar/', views_devoluciones.autorizar_devolucion, name='autorizar_devolucion'),
    
    # Completar
    path('<uuid:devolucion_id>/completar/', views_devoluciones.completar_devolucion, name='completar_devolucion'),
    
    # Cancelar
    path('<uuid:devolucion_id>/cancelar/', views_devoluciones.cancelar_devolucion, name='cancelar_devolucion'),
]
