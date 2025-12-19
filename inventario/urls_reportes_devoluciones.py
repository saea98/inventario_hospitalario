"""
URLs para Reportes de Devoluciones de Proveedores
Fase 2.5 - Reportes y Análisis Avanzados
"""

from django.urls import path
from . import views_reportes_devoluciones

app_name = 'reportes_devoluciones'

urlpatterns = [
    # Reportes principales
    path('reporte-general/', views_reportes_devoluciones.reporte_general_devoluciones, name='reporte_general'),
    path('analisis-proveedores/', views_reportes_devoluciones.analisis_proveedores, name='analisis_proveedores'),
    path('analisis-temporal/', views_reportes_devoluciones.analisis_temporal, name='analisis_temporal'),
    
    # APIs para gráficos
    path('api/grafico-estado/', views_reportes_devoluciones.api_grafico_estado, name='api_grafico_estado'),
    path('api/grafico-proveedores/', views_reportes_devoluciones.api_grafico_proveedores, name='api_grafico_proveedores'),
    path('api/grafico-tendencia/', views_reportes_devoluciones.api_grafico_tendencia, name='api_grafico_tendencia'),
    path('api/grafico-motivos/', views_reportes_devoluciones.api_grafico_motivos, name='api_grafico_motivos'),
]
