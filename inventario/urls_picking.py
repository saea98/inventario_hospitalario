"""
URLs para Fase 6 - Optimización de Picking
"""

from django.urls import path
from . import picking_views

app_name = 'picking'

urlpatterns = [
    # Dashboard
    path('', picking_views.dashboard_picking, name='dashboard'),
    
    # Picking
    path('propuesta/<uuid:propuesta_id>/', picking_views.picking_propuesta, name='picking_propuesta'),
    
    # AJAX
    path(
        "marcar-recogido/<uuid:lote_asignado_id>/",
        picking_views.marcar_item_recogido,
        name="marcar_recogido",
    ),
    path(
        "propuesta/<uuid:propuesta_id>/imprimir/",
        picking_views.imprimir_hoja_surtido,
        name="imprimir_hoja_surtido",
    ),
]