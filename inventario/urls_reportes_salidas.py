"""
URLs para Reportes de Salidas y Distribuciones
"""

from django.urls import path
from . import views_reportes_salidas

app_name = 'reportes_salidas'

urlpatterns = [
    # Reportes
    path('general/', views_reportes_salidas.reporte_general_salidas, name='reporte_general'),
    path('distribuciones/', views_reportes_salidas.analisis_distribuciones, name='analisis_distribuciones'),
    path('temporal/', views_reportes_salidas.analisis_temporal_salidas, name='analisis_temporal'),
    
    # APIs para gráficos
    path('api/grafico-salidas-estado/', views_reportes_salidas.api_grafico_salidas_por_estado, name='api_grafico_salidas_estado'),
    path('api/grafico-salidas-almacen/', views_reportes_salidas.api_grafico_salidas_por_almacen, name='api_grafico_salidas_almacen'),
    path('api/grafico-distribuciones-estado/', views_reportes_salidas.api_grafico_distribuciones_por_estado, name='api_grafico_distribuciones_estado'),
    path('api/grafico-salidas-dia/', views_reportes_salidas.api_grafico_salidas_por_dia, name='api_grafico_salidas_dia'),
]
