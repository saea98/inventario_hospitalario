"""
URLs para los módulos de ENTRADA AL ALMACÉN y PROVEEDURÍA
"""

from django.urls import path
from . import views_entrada_salida

urlpatterns = [
    # ENTRADA AL ALMACÉN
    path('entrada-almacen/paso1/', views_entrada_salida.entrada_almacen_paso1, name='entrada_almacen_paso1'),
    path('entrada-almacen/paso2/', views_entrada_salida.entrada_almacen_paso2, name='entrada_almacen_paso2'),
    path('entrada-almacen/confirmacion/', views_entrada_salida.entrada_almacen_confirmacion, name='entrada_almacen_confirmacion'),
    
    # PROVEEDURÍA
    path('proveeduria/paso1/', views_entrada_salida.proveeduria_paso1, name='proveeduria_paso1'),
    path('proveeduria/paso2/', views_entrada_salida.proveeduria_paso2, name='proveeduria_paso2'),
    path('proveeduria/confirmacion/', views_entrada_salida.proveeduria_confirmacion, name='proveeduria_confirmacion'),
    
    # AJAX
    path('api/lotes-disponibles/', views_entrada_salida.obtener_lotes_disponibles, name='obtener_lotes_disponibles'),
    path('api/lotes-por-producto/', views_entrada_salida.obtener_lotes_por_producto, name='obtener_lotes_por_producto'),
    path('api/detalles-lote/', views_entrada_salida.obtener_detalles_lote, name='obtener_detalles_lote'),
    path('api/validar-item-entrada/', views_entrada_salida.validar_item_entrada, name='validar_item_entrada'),
]
