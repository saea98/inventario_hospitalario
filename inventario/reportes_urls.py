from django.urls import path
from .reportes_views import ReporteEntradasView

urlpatterns = [
    path("entradas/", ReporteEntradasView.as_view(), name="reporte_entradas"),
]
