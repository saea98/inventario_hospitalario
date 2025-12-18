"""
URLs para Fase 2.3: Gestión de Inventario
"""

from django.urls import path
from . import views_inventario

urlpatterns = [
    # Dashboard
    path('dashboard/', views_inventario.dashboard_inventario, name='dashboard_inventario'),
    
    # Consulta de lotes
    path('lotes/', views_inventario.lista_lotes, name='lista_lotes'),
    path('lotes/<int:lote_id>/', views_inventario.detalle_lote, name='detalle_lote'),
    
    # Movimientos
    path('movimientos/', views_inventario.lista_movimientos, name='lista_movimientos'),
    path('salida/', views_inventario.registrar_salida, name='registrar_salida'),
    path('ajuste/', views_inventario.registrar_ajuste, name='registrar_ajuste'),
    
    # Cambio de estado
    path('lotes/<int:lote_id>/cambiar-estado/', views_inventario.cambiar_estado_lote, name='cambiar_estado_lote'),
]
