from django.urls import path
from . import views
from inventario.admin import inventario_admin

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
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
    # Comentamos esta línea hasta que implementemos la vista
    # path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    
    # Lotes
    path('lotes/', views.lista_lotes, name='lista_lotes'),
    path('lotes/crear/', views.crear_lote, name='crear_lote'),
    path('lotes/<int:pk>/', views.detalle_lote, name='detalle_lote'),
    path('admin/', inventario_admin.urls),
    # Comentamos estas líneas hasta que implementemos las vistas
    # path('lotes/<int:pk>/editar/', views.editar_lote, name='editar_lote'),
    # path('lotes/<int:pk>/eliminar/', views.eliminar_lote, name='eliminar_lote'),
    
    # Movimientos - Solo si las vistas están implementadas
    # path('movimientos/crear/', views.crear_movimiento, name='crear_movimiento'),
    # path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    
    # Acciones de lotes - Solo si las vistas están implementadas
    # path('lotes/<int:pk>/marcar-caducado/', views.marcar_lote_caducado, name='marcar_lote_caducado'),
    # path('lotes/<int:pk>/crear-alerta/', views.crear_alerta_lote, name='crear_alerta_lote'),
    
    # Alertas
    path('alertas/caducidad/', views.alertas_caducidad, name='alertas_caducidad'),
    
    # API
    path('api/estadisticas/', views.api_estadisticas_dashboard, name='api_estadisticas_dashboard'),
    
    # Registro
    path('registro/', views.registro_usuario, name='registro'),
]

# Importar vistas adicionales
from .views_extras import (
    cargar_archivo_excel, detalle_carga, lista_cargas,
    descargar_reporte_inventario, descargar_reporte_movimientos,
    descargar_reporte_caducidades, reportes_dashboard,
    configuracion_sistema, ayuda_sistema, manual_usuario
)

# URLs adicionales para funcionalidades avanzadas
urlpatterns += [
    # Carga de archivos
    path('cargas/', lista_cargas, name='lista_cargas'),
    path('cargas/nueva/', cargar_archivo_excel, name='cargar_archivo_excel'),
    path('cargas/<int:pk>/', detalle_carga, name='detalle_carga'),
    
    # Reportes
    path('reportes/', reportes_dashboard, name='reportes_dashboard'),
    path('reportes/inventario/excel/', descargar_reporte_inventario, name='reporte_inventario_excel'),
    path('reportes/movimientos/excel/', descargar_reporte_movimientos, name='reporte_movimientos_excel'),
    path('reportes/caducidades/excel/', descargar_reporte_caducidades, name='reporte_caducidades_excel'),
    
    # Configuración y ayuda
    path('configuracion/', configuracion_sistema, name='configuracion_sistema'),
    path('ayuda/', ayuda_sistema, name='ayuda_sistema'),
    path('manual/', manual_usuario, name='manual_usuario'),
]
