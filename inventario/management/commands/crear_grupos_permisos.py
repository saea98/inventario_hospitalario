"""
Comando de management para crear grupos y permisos de forma dinámica
Ubicación: ./inventario/inventario_hospitalario/inventario/management/commands/crear_grupos_permisos.py

Uso:
    python manage.py crear_grupos_permisos
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from inventario.models import Lote, MovimientoInventario

class Command(BaseCommand):
    help = 'Crea grupos y permisos para el sistema de inventario'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando creación de grupos y permisos...'))
        
        # Obtener los content types
        lote_ct = ContentType.objects.get_for_model(Lote)
        movimiento_ct = ContentType.objects.get_for_model(MovimientoInventario)
        
        # Definir permisos personalizados si no existen
        # (Estos se crean automáticamente con las migraciones)
        
        # ============================================================
        # GRUPO: ALMACENERO
        # ============================================================
        almacenero_group, created = Group.objects.get_or_create(name='Almacenero')
        
        almacenero_permisos = [
            # Lotes - Puede crear y ver
            'add_lote',
            'view_lote',
            'change_lote',  # Para actualizar cantidad disponible
            
            # Movimientos - Puede crear y ver
            'add_movimientoinventario',
            'view_movimientoinventario',
        ]
        
        almacenero_group.permissions.clear()
        for perm_codename in almacenero_permisos:
            try:
                # Intentar obtener del modelo Lote
                perm = Permission.objects.get(
                    content_type=lote_ct,
                    codename=perm_codename
                )
                almacenero_group.permissions.add(perm)
            except Permission.DoesNotExist:
                try:
                    # Intentar obtener del modelo MovimientoInventario
                    perm = Permission.objects.get(
                        content_type=movimiento_ct,
                        codename=perm_codename
                    )
                    almacenero_group.permissions.add(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permiso {perm_codename} no encontrado')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Grupo "Almacenero" creado/actualizado con {almacenero_group.permissions.count()} permisos')
        )
        
        # ============================================================
        # GRUPO: RESPONSABLE PROVEEDURÍA
        # ============================================================
        proveeduria_group, created = Group.objects.get_or_create(name='Responsable Proveeduría')
        
        proveeduria_permisos = [
            # Lotes - Puede ver y cambiar (para actualizar cantidad)
            'view_lote',
            'change_lote',
            
            # Movimientos - Puede crear y ver
            'add_movimientoinventario',
            'view_movimientoinventario',
        ]
        
        proveeduria_group.permissions.clear()
        for perm_codename in proveeduria_permisos:
            try:
                perm = Permission.objects.get(
                    content_type=lote_ct,
                    codename=perm_codename
                )
                proveeduria_group.permissions.add(perm)
            except Permission.DoesNotExist:
                try:
                    perm = Permission.objects.get(
                        content_type=movimiento_ct,
                        codename=perm_codename
                    )
                    proveeduria_group.permissions.add(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permiso {perm_codename} no encontrado')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Grupo "Responsable Proveeduría" creado/actualizado con {proveeduria_group.permissions.count()} permisos')
        )
        
        # ============================================================
        # GRUPO: ADMINISTRADOR
        # ============================================================
        admin_group, created = Group.objects.get_or_create(name='Administrador')
        
        # El administrador tiene TODOS los permisos
        all_permisos = Permission.objects.filter(
            content_type__in=[lote_ct, movimiento_ct]
        )
        
        admin_group.permissions.set(all_permisos)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Grupo "Administrador" creado/actualizado con {admin_group.permissions.count()} permisos')
        )
        
        # ============================================================
        # RESUMEN
        # ============================================================
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('RESUMEN DE GRUPOS Y PERMISOS'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        for group in Group.objects.all().order_by('name'):
            permisos = group.permissions.all()
            self.stdout.write(f'\n📌 {group.name}:')
            for perm in permisos:
                self.stdout.write(f'   ✓ {perm.content_type.model}.{perm.codename}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✓ Grupos y permisos creados correctamente'))
        self.stdout.write(self.style.SUCCESS('='*60))
