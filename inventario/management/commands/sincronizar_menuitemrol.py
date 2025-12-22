"""
Comando para sincronizar MenuItemRol con los decoradores de las vistas
Actualiza los roles permitidos en MenuItemRol según los decoradores
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from inventario.models import MenuItemRol


class Command(BaseCommand):
    help = 'Sincroniza MenuItemRol con los decoradores de las vistas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar cambios sin aplicarlos'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('SINCRONIZACIÓN DE MenuItemRol'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        cambios = []

        # 1. Corregir dashboard - Solo Administrador
        self.stdout.write('Procesando dashboard...')
        try:
            dashboard = MenuItemRol.objects.get(url_name='dashboard')
            roles_actuales = set(dashboard.roles_permitidos.values_list('name', flat=True))
            roles_esperados = {'Administrador'}
            
            if roles_actuales != roles_esperados:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Cambio: {roles_actuales} → {roles_esperados}"
                    )
                )
                cambios.append({
                    'url_name': 'dashboard',
                    'nombre': dashboard.nombre_mostrado,
                    'antes': roles_actuales,
                    'despues': roles_esperados
                })
                
                if not dry_run:
                    dashboard.roles_permitidos.clear()
                    admin_group = Group.objects.get(name='Administrador')
                    dashboard.roles_permitidos.add(admin_group)
                    self.stdout.write(self.style.SUCCESS('  ✅ Actualizado'))
            else:
                self.stdout.write(self.style.SUCCESS('  ✅ Ya está correcto'))
        except MenuItemRol.DoesNotExist:
            self.stdout.write(self.style.ERROR('  ❌ No encontrado en MenuItemRol'))

        # 2. Corregir entrada_almacen_paso1 - Agregar Control Calidad
        self.stdout.write('\nProcesando entrada_almacen_paso1...')
        try:
            entrada = MenuItemRol.objects.get(url_name='entrada_almacen_paso1')
            roles_actuales = set(entrada.roles_permitidos.values_list('name', flat=True))
            roles_esperados = {'Administrador', 'Supervisión', 'Almacenero', 'Control Calidad'}
            
            if roles_actuales != roles_esperados:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Cambio: {roles_actuales} → {roles_esperados}"
                    )
                )
                cambios.append({
                    'url_name': 'entrada_almacen_paso1',
                    'nombre': entrada.nombre_mostrado,
                    'antes': roles_actuales,
                    'despues': roles_esperados
                })
                
                if not dry_run:
                    entrada.roles_permitidos.clear()
                    for rol_name in roles_esperados:
                        try:
                            group = Group.objects.get(name=rol_name)
                            entrada.roles_permitidos.add(group)
                        except Group.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f"    ⚠️  Rol '{rol_name}' no existe")
                            )
                    self.stdout.write(self.style.SUCCESS('  ✅ Actualizado'))
            else:
                self.stdout.write(self.style.SUCCESS('  ✅ Ya está correcto'))
        except MenuItemRol.DoesNotExist:
            self.stdout.write(self.style.ERROR('  ❌ No encontrado en MenuItemRol'))

        # 3. Agregar vistas faltantes a MenuItemRol
        self.stdout.write('\nAgregando vistas faltantes a MenuItemRol...\n')
        
        vistas_faltantes = {
            'lista_usuarios': {
                'nombre': 'Usuarios',
                'roles': ['Administrador'],
                'icono': 'fas fa-users',
                'orden': 100
            },
            'editar_usuario': {
                'nombre': 'Editar Usuario',
                'roles': ['Administrador'],
                'icono': 'fas fa-user-edit',
                'orden': 101
            },
            'asignar_rol_ajax': {
                'nombre': 'Asignar Rol',
                'roles': ['Administrador'],
                'icono': 'fas fa-user-shield',
                'orden': 102
            },
            'lista_roles': {
                'nombre': 'Roles',
                'roles': ['Administrador'],
                'icono': 'fas fa-shield-alt',
                'orden': 103
            },
            'detalle_rol': {
                'nombre': 'Detalle de Rol',
                'roles': ['Administrador'],
                'icono': 'fas fa-shield-alt',
                'orden': 104
            },
            'lista_opciones_menu': {
                'nombre': 'Opciones de Menú',
                'roles': ['Administrador'],
                'icono': 'fas fa-bars',
                'orden': 105
            },
            'editar_opcion_menu': {
                'nombre': 'Editar Opción de Menú',
                'roles': ['Administrador'],
                'icono': 'fas fa-bars',
                'orden': 106
            },
            'reporte_acceso': {
                'nombre': 'Reporte de Acceso',
                'roles': ['Administrador'],
                'icono': 'fas fa-chart-bar',
                'orden': 107
            },
            'estadisticas': {
                'nombre': 'Estadísticas',
                'roles': ['Administrador'],
                'icono': 'fas fa-chart-pie',
                'orden': 108
            },
            'buscar_lote_conteo': {
                'nombre': 'Buscar Lote Conteo',
                'roles': ['Administrador', 'Supervisión', 'Almacenero', 'Gestor de Inventario'],
                'icono': 'fas fa-search',
                'orden': 109
            },
            'historial_conteos': {
                'nombre': 'Historial de Conteos',
                'roles': ['Administrador', 'Supervisión', 'Almacenero', 'Gestor de Inventario'],
                'icono': 'fas fa-history',
                'orden': 110
            },
            'reporte_general': {
                'nombre': 'Reporte General',
                'roles': ['Administrador', 'Analista', 'Gestor de Inventario'],
                'icono': 'fas fa-file-alt',
                'orden': 111
            },
            'analisis_distribuciones': {
                'nombre': 'Análisis de Distribuciones',
                'roles': ['Administrador', 'Analista', 'Gestor de Inventario'],
                'icono': 'fas fa-chart-line',
                'orden': 112
            },
            'analisis_temporal': {
                'nombre': 'Análisis Temporal',
                'roles': ['Administrador', 'Analista', 'Gestor de Inventario'],
                'icono': 'fas fa-calendar-alt',
                'orden': 113
            },
            'picking_propuesta': {
                'nombre': 'Propuesta de Picking',
                'roles': ['Administrador', 'Almacenista', 'Gestor de Inventario'],
                'icono': 'fas fa-boxes',
                'orden': 114
            },
        }

        for url_name, config in vistas_faltantes.items():
            try:
                menu_item = MenuItemRol.objects.get(url_name=url_name)
                self.stdout.write(f"  ✅ {url_name}: Ya existe")
            except MenuItemRol.DoesNotExist:
                self.stdout.write(f"  ➕ {url_name}: Creando...")
                
                if not dry_run:
                    try:
                        menu_item = MenuItemRol.objects.create(
                            menu_item=url_name,
                            nombre_mostrado=config['nombre'],
                            url_name=url_name,
                            icono=config['icono'],
                            orden=config['orden'],
                            activo=True,
                            es_submenu=False
                        )
                        
                        # Agregar roles
                        for rol_name in config['roles']:
                            try:
                                group = Group.objects.get(name=rol_name)
                                menu_item.roles_permitidos.add(group)
                            except Group.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f"    ⚠️  Rol '{rol_name}' no existe")
                                )
                        
                        self.stdout.write(self.style.SUCCESS(f"    ✅ Creado"))
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"    ❌ Error: {str(e)}")
                        )

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Los cambios NO fueron aplicados\n'))
        
        self.stdout.write(f"Cambios a realizar: {len(cambios)}")
        self.stdout.write(f"Vistas a crear: {len(vistas_faltantes)}")
        
        if cambios:
            self.stdout.write(self.style.WARNING('\nCambios:'))
            for cambio in cambios:
                self.stdout.write(
                    f"  • {cambio['url_name']} ({cambio['nombre']})\n"
                    f"    {cambio['antes']} → {cambio['despues']}"
                )
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ Sincronización completada'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Ejecuta sin --dry-run para aplicar cambios'))
        
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
