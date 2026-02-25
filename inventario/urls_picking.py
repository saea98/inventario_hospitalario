"""
URLs para Fase 6 - Optimización de Picking
"""

from django.urls import path
from . import picking_views

app_name = 'picking'

urlpatterns = [
    # Dashboard
    path('', picking_views.dashboard_picking, name='dashboard'),
    # Monitor electrónico vs manual
    path('monitor/', picking_views.monitor_picking, name='monitor'),

    # Picking (redirige a logistica/propuestas/<uuid>/picking/)
    path('propuesta/<uuid:propuesta_id>/', picking_views.redirect_picking_propuesta_a_logistica, name='picking_propuesta'),
    
    # AJAX
    path(
        "marcar-recogido/<uuid:lote_asignado_id>/",
        picking_views.marcar_item_recogido,
        name="marcar_recogido",
    ),
    path(
        "ubicaciones-para-corregir-lote/",
        picking_views.ubicaciones_para_corregir_lote,
        name="ubicaciones_para_corregir_lote",
    ),
    path(
        "corregir-lote/<uuid:lote_asignado_id>/",
        picking_views.corregir_lote_propuesta,
        name="corregir_lote_propuesta",
    ),
    path(
        "propuesta/<uuid:propuesta_id>/imprimir/",
        picking_views.imprimir_hoja_surtido,
        name="imprimir_hoja_surtido",
    ),
    path(
        "propuesta/<uuid:propuesta_id>/exportar-excel/",
        picking_views.exportar_picking_excel,
        name="exportar_picking_excel",
    ),
]