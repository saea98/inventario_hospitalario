"""
URLs para el módulo de Gestión de Pedidos
"""

from django.urls import path
from . import pedidos_views, pedidos_reports_views

app_name = 'pedidos'

urlpatterns = [
    # Vistas de Pedidos
    path('crear/', pedidos_views.crear_solicitud, name='crear_solicitud'),
    path('lista/', pedidos_views.lista_solicitudes, name='lista_solicitudes'),
    path('<uuid:solicitud_id>/', pedidos_views.detalle_solicitud, name='detalle_solicitud'),
    path('<uuid:solicitud_id>/validar/', pedidos_views.validar_solicitud, name='validar_solicitud'),
    path('<uuid:solicitud_id>/editar/', pedidos_views.editar_solicitud, name='editar_solicitud'),
    path('<uuid:solicitud_id>/cancelar/', pedidos_views.cancelar_solicitud, name='cancelar_solicitud'),
    
    # Reportes de Errores
    path('reportes/errores/', pedidos_reports_views.reporte_errores_pedidos, name='reporte_errores'),
    path('reportes/items-no-surtidos/', pedidos_reports_views.reporte_items_no_surtidos, name='reporte_items_no_surtidos'),
    path('reportes/claves-sin-existencia/exportar/', pedidos_reports_views.exportar_claves_sin_existencia_excel, name='exportar_claves_sin_existencia_excel'),
    path('reportes/claves-sin-existencia/', pedidos_reports_views.reporte_claves_sin_existencia, name='reporte_claves_sin_existencia'),
    path('reportes/pedidos-sin-existencia/exportar/', pedidos_reports_views.exportar_pedidos_sin_existencia_excel, name='exportar_pedidos_sin_existencia_excel'),
    path('reportes/pedidos-sin-existencia/', pedidos_reports_views.reporte_pedidos_sin_existencia, name='reporte_pedidos_sin_existencia'),
    path('reportes/claves-no-existen/', pedidos_reports_views.reporte_claves_no_existen, name='reporte_claves_no_existen'),
]
