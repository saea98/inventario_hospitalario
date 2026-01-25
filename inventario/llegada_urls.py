"""
URLs para la Fase 2.2.2: Llegada de Proveedores
"""

from django.urls import path
from .llegada_views import (
    ListaLlegadasView,
    CrearLlegadaView,
    EditarLlegadaView,
    DetalleLlegadaView,
    AprobarEntradaView,
    ControlCalidadView,
    FacturacionView,
    SupervisionView,
    UbicacionView,
    SubirDocumentoView,
    ImprimirEPAView,
    exportar_llegadas_excel,
    api_productos,
    api_ubicaciones_por_almacen,
    api_cita_folio,
    api_debug_citas_disponibles,
)

app_name = 'llegadas'

urlpatterns = [
    path('', ListaLlegadasView.as_view(), name='lista_llegadas'),
    path('exportar-excel/', exportar_llegadas_excel, name='exportar_llegadas_excel'),
    path('crear/', CrearLlegadaView.as_view(), name='crear_llegada'),
    path('api/productos/', api_productos, name='api_productos'),
    path('api/ubicaciones-por-almacen/', api_ubicaciones_por_almacen, name='api_ubicaciones_por_almacen'),
    path('api/cita/<int:cita_id>/folio/', api_cita_folio, name='api_cita_folio'),
    path('api/debug/citas-disponibles/', api_debug_citas_disponibles, name='api_debug_citas_disponibles'),
    path('<uuid:pk>/', DetalleLlegadaView.as_view(), name='detalle_llegada'),
    path('<uuid:pk>/editar/', EditarLlegadaView.as_view(), name='editar_llegada'),
    path('<uuid:pk>/aprobar/', AprobarEntradaView.as_view(), name='aprobar_entrada'),
    path('<uuid:pk>/calidad/', ControlCalidadView.as_view(), name='control_calidad'),
    path('<uuid:pk>/facturacion/', FacturacionView.as_view(), name='facturacion'),
    path('<uuid:pk>/supervision/', SupervisionView.as_view(), name='supervision'),
    path('<uuid:pk>/ubicacion/', UbicacionView.as_view(), name='ubicacion'),
    path('<uuid:pk>/documento/', SubirDocumentoView.as_view(), name='subir_documento'),
    path('<uuid:pk>/imprimir-epa/', ImprimirEPAView.as_view(), name='imprimir_epa'),
]
