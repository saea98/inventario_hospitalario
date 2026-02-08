from django.urls import path
from .reportes_views import ReporteEntradasView
from .views_reporte_disponibilidad import reporte_disponibilidad_lotes, exportar_disponibilidad_excel
from .views_reporte_lote_pedidos import reporte_lote_pedidos, exportar_lote_pedidos_excel
from .views_reporte_auditoria_propuestas import reporte_auditoria_propuestas
from .views_reporte_productos_no_disponibles import reporte_productos_no_disponibles, exportar_productos_no_disponibles_excel
from .views_reporte_inventario_detallado import (
    reporte_inventario_detallado,
    exportar_inventario_detallado_excel,
    carga_masiva_inventario_detallado,
)

app_name = 'reportes'

urlpatterns = [
    path("entradas/", ReporteEntradasView.as_view(), name="reporte_entradas"),
    path("disponibilidad-lotes/", reporte_disponibilidad_lotes, name="reporte_disponibilidad_lotes"),
    path("disponibilidad-lotes/exportar-excel/", exportar_disponibilidad_excel, name="exportar_disponibilidad_excel"),
    path("lote-pedidos/", reporte_lote_pedidos, name="reporte_lote_pedidos"),
    path("lote-pedidos/exportar-excel/", exportar_lote_pedidos_excel, name="exportar_lote_pedidos_excel"),
    path("auditoria-propuestas/", reporte_auditoria_propuestas, name="reporte_auditoria_propuestas"),
    path("productos-no-disponibles/", reporte_productos_no_disponibles, name="reporte_productos_no_disponibles"),
    path("productos-no-disponibles/exportar-excel/", exportar_productos_no_disponibles_excel, name="exportar_productos_no_disponibles_excel"),
    path("inventario-detallado/", reporte_inventario_detallado, name="reporte_inventario_detallado"),
    path("inventario-detallado/exportar-excel/", exportar_inventario_detallado_excel, name="exportar_inventario_detallado_excel"),
    path("inventario-detallado/carga-masiva/", carga_masiva_inventario_detallado, name="carga_masiva_inventario_detallado"),
]
