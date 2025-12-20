"""
Comando de Django para gestionar roles del sistema
Uso: python manage.py gestionar_roles [opción] [argumentos]
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, User


class Command(BaseCommand):
    help = 'Gestiona los roles (grupos) del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            'accion',
            type=str,
            choices=['listar', 'crear', 'asignar', 'remover', 'ver-usuario', 'eliminar'],
            help='Acción a realizar'
        )
        parser.add_argument(
            '--rol',
            type=str,
            help='Nombre del rol'
        )
        parser.add_argument(
            '--usuario',
            type=str,
            help='Nombre de usuario'
        )

    def handle(self, *args, **options):
        accion = options['accion']

        if accion == 'listar':
            self.listar_roles()
        elif accion == 'crear':
            self.crear_roles()
        elif accion == 'asignar':
            self.asignar_rol(options)
        elif accion == 'remover':
            self.remover_rol(options)
        elif accion == 'ver-usuario':
            self.ver_usuario(options)
        elif accion == 'eliminar':
            self.eliminar_rol(options)

    def listar_roles(self):
        """Lista todos los roles disponibles"""
        grupos = Group.objects.all().order_by('name')
        
        if not grupos.exists():
            self.stdout.write(self.style.WARNING('⚠️  No hay roles en el sistema'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n📋 Roles disponibles en el sistema:\n'))
        for i, grupo in enumerate(grupos, 1):
            # Contar usuarios con este rol
            usuarios_count = grupo.user_set.count()
            self.stdout.write(
                f'  {i}. {grupo.name:<30} ({usuarios_count} usuario{"s" if usuarios_count != 1 else ""})'
            )
        
        self.stdout.write(self.style.SUCCESS(f'\n✨ Total de roles: {grupos.count()}\n'))

    def crear_roles(self):
        """Crea todos los roles del sistema"""
        roles = [
            'Revisión',
            'Almacenero',
            'Control Calidad',
            'Facturación',
            'Supervisión',
            'Logística',
            'Recepción',
            'Conteo',
            'Gestor de Inventario',
            'Administrador',
        ]

        self.stdout.write(self.style.SUCCESS('\n🔄 Creando roles del sistema...\n'))

        creados = 0
        existentes = 0

        for rol_name in roles:
            group, created = Group.objects.get_or_create(name=rol_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Rol "{rol_name}" creado exitosamente')
                )
                creados += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'ℹ️  Rol "{rol_name}" ya existe')
                )
                existentes += 1

        self.stdout.write(self.style.SUCCESS(f'\n✨ Resumen:'))
        self.stdout.write(f'  • Roles creados: {creados}')
        self.stdout.write(f'  • Roles existentes: {existentes}')
        self.stdout.write(f'  • Total en el sistema: {Group.objects.count()}\n')

    def asignar_rol(self, options):
        """Asigna un rol a un usuario"""
        if not options['rol'] or not options['usuario']:
            raise CommandError('Debes especificar --rol y --usuario')

        try:
            usuario = User.objects.get(username=options['usuario'])
            grupo = Group.objects.get(name=options['rol'])
            
            usuario.groups.add(grupo)
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Rol "{options["rol"]}" asignado a usuario "{options["usuario"]}"\n'
            ))
            
            # Mostrar roles del usuario
            self.stdout.write(self.style.SUCCESS(f'📋 Roles de {options["usuario"]}:'))
            for rol in usuario.groups.all():
                self.stdout.write(f'  • {rol.name}')
            self.stdout.write('')
            
        except User.DoesNotExist:
            raise CommandError(f'❌ Usuario "{options["usuario"]}" no encontrado')
        except Group.DoesNotExist:
            raise CommandError(f'❌ Rol "{options["rol"]}" no encontrado')

    def remover_rol(self, options):
        """Remueve un rol de un usuario"""
        if not options['rol'] or not options['usuario']:
            raise CommandError('Debes especificar --rol y --usuario')

        try:
            usuario = User.objects.get(username=options['usuario'])
            grupo = Group.objects.get(name=options['rol'])
            
            usuario.groups.remove(grupo)
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Rol "{options["rol"]}" removido de usuario "{options["usuario"]}"\n'
            ))
            
            # Mostrar roles del usuario
            self.stdout.write(self.style.SUCCESS(f'📋 Roles de {options["usuario"]}:'))
            for rol in usuario.groups.all():
                self.stdout.write(f'  • {rol.name}')
            if not usuario.groups.exists():
                self.stdout.write('  (Sin roles asignados)')
            self.stdout.write('')
            
        except User.DoesNotExist:
            raise CommandError(f'❌ Usuario "{options["usuario"]}" no encontrado')
        except Group.DoesNotExist:
            raise CommandError(f'❌ Rol "{options["rol"]}" no encontrado')

    def ver_usuario(self, options):
        """Muestra los roles de un usuario"""
        if not options['usuario']:
            raise CommandError('Debes especificar --usuario')

        try:
            usuario = User.objects.get(username=options['usuario'])
            
            self.stdout.write(self.style.SUCCESS(f'\n👤 Información del usuario "{options["usuario"]}"\n'))
            self.stdout.write(f'  Email: {usuario.email}')
            self.stdout.write(f'  Nombre: {usuario.first_name} {usuario.last_name}')
            self.stdout.write(f'  Activo: {"Sí" if usuario.is_active else "No"}')
            self.stdout.write(f'  Staff: {"Sí" if usuario.is_staff else "No"}')
            self.stdout.write(f'  Superusuario: {"Sí" if usuario.is_superuser else "No"}')
            
            self.stdout.write(self.style.SUCCESS(f'\n📋 Roles asignados:'))
            roles = usuario.groups.all()
            if roles.exists():
                for rol in roles:
                    self.stdout.write(f'  • {rol.name}')
            else:
                self.stdout.write('  (Sin roles asignados)')
            
            self.stdout.write(self.style.SUCCESS(f'\n🔐 Permisos:'))
            permisos = usuario.get_all_permissions()
            if permisos:
                for permiso in permisos:
                    self.stdout.write(f'  • {permiso}')
            else:
                self.stdout.write('  (Sin permisos asignados)')
            
            self.stdout.write('')
            
        except User.DoesNotExist:
            raise CommandError(f'❌ Usuario "{options["usuario"]}" no encontrado')

    def eliminar_rol(self, options):
        """Elimina un rol del sistema"""
        if not options['rol']:
            raise CommandError('Debes especificar --rol')

        try:
            grupo = Group.objects.get(name=options['rol'])
            usuarios_count = grupo.user_set.count()
            
            if usuarios_count > 0:
                self.stdout.write(self.style.WARNING(
                    f'\n⚠️  El rol "{options["rol"]}" está asignado a {usuarios_count} usuario{"s" if usuarios_count != 1 else ""}'
                ))
            
            grupo.delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Rol "{options["rol"]}" eliminado del sistema\n'
            ))
            
        except Group.DoesNotExist:
            raise CommandError(f'❌ Rol "{options["rol"]}" no encontrado')
