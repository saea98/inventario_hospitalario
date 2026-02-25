
"""
URLs para FASE 2: Gestión Logística
Incluye: Citas, Traslados y Conteo Físico
"""

from django.urls import path, include
from . import views_fase2, views_telegram_test, views_traslados_completo, views_conteo_fisico_v2, pedidos_views, views_dashboard_conteos, views_acuse_entrega, views_cedula_rechazo, views_citas_dos_pasos, picking_views
from . import llegada_urls

app_name = 'logistica'

urlpatterns = [
    # ========================================================================
    # CITAS DE PROVEEDORES
    # ========================================================================
    path('citas/', views_fase2.lista_citas, name='lista_citas'),
    path('citas/exportar/', views_fase2.exportar_citas_excel, name='exportar_citas_excel'),
    path('citas/crear/', views_citas_dos_pasos.crear_cita_paso1, name='crear_cita'),
    path('citas/crear/paso1/', views_citas_dos_pasos.crear_cita_paso1, name='crear_cita_paso1'),
    path('citas/crear/paso2/', views_citas_dos_pasos.crear_cita_paso2, name='crear_cita_paso2'),
    path('citas/crear/masiva/', views_citas_dos_pasos.crear_cita_masiva, name='crear_cita_masiva'),
    path('citas/agregar-detalle/', views_citas_dos_pasos.agregar_detalle_cita, name='agregar_detalle_cita'),
    path('citas/buscar-productos/', views_citas_dos_pasos.buscar_productos_cita, name='buscar_productos_cita'),
    path('citas/<int:pk>/editar/paso1/', views_citas_dos_pasos.editar_cita_paso1, name='editar_cita_paso1'),
    path('citas/<int:pk>/editar/paso2/', views_citas_dos_pasos.editar_cita_paso2, name='editar_cita_paso2'),
    path('citas/<int:pk>/', views_fase2.detalle_cita, name='detalle_cita'),
    path('citas/<int:pk>/toggle-no-material-medico/', views_fase2.toggle_no_material_medico, name='toggle_no_material_medico'),
    path('citas/<int:pk>/editar/', views_citas_dos_pasos.editar_cita_paso1, name='editar_cita'),
    path('citas/<int:pk>/validar-entrada/', views_fase2.validar_entrada, name='validar_entrada'),
    path('citas/<int:pk>/replicar-aprobacion-llegada/', views_fase2.replicar_aprobacion_llegada, name='replicar_aprobacion_llegada'),
    path('citas/<int:pk>/cancelar/', views_fase2.cancelar_cita, name='cancelar_cita'),
    path('citas/<int:pk>/cedula-rechazo/', views_cedula_rechazo.generar_cedula_rechazo, name='cedula_rechazo'),
    path('citas/<int:pk>/cedula-rechazo/imprimir/', views_cedula_rechazo.imprimir_cedula_rechazo, name='imprimir_cedula_rechazo'),
    
    # ========================================================================
    # TRASLADOS
    # ========================================================================
    path('traslados/', views_traslados_completo.lista_traslados, name='lista_traslados'),
    path('traslados/crear/', views_traslados_completo.crear_traslado, name='crear_traslado'),
    path('traslados/datos-desde-orden-suministro/', views_traslados_completo.datos_traslado_desde_orden_suministro, name='datos_traslado_desde_orden_suministro'),
    path('traslados/datos-desde-folio-pedido/', views_traslados_completo.datos_traslado_desde_folio_pedido, name='datos_traslado_desde_folio_pedido'),
    path('traslados/<int:pk>/', views_traslados_completo.detalle_traslado, name='detalle_traslado'),
    path('traslados/<int:pk>/editar/', views_traslados_completo.editar_traslado, name='editar_traslado'),
    path('traslados/<int:pk>/asignar-logistica/', views_traslados_completo.asignar_logistica_traslado, name='asignar_logistica_traslado'),
    path('traslados/<int:pk>/iniciar-transito/', views_traslados_completo.iniciar_transito_traslado, name='iniciar_transito_traslado'),
    path('traslados/<int:pk>/confirmar-recepcion/', views_traslados_completo.confirmar_recepcion_traslado, name='confirmar_recepcion_traslado'),
    path('traslados/<int:pk>/completar/', views_traslados_completo.completar_traslado, name='completar_traslado'),
    path('traslados/<int:pk>/cancelar/', views_traslados_completo.cancelar_traslado, name='cancelar_traslado'),
    path('traslados/<int:pk>/agregar-item/', views_traslados_completo.agregar_item_traslado, name='agregar_item_traslado'),
    path('traslados/<int:pk>/eliminar-item/<int:item_id>/', views_traslados_completo.eliminar_item_traslado, name='eliminar_item_traslado'),
    path('traslados/<int:pk>/validar-llegada/', views_traslados_completo.validar_llegada_traslado, name='validar_llegada_traslado'),
    
    # ========================================================================
    # CONTEO FÍSICO - Validación de Existencias (NUEVA VERSIÓN)
    # ========================================================================
    path('conteos/buscar/', views_conteo_fisico_v2.buscar_lote_conteo, name='buscar_lote_conteo'),
    path('conteos/seleccionar-ubicacion/', views_conteo_fisico_v2.seleccionar_ubicacion_conteo, name='seleccionar_ubicacion_conteo'),
    path('conteos/seleccionar/', views_conteo_fisico_v2.seleccionar_lote_conteo, name='seleccionar_lote_conteo'),
    path('conteos/lotes/<int:lote_id>/capturar/', views_conteo_fisico_v2.capturar_conteo_lote, name='capturar_conteo_lote'),
    path('conteos/ubicaciones/<int:lote_ubicacion_id>/capturar/', views_conteo_fisico_v2.capturar_conteo_lote, name='capturar_conteo_lote'),
    path('conteos/crear-lote/', views_conteo_fisico_v2.crear_lote_conteo, name='crear_lote_conteo'),
    path('conteos/historial/', views_conteo_fisico_v2.listar_conteos, name='historial_conteos'),
    path('conteos/exportar-personalizado/', views_conteo_fisico_v2.exportar_conteos_personalizado, name='exportar_conteos_personalizado'),
    path('conteos/carga-masiva/', views_conteo_fisico_v2.carga_masiva_conteos, name='carga_masiva_conteos'),
    path('conteos/movimientos/<int:movimiento_id>/', views_conteo_fisico_v2.detalle_movimiento_conteo, name='detalle_movimiento_conteo'),
    path('conteos/dashboard/', views_dashboard_conteos.dashboard_conteos, name='dashboard_conteos'),
    path('conteos/dashboard/exportar/excel/', views_dashboard_conteos.exportar_conteos_excel, name='exportar_conteos_excel'),
    path('conteos/dashboard/exportar/pdf/', views_dashboard_conteos.exportar_conteos_pdf, name='exportar_conteos_pdf'),
    
    # ========================================================================
    # FASE 2.2.1: GESTION DE PEDIDOS (RECONSTRUIDA)
    # ========================================================================
    path('pedidos/', pedidos_views.lista_solicitudes, name='lista_pedidos'),
    path('pedidos/crear/', pedidos_views.crear_solicitud, name='crear_pedido'),
    path('pedidos/api/verificar-folio/', pedidos_views.verificar_folio_pedido, name='verificar_folio_pedido'),
    path('pedidos/<uuid:solicitud_id>/', pedidos_views.detalle_solicitud, name='detalle_pedido'),
    path('pedidos/<uuid:solicitud_id>/validar/', pedidos_views.validar_solicitud, name='validar_pedido'),
    path('pedidos/<uuid:solicitud_id>/editar/', pedidos_views.editar_solicitud, name='editar_solicitud'),
    path('pedidos/<uuid:solicitud_id>/cancelar/', pedidos_views.cancelar_solicitud, name='cancelar_solicitud'),
    
    # Propuestas de Pedido (para personal de almacén)
    path('propuestas/', pedidos_views.lista_propuestas, name='lista_propuestas'),
    path('propuestas/<uuid:propuesta_id>/', pedidos_views.detalle_propuesta, name='detalle_propuesta'),
    path('propuestas/<uuid:propuesta_id>/acuse-pdf/', views_acuse_entrega.generar_acuse_entrega_pdf, name='generar_acuse_pdf'),
    path('propuestas/<uuid:propuesta_id>/acuse-excel/', views_acuse_entrega.generar_acuse_entrega_excel, name='generar_acuse_excel'),
    path('propuestas/<uuid:propuesta_id>/cancelar/', pedidos_views.cancelar_propuesta_view, name='cancelar_propuesta'),
    path('propuestas/<uuid:propuesta_id>/eliminar/', pedidos_views.eliminar_propuesta_view, name='eliminar_propuesta'),
    path('propuestas/<uuid:propuesta_id>/editar/', pedidos_views.editar_propuesta, name='editar_propuesta'),
    path('propuestas/<uuid:propuesta_id>/picking/', picking_views.picking_propuesta, name='picking_propuesta'),
    path('propuestas/<uuid:propuesta_id>/picking/imprimir/', picking_views.imprimir_hoja_surtido, name='imprimir_hoja_surtido'),
    path('propuestas/<uuid:propuesta_id>/picking/exportar-excel/', picking_views.exportar_picking_excel, name='exportar_picking_excel'),
    path('propuestas/<uuid:propuesta_id>/revisar/', pedidos_views.revisar_propuesta, name='revisar_propuesta'),
    path('propuestas/<uuid:propuesta_id>/surtir/', pedidos_views.surtir_propuesta, name='surtir_propuesta'),
    path('propuestas/auditar-surtido-documento/', pedidos_views.auditar_surtido_documento, name='auditar_surtido_documento'),
    path('propuestas/auditar-surtido-documento/exportar-excel/', pedidos_views.exportar_auditoria_surtido_excel, name='exportar_auditoria_surtido_excel'),
    path('api/obtener-ubicaciones-producto/', pedidos_views.obtener_ubicaciones_producto, name='obtener_ubicaciones_producto'),
    path('api/corregir-dato-lote/', pedidos_views.corregir_dato_lote, name='corregir_dato_lote'),
    
    # ========================================================================
    # FASE 2.2.2: LLEGADA DE PROVEEDORES
    # ========================================================================
    path('llegadas/', include(llegada_urls)),
    
    # ========================================================================
    # PRUEBA DE TELEGRAM
    # ========================================================================
    path('test-telegram/', views_telegram_test.test_telegram, name='test_telegram'),
    path('api/telegram/chat-id/', views_telegram_test.obtener_chat_id_desde_updates, name='api_telegram_chat_id'),
]
