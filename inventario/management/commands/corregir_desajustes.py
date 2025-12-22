"""
Comando para corregir los desajustes específicos encontrados
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from inventario.models import MenuItemRol


class Command(BaseCommand):
    help = 'Corrige los desajustes específicos en MenuItemRol'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar cambios sin aplicarlos'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('CORRECCIÓN DE DESAJUSTES'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # Desajustes a corregir
        correcciones = {
            'entrada_almacen_paso1': {
                'nombre': 'Entrada al Almacén',
                'roles': ['Control Calidad', 'Almacenero', 'Supervisión']
            },
            'reporte_general': {
                'nombre': 'Reporte General',
                'roles': ['Analista', 'Gestor de Inventario', 'Administrador']
            },
            'analisis_distribuciones': {
                'nombre': 'Análisis de Distribuciones',
                'roles': ['Analista', 'Gestor de Inventario', 'Administrador']
            },
            'analisis_temporal': {
                'nombre': 'Análisis Temporal',
                'roles': ['Analista', 'Gestor de Inventario', 'Administrador']
            },
            'dashboard': {
                'nombre': 'Dashboard',
                'roles': ['Almacenista', 'Gestor de Inventario', 'Administrador']
            },
            'picking_propuesta': {
                'nombre': 'Propuesta de Picking',
                'roles': ['Almacenista', 'Gestor de Inventario', 'Administrador']
            },
        }

        cambios_realizados = 0

        for url_name, config in correcciones.items():
            self.stdout.write(f'Procesando {url_name}...')
            
            try:
                menu_item = MenuItemRol.objects.get(url_name=url_name)
                roles_actuales = set(menu_item.roles_permitidos.values_list('name', flat=True))
                roles_esperados = set(config['roles'])
                
                if roles_actuales != roles_esperados:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Cambio: {roles_actuales} → {roles_esperados}"
                        )
                    )
                    
                    if not dry_run:
                        menu_item.roles_permitidos.clear()
                        
                        for rol_name in roles_esperados:
                            try:
                                group = Group.objects.get(name=rol_name)
                                menu_item.roles_permitidos.add(group)
                            except Group.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f"    ⚠️  Rol '{rol_name}' no existe")
                                )
                        
                        self.stdout.write(self.style.SUCCESS('  ✅ Actualizado'))
                        cambios_realizados += 1
                else:
                    self.stdout.write(self.style.SUCCESS('  ✅ Ya está correcto'))
            
            except MenuItemRol.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ❌ No encontrado en MenuItemRol'))

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Los cambios NO fueron aplicados\n'))
        
        self.stdout.write(f"Cambios realizados: {cambios_realizados}")
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ Corrección completada'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Ejecuta sin --dry-run para aplicar cambios'))
        
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
