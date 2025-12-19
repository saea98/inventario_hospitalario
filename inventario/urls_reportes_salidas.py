"""
URLs para Reportes de Salidas
"""

from django.urls import path
from . import views_reportes_salidas

app_name = 'reportes_salidas'

urlpatterns = [
    # Reportes
    path('general/', views_reportes_salidas.reporte_general_salidas, name='reporte_general'),
    path('distribuciones/', views_reportes_salidas.analisis_distribuciones, name='analisis_distribuciones'),
    path('temporal/', views_reportes_salidas.analisis_temporal, name='analisis_temporal'),
]
