"""
Comando de Django para cargar usuarios de ejemplo con roles
Uso: python manage.py cargar_usuarios_ejemplo
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from inventario.models import User


class Command(BaseCommand):
    help = 'Carga usuarios de ejemplo con roles específicos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('👥 CARGAR USUARIOS DE EJEMPLO'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # Verificar que existan los roles
        roles_requeridos = [
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

        roles_faltantes = []
        for rol_name in roles_requeridos:
            if not Group.objects.filter(name=rol_name).exists():
                roles_faltantes.append(rol_name)

        if roles_faltantes:
            raise CommandError(
                f'❌ Faltan los siguientes roles: {", ".join(roles_faltantes)}\n'
                f'Ejecuta primero: python manage.py crear_roles'
            )

        # Definir usuarios de ejemplo
        usuarios_ejemplo = [
            {
                'username': 'revision1',
                'email': 'revision@almacen.local',
                'password': 'revision123',
                'first_name': 'María',
                'last_name': 'García',
                'roles': ['Revisión']
            },
            {
                'username': 'almacenero1',
                'email': 'almacenero1@almacen.local',
                'password': 'almacen123',
                'first_name': 'Juan',
                'last_name': 'López',
                'roles': ['Almacenero']
            },
            {
                'username': 'almacenero2',
                'email': 'almacenero2@almacen.local',
                'password': 'almacen123',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'roles': ['Almacenero']
            },
            {
                'username': 'calidad1',
                'email': 'calidad@almacen.local',
                'password': 'calidad123',
                'first_name': 'Ana',
                'last_name': 'Martínez',
                'roles': ['Control Calidad']
            },
            {
                'username': 'facturacion1',
                'email': 'facturacion@almacen.local',
                'password': 'factura123',
                'first_name': 'Pedro',
                'last_name': 'Sánchez',
                'roles': ['Facturación']
            },
            {
                'username': 'supervision1',
                'email': 'supervision@almacen.local',
                'password': 'supervision123',
                'first_name': 'Roberto',
                'last_name': 'Díaz',
                'roles': ['Supervisión']
            },
            {
                'username': 'logistica1',
                'email': 'logistica@almacen.local',
                'password': 'logistica123',
                'first_name': 'Fernando',
                'last_name': 'Gómez',
                'roles': ['Logística']
            },
            {
                'username': 'recepcion1',
                'email': 'recepcion@almacen.local',
                'password': 'recepcion123',
                'first_name': 'Sofía',
                'last_name': 'Flores',
                'roles': ['Recepción']
            },
            {
                'username': 'conteo1',
                'email': 'conteo@almacen.local',
                'password': 'conteo123',
                'first_name': 'Luis',
                'last_name': 'Vargas',
                'roles': ['Conteo']
            },
            {
                'username': 'gestor1',
                'email': 'gestor@almacen.local',
                'password': 'gestor123',
                'first_name': 'Patricia',
                'last_name': 'Ruiz',
                'roles': ['Gestor de Inventario']
            },
        ]

        creados = 0
        existentes = 0

        self.stdout.write(self.style.SUCCESS('⏳ Creando usuarios de ejemplo...\n'))

        for usuario_data in usuarios_ejemplo:
            username = usuario_data['username']

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'ℹ️  Usuario "{username}" ya existe')
                )
                existentes += 1
                continue

            try:
                usuario = User.objects.create_user(
                    username=username,
                    email=usuario_data['email'],
                    password=usuario_data['password'],
                    first_name=usuario_data['first_name'],
                    last_name=usuario_data['last_name']
                )

                # Asignar roles
                for rol_name in usuario_data['roles']:
                    rol = Group.objects.get(name=rol_name)
                    usuario.groups.add(rol)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Usuario "{username}" creado con rol: {", ".join(usuario_data["roles"])}'
                    )
                )
                creados += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error al crear "{username}": {str(e)}')
                )

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN\n'))
        self.stdout.write(f'  ✅ Usuarios creados: {creados}')
        self.stdout.write(f'  ℹ️  Usuarios existentes: {existentes}')
        self.stdout.write(f'  👥 Total de usuarios: {User.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))

        # Mostrar tabla de usuarios
        self.stdout.write(self.style.SUCCESS('\n📋 USUARIOS DEL SISTEMA\n'))
        self.stdout.write(f'{"Usuario":<20} {"Email":<30} {"Roles":<40}')
        self.stdout.write('-'*90)

        for usuario in User.objects.all().order_by('username'):
            roles = ', '.join([g.name for g in usuario.groups.all()])
            if not roles:
                roles = '(Sin roles)'
            self.stdout.write(f'{usuario.username:<20} {usuario.email:<30} {roles:<40}')

        self.stdout.write('\n' + '='*60 + '\n')

        # Mostrar credenciales
        self.stdout.write(self.style.WARNING('🔑 CREDENCIALES DE ACCESO\n'))
        self.stdout.write('Usuario: admin')
        self.stdout.write('Contraseña: (la que configuraste)\n')

        for usuario_data in usuarios_ejemplo:
            if not User.objects.filter(username=usuario_data['username']).exists():
                continue
            self.stdout.write(f'Usuario: {usuario_data["username"]}')
            self.stdout.write(f'Contraseña: {usuario_data["password"]}\n')

        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
