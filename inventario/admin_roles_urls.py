"""
URLs para el dashboard de administración de roles
"""

from django.urls import path
from . import admin_roles_views

app_name = 'admin_roles'

urlpatterns = [
    # Dashboard principal
    path('', admin_roles_views.dashboard_admin_roles, name='dashboard'),
    
    # Gestión de usuarios
    path('usuarios/', admin_roles_views.lista_usuarios_roles, name='lista_usuarios'),
    path('usuarios/<int:usuario_id>/editar/', admin_roles_views.editar_usuario_roles, name='editar_usuario'),
    path('usuarios/asignar-rol/', admin_roles_views.asignar_rol_usuario_ajax, name='asignar_rol_ajax'),
    
    # Gestión de roles
    path('roles/', admin_roles_views.lista_roles, name='lista_roles'),
    path('roles/<int:rol_id>/', admin_roles_views.detalle_rol, name='detalle_rol'),
    
    # Gestión de opciones de menú
    path('menu/', admin_roles_views.lista_opciones_menu, name='lista_opciones_menu'),
    path('menu/<int:opcion_id>/editar/', admin_roles_views.editar_opcion_menu, name='editar_opcion_menu'),
    
    # Reportes
    path('reporte-acceso/', admin_roles_views.reporte_acceso, name='reporte_acceso'),
    path('estadisticas/', admin_roles_views.estadisticas_roles, name='estadisticas'),
]
