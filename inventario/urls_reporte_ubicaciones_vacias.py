"""
URLs para el reporte de ubicaciones vacías
Agregar estas líneas a tu urls.py principal
"""

from django.urls import path
from .views_reporte_ubicaciones_vacias import (
    reporte_ubicaciones_vacias,
    exportar_ubicaciones_vacias_excel,
    exportar_ubicaciones_vacias_pdf,
)

urlpatterns = [
    path('reportes/ubicaciones-vacias/', reporte_ubicaciones_vacias, name='reporte_ubicaciones_vacias'),
    path('reportes/ubicaciones-vacias/exportar-excel/', exportar_ubicaciones_vacias_excel, name='exportar_ubicaciones_vacias_excel'),
    path('reportes/ubicaciones-vacias/exportar-pdf/', exportar_ubicaciones_vacias_pdf, name='exportar_ubicaciones_vacias_pdf'),
]
