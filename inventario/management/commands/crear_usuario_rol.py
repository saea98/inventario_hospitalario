"""
Comando de Django para crear usuarios con roles específicos
Uso: python manage.py crear_usuario_rol
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from inventario.models import User


class Command(BaseCommand):
    help = 'Crea usuarios con roles específicos del sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🔐 CREAR USUARIO CON ROL'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # Mostrar roles disponibles
        roles = Group.objects.all().order_by('name')
        if not roles.exists():
            raise CommandError('❌ No hay roles en el sistema. Ejecuta: python manage.py crear_roles')

        self.stdout.write(self.style.SUCCESS('📋 Roles disponibles:\n'))
        roles_list = list(roles)
        for i, rol in enumerate(roles_list, 1):
            self.stdout.write(f'  {i}. {rol.name}')

        # Obtener datos del usuario
        self.stdout.write(self.style.SUCCESS('\n' + '-'*60))
        self.stdout.write(self.style.SUCCESS('📝 DATOS DEL USUARIO\n'))

        username = input('👤 Nombre de usuario: ').strip()

        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            raise CommandError(f'❌ El usuario "{username}" ya existe')

        email = input('📧 Email: ').strip()
        password = input('🔑 Contraseña: ').strip()
        first_name = input('📛 Nombre (opcional): ').strip()
        last_name = input('👨‍👩 Apellido (opcional): ').strip()

        # Seleccionar roles
        self.stdout.write(self.style.SUCCESS('\n' + '-'*60))
        self.stdout.write(self.style.SUCCESS('🎯 SELECCIONAR ROLES\n'))
        self.stdout.write('Ingresa los números de los roles separados por comas (ej: 1,3,5)\n')

        roles_input = input('Roles: ').strip()
        
        try:
            roles_indices = [int(x.strip()) - 1 for x in roles_input.split(',')]
            roles_seleccionados = [roles_list[i] for i in roles_indices if 0 <= i < len(roles_list)]
            
            if not roles_seleccionados:
                raise CommandError('❌ No se seleccionaron roles válidos')
        except (ValueError, IndexError):
            raise CommandError('❌ Entrada inválida. Usa números separados por comas')

        # Crear usuario
        self.stdout.write(self.style.SUCCESS('\n' + '-'*60))
        self.stdout.write(self.style.SUCCESS('⏳ Creando usuario...\n'))

        try:
            usuario = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Asignar roles
            for rol in roles_seleccionados:
                usuario.groups.add(rol)

            self.stdout.write(self.style.SUCCESS('✅ Usuario creado exitosamente!\n'))
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write(self.style.SUCCESS('📊 RESUMEN DEL USUARIO\n'))
            self.stdout.write(f'  👤 Usuario: {usuario.username}')
            self.stdout.write(f'  📧 Email: {usuario.email}')
            self.stdout.write(f'  📛 Nombre: {usuario.first_name} {usuario.last_name}')
            self.stdout.write(f'\n  🎯 Roles asignados:')
            for rol in usuario.groups.all():
                self.stdout.write(f'     • {rol.name}')
            self.stdout.write(self.style.SUCCESS('\n' + '='*60 + '\n'))

        except Exception as e:
            raise CommandError(f'❌ Error al crear usuario: {str(e)}')
