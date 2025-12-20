"""
URLs para Fase 6 - Optimización de Picking
"""

from django.urls import path
from . import picking_views

app_name = 'picking'

urlpatterns = [
    # Picking
    path('propuesta/<uuid:propuesta_id>/', picking_views.picking_propuesta, name='picking_propuesta'),
    path('propuesta/<uuid:propuesta_id>/pdf/', picking_views.generar_picking_pdf, name='generar_picking_pdf'),
    
    # AJAX
    path('marcar-recogido/<uuid:lote_asignado_id>/', picking_views.marcar_item_recogido, name='marcar_recogido'),
]
