from django.urls import path, include
from . import views, reportes_urls, sql_urls
from . import urls_entrada_salida, urls_fase2, urls_inventario, urls_devoluciones, urls_reportes_devoluciones, urls_reportes_salidas, urls_picking
from .views_dashboard_movimientos import dashboard_movimientos, api_estadisticas_movimientos
from .views_logs import lista_logs, detalle_log, marcar_resuelto, limpiar_logs, api_logs_recientes
from .views_health import health_check, diagnostico_sistema
from .views_asignacion_rapida import asignacion_rapida, api_buscar_lote, api_obtener_ubicaciones, api_asignar_ubicacion
from .views_carga_masiva import carga_masiva_lotes, carga_masiva_resultado
from .views_reporte_ubicaciones_vacias import reporte_ubicaciones_vacias, exportar_ubicaciones_vacias_excel, exportar_ubicaciones_vacias_pdf
#from inventario.admin import inventario_admin
from django.contrib import admin as django_admin


urlpatterns = [
    # Health Check y Diagnóstico
    path('health/', health_check, name='health_check'),
    path('diagnostico/', diagnostico_sistema, name='diagnostico_sistema'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('api/estadisticas/', views.api_estadisticas_dashboard, name='api_estadisticas_dashboard'),

    # Instituciones
    path('instituciones/', views.lista_instituciones, name='lista_instituciones'),
    path('instituciones/crear/', views.crear_institucion, name='crear_institucion'),
    path('instituciones/<int:pk>/', views.detalle_institucion, name='detalle_institucion'),
    path('instituciones/<int:pk>/editar/', views.editar_institucion, name='editar_institucion'),

    # Productos
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),

    # Lotes
    path('lotes/', views.lista_lotes, name='lista_lotes'),
    path('lotes/crear/', views.crear_lote, name='crear_lote'),
    path('lotes/<int:pk>/', views.detalle_lote, name='detalle_lote'),
    path('lotes/<int:pk>/editar/', views.editar_lote, name='editar_lote'),
    path('lotes/<int:pk>/editar-ubicaciones/', views.editar_ubicaciones_lote, name='editar_ubicaciones_lote'),
    path('lotes/<int:pk>/eliminar/', views.eliminar_lote, name='eliminar_lote'),
    path('lotes/<int:pk>/marcar-caducado/', views.marcar_lote_caducado, name='marcar_lote_caducado'),
    path('lotes/<int:pk>/crear-alerta/', views.crear_alerta_lote, name='crear_alerta_lote'),
    
    # Asignación Rápida de Ubicaciones
    path('asignacion-rapida/', asignacion_rapida, name='asignacion_rapida'),
    path('api/buscar-lote/', api_buscar_lote, name='api_buscar_lote'),
    path('api/obtener-ubicaciones/', api_obtener_ubicaciones, name='api_obtener_ubicaciones'),
    path('api/asignar-ubicacion/', api_asignar_ubicacion, name='api_asignar_ubicacion'),
    
    # Carga Masiva de Lotes
    path('carga-masiva/', carga_masiva_lotes, name='carga_masiva_lotes'),
    path('carga-masiva/resultado/', carga_masiva_resultado, name='carga_masiva_resultado'),

    # Movimientos
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos/crear/', views.crear_movimiento, name='crear_movimiento'),
    path('movimientos/<int:pk>/detalle/', views.detalle_movimiento, name='detalle_movimiento'),
    path('movimientos/<int:pk>/anular/', views.anular_movimiento, name='anular_movimiento'),
    path('movimientos/<int:pk>/editar/', views.editar_movimiento, name='editar_movimiento'),
    path('lotes/reporte-excel/', views.reporte_lotes_excel, name='reporte_lotes_excel'),

    # Cargas
    path('cargas/', views.lista_cargas, name='lista_cargas'),
    path('cargas/nueva/', views.cargar_archivo_excel, name='cargar_archivo_excel'),
    path('cargas/<int:pk>/', views.detalle_carga, name='detalle_carga'),

    # Dashboard de Movimientos
    path('dashboard/movimientos/', dashboard_movimientos, name='dashboard_movimientos'),
    path('api/movimientos/estadisticas/', api_estadisticas_movimientos, name='api_estadisticas_movimientos'),
    
    # Logs del Sistema
    path('sistema/logs/', lista_logs, name='lista_logs'),
    path('sistema/logs/<int:pk>/', detalle_log, name='detalle_log'),
    path('sistema/logs/<int:pk>/marcar-resuelto/', marcar_resuelto, name='marcar_resuelto'),
    path('sistema/logs/limpiar/', limpiar_logs, name='limpiar_logs'),
    path('api/logs/recientes/', api_logs_recientes, name='api_logs_recientes'),
    
    # Reportes
    path('reportes/', views.reportes_dashboard, name='reportes_dashboard'),
    path('reportes/inventario/excel/', views.descargar_reporte_inventario, name='reporte_inventario_excel'),
    path('reportes/movimientos/excel/', views.descargar_reporte_movimientos, name='reporte_movimientos_excel'),
    path('reportes/caducidades/excel/', views.descargar_reporte_caducidades, name='reporte_caducidades_excel'),
    path('reportes/ubicaciones-vacias/', reporte_ubicaciones_vacias, name='reporte_ubicaciones_vacias'),
    path('reportes/ubicaciones-vacias/exportar-excel/', exportar_ubicaciones_vacias_excel, name='exportar_ubicaciones_vacias_excel'),
    path('reportes/ubicaciones-vacias/exportar-pdf/', exportar_ubicaciones_vacias_pdf, name='exportar_ubicaciones_vacias_pdf'),

    # Configuración y Ayuda
    path('configuracion/', views.configuracion_sistema, name='configuracion_sistema'),
    path('ayuda/', views.ayuda_sistema, name='ayuda_sistema'),
    path('manual/', views.manual_usuario, name='manual_usuario'),

    # Registro
    path('registro/', views.registro_usuario, name='registro'),

    #Alertas
    path('alertas/caducidad/', views.alertas_caducidad, name='alertas_caducidad'),
    #Carga masiva clues
    path('carga-masiva-instituciones/', views.carga_masiva_instituciones, name='carga_masiva_instituciones'),
    path('borrar-instituciones/', views.borrar_instituciones, name='borrar_instituciones'),

    # inventario/urls.py
    path('solicitudes/', views.lista_solicitudes_semanales, name='lista_solicitudes'),
    path('solicitudes/detalle/<str:fecha>/', views.detalle_solicitud, name='detalle_solicitud'),
    path('carga-masiva-solicitud/', views.carga_masiva_solicitud, name='carga_masiva_solicitud'),
    path('complemento-carga-masiva-solicitud/', views.complemento_carga_masiva, name='complemento_carga_masiva'),
    path('borrar-solicitud/<str:fecha>/', views.borrar_solicitud, name='borrar_solicitud_fecha'),
    path('borrar-solicitud/', views.borrar_solicitud, name='borrar_solicitud_todas'),
    path('solicitudes/exportar/<str:fecha>/', views.exportar_solicitud_excel, name='exportar_solicitud_excel'),
    path("reporte_personalizado/", views.reporte_personalizado, name="reporte_personalizado"),

    path('ajax/ubicaciones/', views.ajax_ubicaciones_por_almacen, name='ajax_ubicaciones_por_almacen'),
    path('carga-lotes-excel/', views.carga_lotes_desde_excel_view, name='carga_lotes_excel'),
    path('inventario/', include(urls_entrada_salida)),
    path('logistica/', include(urls_fase2)),  # URLs de FASE 2: Citas, Traslados, Conteo, Propuestas y Acuse de Entrega
    path('gestion-inventario/', include(urls_inventario)),  # URLs de FASE 2.3: Gestión de Inventario
    path('devoluciones/', include(urls_devoluciones)),  # URLs de FASE 2.4: Devoluciones de Proveedores
    path('reportes/devoluciones/', include(urls_reportes_devoluciones)),  # URLs de FASE 2.5: Reportes de Devoluciones
    path('reportes/salidas/', include(urls_reportes_salidas)),  # URLs de FASE 4: Reportes de Salidas
    path('picking/', include(urls_picking)),  # URLs de FASE 6: Optimización de Picking
    path('admin/', django_admin.site.urls),
    path('reportes/', include(reportes_urls)),
    path('admin/', include(sql_urls)),
    
]