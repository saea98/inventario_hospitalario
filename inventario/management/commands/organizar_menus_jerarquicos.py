"""
Comando para organizar los menús en una estructura jerárquica
Agrupa items relacionados bajo menús padres
"""

from django.core.management.base import BaseCommand
from inventario.models import MenuItemRol


class Command(BaseCommand):
    help = 'Organiza los menús en una estructura jerárquica con submenús'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar cambios sin aplicarlos'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('ORGANIZACIÓN DE MENÚS JERÁRQUICOS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # Definir la estructura jerárquica
        estructura = {
            # Menú padre: [items hijos]
            'Administración': [
                'lista_usuarios',
                'editar_usuario',
                'asignar_rol_ajax',
                'lista_roles',
                'detalle_rol',
                'lista_opciones_menu',
                'editar_opcion_menu',
                'reporte_acceso',
            ],
            'Gestión de Inventario': [
                'lista_instituciones',
                'lista_productos',
                'lista_lotes',
                'lista_movimientos',
                'alertas_caducidad',
            ],
            'Entrada y Salida': [
                'entrada_almacen_paso1',
                'proveeduria_paso1',
            ],
            'Conteo Físico': [
                'buscar_lote_conteo',
                'historial_conteos',
            ],
            'Reportes': [
                'reporte_general',
                'analisis_distribuciones',
                'analisis_temporal',
                'estadisticas',
            ],
            'Picking': [
                'picking_propuesta',
            ],
        }

        cambios = 0

        for menu_padre_nombre, items_hijos in estructura.items():
            self.stdout.write(f'\nProcesando "{menu_padre_nombre}"...')
            
            # Crear o obtener el menú padre
            menu_padre, creado = MenuItemRol.objects.get_or_create(
                url_name=menu_padre_nombre.lower().replace(' ', '_'),
                defaults={
                    'nombre_mostrado': menu_padre_nombre,
                    'menu_item': menu_padre_nombre.lower().replace(' ', '_'),
                    'icono': 'fas fa-folder',
                    'orden': 0,
                    'activo': True,
                    'menu_padre': None,
                }
            )
            
            if creado:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Menú padre creado: {menu_padre_nombre}'))
                cambios += 1
            else:
                self.stdout.write(f'  ℹ️  Menú padre existente: {menu_padre_nombre}')
            
            # Asignar items hijos
            for item_url_name in items_hijos:
                try:
                    item = MenuItemRol.objects.get(url_name=item_url_name)
                    
                    if item.menu_padre != menu_padre:
                        if not dry_run:
                            item.menu_padre = menu_padre
                            item.save()
                            self.stdout.write(
                                self.style.SUCCESS(f'    ✅ {item.nombre_mostrado} → {menu_padre_nombre}')
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'    → {item.nombre_mostrado} → {menu_padre_nombre}')
                            )
                        cambios += 1
                    else:
                        self.stdout.write(f'    ℹ️  {item.nombre_mostrado} ya está asignado')
                
                except MenuItemRol.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'    ❌ Item no encontrado: {item_url_name}')
                    )

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Los cambios NO fueron aplicados\n'))
        
        self.stdout.write(f"Cambios realizados: {cambios}")
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ Organización completada'))
            self.stdout.write(self.style.SUCCESS('\nAhora puedes:'))
            self.stdout.write('1. Ir a Django Admin → Inventario → Menu Item Rol')
            self.stdout.write('2. Editar los menús padres para personalizar iconos y orden')
            self.stdout.write('3. Los submenús aparecerán automáticamente en el navegador')
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  Ejecuta sin --dry-run para aplicar cambios'))
        
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
