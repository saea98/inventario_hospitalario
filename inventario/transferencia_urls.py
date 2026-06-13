from django.urls import path

from . import transferencia_views

app_name = 'transferencias'

urlpatterns = [
    path('', transferencia_views.ListaTransferenciasView.as_view(), name='lista_transferencias'),
    path('crear/', transferencia_views.CrearTransferenciaView.as_view(), name='crear_transferencia'),
    path('<uuid:pk>/', transferencia_views.DetalleTransferenciaView.as_view(), name='detalle_transferencia'),
    path('<uuid:pk>/editar/', transferencia_views.EditarTransferenciaView.as_view(), name='editar_transferencia'),
    path('<uuid:pk>/aprobar/', transferencia_views.AprobarTransferenciaView.as_view(), name='aprobar_transferencia'),
    path('<uuid:pk>/imprimir-epa/', transferencia_views.ImprimirEPATransferenciaView.as_view(), name='imprimir_epa'),
    path('api/buscar-clave/', transferencia_views.api_buscar_clave_producto, name='api_buscar_clave'),
]
