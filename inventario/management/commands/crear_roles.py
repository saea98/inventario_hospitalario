"""
Comando de Django para crear los roles del sistema
Uso: python manage.py crear_roles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Crea los roles (grupos) necesarios para el sistema de inventario'

    def handle(self, *args, **options):
        roles = [
            {
                'name': 'Revisión',
                'description': 'Responsable de revisar y autorizar citas y pedidos'
            },
            {
                'name': 'Almacenero',
                'description': 'Responsable de recepción, almacenamiento y picking'
            },
            {
                'name': 'Control Calidad',
                'description': 'Responsable de inspeccionar productos'
            },
            {
                'name': 'Facturación',
                'description': 'Responsable de registrar facturas'
            },
            {
                'name': 'Supervisión',
                'description': 'Responsable de supervisar y validar operaciones'
            },
            {
                'name': 'Logística',
                'description': 'Responsable de asignación de logística y traslados'
            },
            {
                'name': 'Recepción',
                'description': 'Responsable de recepción en destino de traslados'
            },
            {
                'name': 'Conteo',
                'description': 'Responsable de realizar conteos físicos'
            },
            {
                'name': 'Gestor de Inventario',
                'description': 'Responsable de gestión general del inventario'
            },
            {
                'name': 'Administrador',
                'description': 'Administrador del sistema'
            },
        ]

        self.stdout.write(self.style.SUCCESS('🔄 Creando roles del sistema...\n'))

        for role_data in roles:
            group, created = Group.objects.get_or_create(name=role_data['name'])
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Rol "{role_data["name"]}" creado exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'ℹ️  Rol "{role_data["name"]}" ya existe')
                )

        # Mostrar resumen
        total_grupos = Group.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n✨ Total de roles en el sistema: {total_grupos}'))
        
        self.stdout.write(self.style.SUCCESS('\n📋 Roles disponibles:'))
        for grupo in Group.objects.all().order_by('name'):
            self.stdout.write(f'  • {grupo.name}')
