"""
URLs para Fase 2.3: Gestión de Inventario
"""

from django.urls import path
from . import views_inventario
from . import views_reporte_no_afectados
from . import views_reporte_sin_caducidad

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
    
    # Exportación personalizada de lotes
    path('lotes/exportar-personalizado/', views_inventario.exportar_lotes_personalizado, name='exportar_lotes_personalizado'),
    
    # Reporte de registros no afectados
    path('reporte-no-afectados/', views_reporte_no_afectados.reporte_no_afectados, name='reporte_no_afectados'),
    path('reporte-no-afectados/exportar/', views_reporte_no_afectados.exportar_no_afectados_excel, name='exportar_no_afectados_excel'),
    
    # Reporte de lotes sin fecha de caducidad válida
    path('reporte-sin-caducidad/', views_reporte_sin_caducidad.reporte_sin_caducidad, name='reporte_sin_caducidad'),
    path('reporte-sin-caducidad/exportar/', views_reporte_sin_caducidad.exportar_sin_caducidad_excel, name='exportar_sin_caducidad_excel'),
]
