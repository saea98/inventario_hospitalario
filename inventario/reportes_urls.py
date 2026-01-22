from django.urls import path
from .reportes_views import ReporteEntradasView
from .views_reporte_disponibilidad import reporte_disponibilidad_lotes, exportar_disponibilidad_excel
from .views_reporte_lote_pedidos import reporte_lote_pedidos, exportar_lote_pedidos_excel

app_name = 'reportes'

urlpatterns = [
    path("entradas/", ReporteEntradasView.as_view(), name="reporte_entradas"),
    path("disponibilidad-lotes/", reporte_disponibilidad_lotes, name="reporte_disponibilidad_lotes"),
    path("disponibilidad-lotes/exportar-excel/", exportar_disponibilidad_excel, name="exportar_disponibilidad_excel"),
    path("lote-pedidos/", reporte_lote_pedidos, name="reporte_lote_pedidos"),
    path("lote-pedidos/exportar-excel/", exportar_lote_pedidos_excel, name="exportar_lote_pedidos_excel"),
]
