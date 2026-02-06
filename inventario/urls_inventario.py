"""
URLs para Fase 2.3: Gestión de Inventario
"""

from django.urls import path
from . import views_inventario
from . import views_reporte_no_afectados
from . import views_reporte_sin_caducidad
from . import views_reporte_entradas
from . import views_reporte_sin_ubicacion
from . import views_reporte_conteo_almacen

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
    
    # Exportación personalizada de lotes (desde lista_lotes)
    path('lotes/exportar-personalizado/', views_inventario.exportar_lotes_personalizado, name='exportar_lotes_personalizado'),
    # Reporte independiente de lotes para exportación (solo lectura)
    path('lotes/reporte-personalizado/', views_inventario.reporte_lotes_personalizado, name='reporte_lotes_personalizado'),
    
    # Reporte de registros no afectados
    path('reporte-no-afectados/', views_reporte_no_afectados.reporte_no_afectados, name='reporte_no_afectados'),
    path('reporte-no-afectados/exportar/', views_reporte_no_afectados.exportar_no_afectados_excel, name='exportar_no_afectados_excel'),
    path('reporte-no-afectados/eliminar/<int:lote_id>/', views_reporte_no_afectados.eliminar_registro_no_afectado, name='eliminar_registro_no_afectado'),
    path('reporte-no-afectados/eliminar/<int:lote_id>/<int:ubicacion_id>/', views_reporte_no_afectados.eliminar_registro_no_afectado, name='eliminar_registro_no_afectado_ubicacion'),
    path('reporte-no-afectados/bulk-delete/', views_reporte_no_afectados.reporte_no_afectados_bulk_delete, name='reporte_no_afectados_bulk_delete'),
    
    # Reporte de lotes sin fecha de caducidad válida
    path('reporte-sin-caducidad/', views_reporte_sin_caducidad.reporte_sin_caducidad, name='reporte_sin_caducidad'),
    path('reporte-sin-caducidad/exportar/', views_reporte_sin_caducidad.exportar_sin_caducidad_excel, name='exportar_sin_caducidad_excel'),
    
    # Reporte de entradas al inventario
    path('reporte-entradas/', views_reporte_entradas.reporte_entradas, name='reporte_entradas'),
    path('reporte-entradas/exportar/', views_reporte_entradas.exportar_entradas_excel, name='exportar_entradas_excel'),
    
    # Reporte de productos sin ubicación asignada
    path('reporte-sin-ubicacion/', views_reporte_sin_ubicacion.reporte_sin_ubicacion, name='reporte_sin_ubicacion'),
    path('reporte-sin-ubicacion/exportar/', views_reporte_sin_ubicacion.exportar_sin_ubicacion_excel, name='exportar_sin_ubicacion_excel'),
    
    # Reporte de conteo de almacén
    path('reporte-conteo-almacen/', views_reporte_conteo_almacen.reporte_conteo_almacen, name='reporte_conteo_almacen'),
    path('reporte-conteo-almacen/exportar/', views_reporte_conteo_almacen.exportar_conteo_almacen_excel, name='exportar_conteo_almacen_excel'),
]

from . import views_reporte_conteo_desagregado

urlpatterns.append(
    path("reporte-conteo-desagregado/", views_reporte_conteo_desagregado.reporte_conteo_desagregado, name="reporte_conteo_desagregado")
)
urlpatterns.append(
    path("reporte-conteo-desagregado/exportar/", views_reporte_conteo_desagregado.exportar_conteo_desagregado_excel, name="exportar_conteo_desagregado_excel")
)
