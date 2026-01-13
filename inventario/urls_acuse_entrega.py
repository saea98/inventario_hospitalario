"""
URLs para el módulo de Acuse de Entrega
Agregar estas líneas a tu urls.py principal
"""

from django.urls import path
from .views_acuse_entrega import (
    lista_propuestas_surtimiento,
    detalle_propuesta_surtimiento,
    generar_acuse_entrega_pdf,
)

urlpatterns = [
    path('propuestas/', lista_propuestas_surtimiento, name='lista_propuestas_surtimiento'),
    path('propuestas/<uuid:propuesta_id>/', detalle_propuesta_surtimiento, name='detalle_propuesta_surtimiento'),
    path('propuestas/<uuid:propuesta_id>/acuse-pdf/', generar_acuse_entrega_pdf, name='generar_acuse_entrega_pdf'),
]
