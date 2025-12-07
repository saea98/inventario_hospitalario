"""
Comando Django para crear grupos de usuarios y asignar permisos
para los módulos de ENTRADA AL ALMACÉN y PROVEEDURÍA

Uso: python manage.py crear_grupos_permisos
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from inventario.models import Lote, MovimientoInventario


class Command(BaseCommand):
    help = 'Crea grupos de usuarios y asigna permisos para el sistema de inventario'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando grupos y permisos...'))
        
        # Obtener los tipos de contenido
        lote_ct = ContentType.objects.get_for_model(Lote)
        movimiento_ct = ContentType.objects.get_for_model(MovimientoInventario)
        
        # Obtener los permisos
        perms = {
            'add_lote': Permission.objects.get(content_type=lote_ct, codename='add_lote'),
            'change_lote': Permission.objects.get(content_type=lote_ct, codename='change_lote'),
            'view_lote': Permission.objects.get(content_type=lote_ct, codename='view_lote'),
            'delete_lote': Permission.objects.get(content_type=lote_ct, codename='delete_lote'),
            'add_movimiento': Permission.objects.get(content_type=movimiento_ct, codename='add_movimientoinventario'),
            'change_movimiento': Permission.objects.get(content_type=movimiento_ct, codename='change_movimientoinventario'),
            'view_movimiento': Permission.objects.get(content_type=movimiento_ct, codename='view_movimientoinventario'),
            'delete_movimiento': Permission.objects.get(content_type=movimiento_ct, codename='delete_movimientoinventario'),
        }
        
        # ============================================================
        # GRUPO 1: ALMACENERO
        # ============================================================
        almacenero_group, created = Group.objects.get_or_create(name='almacenero')
        almacenero_group.permissions.set([
            perms['add_lote'],
            perms['view_lote'],
            perms['add_movimiento'],
            perms['view_movimiento'],
        ])
        
        status = "creado" if created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(f"✓ Grupo 'almacenero' {status}")
        )
        self.stdout.write("  Permisos: add_lote, view_lote, add_movimiento, view_movimiento")
        
        # ============================================================
        # GRUPO 2: RESPONSABLE DE PROVEEDURÍA
        # ============================================================
        proveeduria_group, created = Group.objects.get_or_create(name='responsable_proveeduria')
        proveeduria_group.permissions.set([
            perms['view_lote'],
            perms['change_lote'],
            perms['add_movimiento'],
            perms['view_movimiento'],
        ])
        
        status = "creado" if created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(f"✓ Grupo 'responsable_proveeduria' {status}")
        )
        self.stdout.write("  Permisos: view_lote, change_lote, add_movimiento, view_movimiento")
        
        # ============================================================
        # GRUPO 3: VALIDADOR
        # ============================================================
        validador_group, created = Group.objects.get_or_create(name='validador')
        validador_group.permissions.set([
            perms['view_lote'],
            perms['change_lote'],
            perms['view_movimiento'],
            perms['change_movimiento'],
        ])
        
        status = "creado" if created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(f"✓ Grupo 'validador' {status}")
        )
        self.stdout.write("  Permisos: view_lote, change_lote, view_movimiento, change_movimiento")
        
        # ============================================================
        # GRUPO 4: ADMINISTRADOR
        # ============================================================
        admin_group, created = Group.objects.get_or_create(name='administrador')
        admin_group.permissions.set([
            perms['add_lote'],
            perms['change_lote'],
            perms['view_lote'],
            perms['delete_lote'],
            perms['add_movimiento'],
            perms['change_movimiento'],
            perms['view_movimiento'],
            perms['delete_movimiento'],
        ])
        
        status = "creado" if created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(f"✓ Grupo 'administrador' {status}")
        )
        self.stdout.write("  Permisos: Todos")
        
        # ============================================================
        # RESUMEN
        # ============================================================
        self.stdout.write(self.style.SUCCESS('\n✓ Grupos y permisos configurados correctamente\n'))
        
        self.stdout.write(self.style.WARNING('RESUMEN DE ROLES:\n'))
        
        roles_info = [
            {
                'nombre': 'ALMACENERO',
                'descripcion': 'Puede crear entradas al almacén y ver lotes',
                'permisos': ['add_lote', 'view_lote', 'add_movimiento', 'view_movimiento']
            },
            {
                'nombre': 'RESPONSABLE DE PROVEEDURÍA',
                'descripcion': 'Puede crear salidas de inventario y modificar lotes',
                'permisos': ['view_lote', 'change_lote', 'add_movimiento', 'view_movimiento']
            },
            {
                'nombre': 'VALIDADOR',
                'descripcion': 'Puede validar y aprobar operaciones de inventario',
                'permisos': ['view_lote', 'change_lote', 'view_movimiento', 'change_movimiento']
            },
            {
                'nombre': 'ADMINISTRADOR',
                'descripcion': 'Acceso total al sistema',
                'permisos': ['Todos']
            }
        ]
        
        for rol in roles_info:
            self.stdout.write(f"\n{rol['nombre']}")
            self.stdout.write(f"  {rol['descripcion']}")
            self.stdout.write(f"  Permisos: {', '.join(rol['permisos'])}")
        
        self.stdout.write(self.style.WARNING('\nPARA ASIGNAR ROLES A USUARIOS:\n'))
        self.stdout.write('1. Accede a Django Admin (/admin/)')
        self.stdout.write('2. Ve a Usuarios')
        self.stdout.write('3. Selecciona un usuario')
        self.stdout.write('4. En la sección "Grupos", selecciona el rol deseado')
        self.stdout.write('5. Guarda los cambios\n')
