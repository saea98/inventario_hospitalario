"""
URLs para la Fase 2.2.2: Llegada de Proveedores
"""

from django.urls import path
from .llegada_views import (
    ListaLlegadasView,
    CrearLlegadaView,
    DetalleLlegadaView,
    ControlCalidadView,
    FacturacionView,
    SupervisionView,
    UbicacionView,
    SubirDocumentoView,
    api_productos,
)

app_name = 'llegadas'

urlpatterns = [
    path('', ListaLlegadasView.as_view(), name='lista_llegadas'),
    path('crear/', CrearLlegadaView.as_view(), name='crear_llegada'),
    path('api/productos/', api_productos, name='api_productos'),
    path('<uuid:pk>/', DetalleLlegadaView.as_view(), name='detalle_llegada'),
    path('<uuid:pk>/calidad/', ControlCalidadView.as_view(), name='control_calidad'),
    path('<uuid:pk>/facturacion/', FacturacionView.as_view(), name='facturacion'),
    path('<uuid:pk>/supervision/', SupervisionView.as_view(), name='supervision'),
    path('<uuid:pk>/ubicacion/', UbicacionView.as_view(), name='ubicacion'),
    path('<uuid:pk>/documento/', SubirDocumentoView.as_view(), name='subir_documento'),
]
