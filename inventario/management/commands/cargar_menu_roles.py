"""
Comando de Django para cargar la configuración inicial del menú por roles
Uso: python manage.py cargar_menu_roles
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from inventario.models import MenuItemRol


class Command(BaseCommand):
    help = 'Carga la configuración inicial del menú por roles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🔧 CARGAR CONFIGURACIÓN DE MENÚ POR ROLES'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # Definir la configuración del menú
        menu_config = [
            # Dashboard - Todos pueden verlo
            {
                'menu_item': 'dashboard',
                'nombre_mostrado': 'Dashboard',
                'icono': 'fas fa-tachometer-alt',
                'url_name': 'dashboard',
                'roles': ['Revisión', 'Almacenero', 'Control Calidad', 'Facturación', 
                         'Supervisión', 'Logística', 'Recepción', 'Conteo', 
                         'Gestor de Inventario', 'Administrador'],
                'orden': 1,
                'es_submenu': False,
            },

            # ===== SECCIÓN ADMINISTRACIÓN =====
            {
                'menu_item': 'admin_roles',
                'nombre_mostrado': 'Administración de Roles',
                'icono': 'fas fa-user-shield',
                'url_name': 'admin_roles:dashboard',
                'roles': ['Administrador'],
                'orden': 5,
                'es_submenu': False,
            },
            {
                'menu_item': 'instituciones',
                'nombre_mostrado': 'Instituciones',
                'icono': 'fas fa-building',
                'url_name': 'lista_instituciones',
                'roles': ['Administrador'],
                'orden': 10,
                'es_submenu': False,
            },
            {
                'menu_item': 'productos',
                'nombre_mostrado': 'Productos',
                'icono': 'fas fa-pills',
                'url_name': 'lista_productos',
                'roles': ['Administrador'],
                'orden': 11,
                'es_submenu': False,
            },
            {
                'menu_item': 'proveedores',
                'nombre_mostrado': 'Proveedores',
                'icono': 'fas fa-truck',
                'url_name': 'lista_proveedores',
                'roles': ['Administrador'],
                'orden': 12,
                'es_submenu': False,
            },
            {
                'menu_item': 'alcaldias',
                'nombre_mostrado': 'Alcaldías',
                'icono': 'fas fa-map',
                'url_name': 'lista_alcaldias',
                'roles': ['Administrador'],
                'orden': 13,
                'es_submenu': False,
            },
            {
                'menu_item': 'almacenes',
                'nombre_mostrado': 'Almacenes',
                'icono': 'fas fa-warehouse',
                'url_name': 'lista_almacenes',
                'roles': ['Administrador'],
                'orden': 14,
                'es_submenu': False,
            },
            {
                'menu_item': 'ubicaciones_almacen',
                'nombre_mostrado': 'Ubicaciones de Almacén',
                'icono': 'fas fa-map-marker-alt',
                'url_name': 'lista_ubicaciones_almacen',
                'roles': ['Administrador', 'Gestor de Inventario', 'Almacenero', 'Supervisión'],
                'orden': 15,
                'es_submenu': False,
            },

            # ===== SECCIÓN EXISTENCIAS =====
            {
                'menu_item': 'existencias',
                'nombre_mostrado': 'Existencias',
                'icono': 'fas fa-boxes',
                'url_name': 'lista_lotes',
                'roles': ['Almacenero', 'Supervisión', 'Administrador', 'Gestor de Inventario'],
                'orden': 20,
                'es_submenu': False,
            },

            # ===== SECCIÓN OPERACIONES =====
            {
                'menu_item': 'entrada_almacen',
                'nombre_mostrado': 'Entrada al Almacén',
                'icono': 'fas fa-inbox',
                'url_name': 'entrada_almacen_paso1',
                'roles': ['Almacenero', 'Supervisión', 'Administrador'],
                'orden': 30,
                'es_submenu': False,
            },
            {
                'menu_item': 'salidas_almacen',
                'nombre_mostrado': 'Salidas del Almacén',
                'icono': 'fas fa-dolly',
                'url_name': 'proveeduria_paso1',
                'roles': ['Almacenero', 'Supervisión', 'Administrador'],
                'orden': 31,
                'es_submenu': False,
            },

            # ===== SECCIÓN GESTIÓN LOGÍSTICA =====
            {
                'menu_item': 'citas',
                'nombre_mostrado': 'Citas de Proveedores',
                'icono': 'fas fa-calendar-check',
                'url_name': 'logistica:lista_citas',
                'roles': ['Revisión', 'Supervisión', 'Administrador'],
                'orden': 40,
                'es_submenu': False,
            },
            {
                'menu_item': 'traslados',
                'nombre_mostrado': 'Traslados',
                'icono': 'fas fa-truck',
                'url_name': 'logistica:lista_traslados',
                'roles': ['Logística', 'Supervisión', 'Administrador'],
                'orden': 41,
                'es_submenu': False,
            },
            {
                'menu_item': 'conteo_fisico',
                'nombre_mostrado': 'Conteo Físico',
                'icono': 'fas fa-clipboard-check',
                'url_name': 'logistica:buscar_lote_conteo',
                'roles': ['Conteo', 'Supervisión', 'Administrador'],
                'orden': 42,
                'es_submenu': False,
            },
            {
                'menu_item': 'gestion_pedidos',
                'nombre_mostrado': 'Gestión de Pedidos',
                'icono': 'fas fa-shopping-cart',
                'url_name': 'logistica:lista_pedidos',
                'roles': ['Revisión', 'Supervisión', 'Administrador'],
                'orden': 43,
                'es_submenu': False,
            },
            {
                'menu_item': 'reporte_items_no_surtidos',
                'nombre_mostrado': 'Reporte Items No Surtidos',
                'icono': 'fas fa-clipboard-list',
                'url_name': 'pedidos:reporte_items_no_surtidos',
                'roles': ['Supervisión', 'Administrador'],
                'orden': 43,
                'es_submenu': False,
            },
            {
                'menu_item': 'reporte_pedidos_sin_existencia',
                'nombre_mostrado': 'Reporte Pedidos Sin Existencia',
                'icono': 'fas fa-exclamation-triangle',
                'url_name': 'pedidos:reporte_pedidos_sin_existencia',
                'roles': ['Supervisión', 'Administrador'],
                'orden': 43,
                'es_submenu': False,
            },
            {
                'menu_item': 'propuestas_surtimiento',
                'nombre_mostrado': 'Propuestas de Surtimiento',
                'icono': 'fas fa-boxes',
                'url_name': 'logistica:lista_propuestas',
                'roles': ['Almacenero', 'Supervisión', 'Administrador'],
                'orden': 44,
                'es_submenu': False,
            },
            {
                'menu_item': 'llegada_proveedores',
                'nombre_mostrado': 'Llegada de Proveedores',
                'icono': 'fas fa-truck-loading',
                'url_name': 'logistica:llegadas:lista_llegadas',
                'roles': ['Recepción', 'Supervisión', 'Administrador'],
                'orden': 45,
                'es_submenu': False,
            },
            {
                'menu_item': 'entrada_transferencias',
                'nombre_mostrado': 'Entradas por Transferencia',
                'icono': 'fas fa-exchange-alt',
                'url_name': 'logistica:transferencias:lista_transferencias',
                'roles': ['Recepción', 'Supervisión', 'Administrador'],
                'orden': 46,
                'es_submenu': False,
            },
            {
                'menu_item': 'devoluciones',
                'nombre_mostrado': 'Devoluciones de Proveedores',
                'icono': 'fas fa-undo',
                'url_name': 'devoluciones:lista_devoluciones',
                'roles': ['Almacenero', 'Supervisión', 'Administrador'],
                'orden': 47,
                'es_submenu': False,
            },

            # ===== SECCIÓN REPORTES =====
            {
                'menu_item': 'reportes_devoluciones',
                'nombre_mostrado': 'Reportes de Devoluciones',
                'icono': 'fas fa-chart-bar',
                'url_name': 'reportes_devoluciones:reporte_general',
                'roles': ['Supervisión', 'Administrador'],
                'orden': 50,
                'es_submenu': False,
            },
            {
                'menu_item': 'reportes_salidas',
                'nombre_mostrado': 'Reportes de Salidas',
                'icono': 'fas fa-arrow-right',
                'url_name': 'reportes_salidas:reporte_general',
                'roles': ['Supervisión', 'Administrador'],
                'orden': 51,
                'es_submenu': False,
            },

            # ===== SECCIÓN INVENTARIO =====
            {
                'menu_item': 'inventario',
                'nombre_mostrado': 'Inventario',
                'icono': 'fas fa-warehouse',
                'url_name': 'lista_movimientos',
                'roles': ['Gestor de Inventario', 'Supervisión', 'Administrador'],
                'orden': 60,
                'es_submenu': False,
            },
            {
                'menu_item': 'alertas',
                'nombre_mostrado': 'Alertas',
                'icono': 'fas fa-exclamation-triangle',
                'url_name': 'alertas_caducidad',
                'roles': ['Almacenero', 'Supervisión', 'Administrador'],
                'orden': 61,
                'es_submenu': False,
            },

            # ===== SECCIÓN SOLICITUDES =====
            {
                'menu_item': 'solicitudes',
                'nombre_mostrado': 'Solicitudes',
                'icono': 'fas fa-clipboard-list',
                'url_name': 'lista_solicitudes',
                'roles': ['Revisión', 'Supervisión', 'Administrador'],
                'orden': 70,
                'es_submenu': False,
            },

            # ===== SECCIÓN CARGAS MASIVAS =====
            {
                'menu_item': 'cargas_masivas',
                'nombre_mostrado': 'Cargas Masivas',
                'icono': 'fas fa-file-excel',
                'url_name': 'carga_masiva_instituciones',
                'roles': ['Administrador'],
                'orden': 80,
                'es_submenu': False,
            },

            # ===== SECCIÓN PICKING =====
            {
                'menu_item': 'picking',
                'nombre_mostrado': 'Picking y Operaciones',
                'icono': 'fas fa-dolly',
                'url_name': 'picking:dashboard',
                'roles': ['Almacenero', 'Supervisión', 'Administrador'],
                'orden': 90,
                'es_submenu': False,
            },

            # ===== SECCIÓN ADMINISTRACIÓN SISTEMA =====
            {
                'menu_item': 'administracion',
                'nombre_mostrado': 'Panel de Django',
                'icono': 'fas fa-cog',
                'url_name': 'admin:index',
                'roles': ['Administrador'],
                'orden': 100,
                'es_submenu': False,
            },
        ]

        # Actualizar MENU_CHOICES en el modelo si es necesario
        # Cargar la configuración
        self.stdout.write(self.style.SUCCESS('⏳ Cargando configuración del menú...\n'))

        creados = 0
        actualizados = 0

        for config in menu_config:
            # Obtener los roles
            roles = []
            for rol_name in config['roles']:
                try:
                    rol = Group.objects.get(name=rol_name)
                    roles.append(rol)
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Rol "{rol_name}" no encontrado')
                    )

            # Crear o actualizar el item de menú
            menu_item, created = MenuItemRol.objects.update_or_create(
                menu_item=config['menu_item'],
                defaults={
                    'nombre_mostrado': config['nombre_mostrado'],
                    'icono': config['icono'],
                    'url_name': config['url_name'],
                    'orden': config['orden'],
                    'es_submenu': config['es_submenu'],
                }
            )

            # Asignar roles
            menu_item.roles_permitidos.set(roles)

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ "{config["nombre_mostrado"]}" creado')
                )
                creados += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'ℹ️  "{config["nombre_mostrado"]}" actualizado')
                )
                actualizados += 1

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN\n'))
        self.stdout.write(f'  ✅ Items creados: {creados}')
        self.stdout.write(f'  ℹ️  Items actualizados: {actualizados}')
        self.stdout.write(f'  📋 Total de items: {MenuItemRol.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n' + '='*60 + '\n'))
