"""
Comando para probar automáticamente el acceso de cada rol a las vistas del sistema.

Uso:
    python manage.py test_roles_acceso
    python manage.py test_roles_acceso --verbose
    python manage.py test_roles_acceso --rol Almacenero
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.test import Client
from django.urls import reverse


class Command(BaseCommand):
    help = 'Prueba automáticamente el acceso de cada rol a las vistas del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rol',
            type=str,
            help='Probar solo un rol específico'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada'
        )
        parser.add_argument(
            '--crear-usuarios',
            action='store_true',
            help='Crear usuarios de prueba para cada rol'
        )

    def handle(self, *args, **options):
        """Ejecutar las pruebas de acceso"""
        
        verbose = options.get('verbose', False)
        rol_filtro = options.get('rol')
        crear_usuarios = options.get('crear_usuarios', False)
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('PRUEBA DE ACCESO POR ROLES'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))
        
        # Definir las vistas a probar
        vistas_a_probar = {
            'Dashboard': {
                'url': 'dashboard',
                'roles_permitidos': ['Todos'],
                'descripcion': 'Panel principal del sistema'
            },
            'Picking Dashboard': {
                'url': 'logistica:dashboard_picking',
                'roles_permitidos': ['Administrador', 'Almacenista', 'Gestor de Inventario'],
                'descripcion': 'Dashboard de picking'
            },
            'Buscar Lote Conteo': {
                'url': 'logistica:buscar_lote_conteo',
                'roles_permitidos': ['Todos'],
                'descripcion': 'Búsqueda de lotes para conteo físico'
            },
            'Historial Conteos': {
                'url': 'logistica:historial_conteos',
                'roles_permitidos': ['Todos'],
                'descripcion': 'Historial de conteos realizados'
            },
            'Entrada Almacén': {
                'url': 'inventario:entrada_almacen_paso1',
                'roles_permitidos': ['Almacenero', 'Supervisión', 'Control Calidad'],
                'descripcion': 'Entrada de almacén'
            },
        }
        
        # Roles del sistema
        roles_sistema = [
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
        
        # Filtrar por rol si se especifica
        if rol_filtro:
            if rol_filtro not in roles_sistema:
                raise CommandError(f'Rol no válido: {rol_filtro}')
            roles_sistema = [rol_filtro]
        
        # Crear usuarios de prueba si se solicita
        if crear_usuarios:
            self.crear_usuarios_prueba(roles_sistema)
        
        # Verificar que existan los usuarios
        usuarios_existentes = self.verificar_usuarios_prueba(roles_sistema)
        
        if not usuarios_existentes:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  No hay usuarios de prueba. Ejecuta con --crear-usuarios'
                )
            )
            return
        
        # Ejecutar pruebas
        resultados = {}
        
        for rol in roles_sistema:
            self.stdout.write(self.style.HTTP_INFO(f'\n🔐 Probando rol: {rol}'))
            self.stdout.write('-' * 80)
            
            # Obtener usuario para este rol
            usuario = self.obtener_usuario_prueba(rol)
            if not usuario:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  No hay usuario de prueba para {rol}')
                )
                continue
            
            resultados[rol] = {}
            
            # Probar cada vista
            for vista_nombre, vista_config in vistas_a_probar.items():
                resultado = self.probar_vista(
                    usuario,
                    vista_config,
                    rol,
                    verbose
                )
                resultados[rol][vista_nombre] = resultado
        
        # Mostrar resumen
        self.mostrar_resumen(resultados, vistas_a_probar, roles_sistema)
    
    def crear_usuarios_prueba(self, roles):
        """Crear usuarios de prueba para cada rol"""
        self.stdout.write(self.style.SUCCESS('\n📝 Creando usuarios de prueba...\n'))
        
        for rol in roles:
            username = f'test_{rol.lower().replace(" ", "_")}'
            
            # Verificar si ya existe
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  ✓ Usuario {username} ya existe')
                continue
            
            # Crear usuario
            usuario = User.objects.create_user(
                username=username,
                password='test123456',
                email=f'{username}@test.com',
                first_name=rol,
                last_name='Test'
            )
            
            # Asignar rol
            try:
                grupo = Group.objects.get(name=rol)
                usuario.groups.add(grupo)
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Usuario {username} creado con rol {rol}')
                )
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Rol {rol} no existe en el sistema')
                )
    
    def verificar_usuarios_prueba(self, roles):
        """Verificar que existan usuarios de prueba"""
        usuarios = {}
        for rol in roles:
            username = f'test_{rol.lower().replace(" ", "_")}'
            usuario = User.objects.filter(username=username).first()
            if usuario:
                usuarios[rol] = usuario
        return usuarios
    
    def obtener_usuario_prueba(self, rol):
        """Obtener usuario de prueba para un rol"""
        username = f'test_{rol.lower().replace(" ", "_")}'
        return User.objects.filter(username=username).first()
    
    def probar_vista(self, usuario, vista_config, rol, verbose):
        """Probar acceso a una vista específica"""
        
        vista_nombre = vista_config.get('url')
        roles_permitidos = vista_config.get('roles_permitidos', [])
        descripcion = vista_config.get('descripcion', '')
        
        # Determinar si el rol debería tener acceso
        deberia_tener_acceso = (
            'Todos' in roles_permitidos or 
            rol in roles_permitidos
        )
        
        # Crear cliente y autenticar
        client = Client()
        client.login(username=usuario.username, password='test123456')
        
        try:
            # Obtener la URL
            url = reverse(vista_nombre)
        except Exception as e:
            if verbose:
                self.stdout.write(
                    self.style.WARNING(f'    ⚠️  Vista no encontrada: {vista_nombre}')
                )
            return {
                'acceso': 'ERROR',
                'esperado': deberia_tener_acceso,
                'correcto': False,
                'razon': 'Vista no encontrada'
            }
        
        # Realizar petición
        try:
            response = client.get(url, follow=True)
            status_code = response.status_code
            
            # Verificar acceso
            tiene_acceso = status_code == 200
            
            # Determinar si es correcto
            es_correcto = tiene_acceso == deberia_tener_acceso
            
            # Mostrar resultado
            if es_correcto:
                if tiene_acceso:
                    simbolo = '✅'
                    estado = 'ACCESO PERMITIDO'
                else:
                    simbolo = '✅'
                    estado = 'ACCESO DENEGADO (correcto)'
            else:
                simbolo = '❌'
                if tiene_acceso:
                    estado = 'ACCESO PERMITIDO (debería estar denegado)'
                else:
                    estado = 'ACCESO DENEGADO (debería estar permitido)'
            
            if verbose:
                self.stdout.write(
                    f'    {simbolo} {vista_nombre}: {estado}'
                )
            
            return {
                'acceso': 'PERMITIDO' if tiene_acceso else 'DENEGADO',
                'esperado': deberia_tener_acceso,
                'correcto': es_correcto,
                'status_code': status_code,
                'razon': descripcion
            }
        
        except Exception as e:
            if verbose:
                self.stdout.write(
                    self.style.WARNING(f'    ⚠️  Error al probar {vista_nombre}: {str(e)}')
                )
            return {
                'acceso': 'ERROR',
                'esperado': deberia_tener_acceso,
                'correcto': False,
                'razon': str(e)
            }
    
    def mostrar_resumen(self, resultados, vistas, roles):
        """Mostrar resumen de resultados"""
        
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('RESUMEN DE PRUEBAS')
        self.stdout.write('=' * 80 + '\n')
        
        # Contar resultados
        total_pruebas = 0
        pruebas_correctas = 0
        pruebas_incorrectas = 0
        
        for rol in roles:
            if rol not in resultados:
                continue
            
            rol_resultados = resultados[rol]
            rol_correctas = sum(1 for r in rol_resultados.values() if r.get('correcto'))
            rol_total = len(rol_resultados)
            
            total_pruebas += rol_total
            pruebas_correctas += rol_correctas
            pruebas_incorrectas += (rol_total - rol_correctas)
            
            # Mostrar por rol
            porcentaje = (rol_correctas / rol_total * 100) if rol_total > 0 else 0
            
            if porcentaje == 100:
                simbolo = '✅'
            elif porcentaje >= 80:
                simbolo = '⚠️'
            else:
                simbolo = '❌'
            
            self.stdout.write(
                f'{simbolo} {rol}: {rol_correctas}/{rol_total} ({porcentaje:.0f}%)'
            )
        
        # Resumen general
        self.stdout.write(f'\n{"-" * 80}')
        porcentaje_general = (pruebas_correctas / total_pruebas * 100) if total_pruebas > 0 else 0
        
        if porcentaje_general == 100:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ TODAS LAS PRUEBAS PASARON: {pruebas_correctas}/{total_pruebas}'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ ALGUNAS PRUEBAS FALLARON: {pruebas_correctas}/{total_pruebas} ({porcentaje_general:.0f}%)'
                )
            )
        
        self.stdout.write('\n' + '=' * 80 + '\n')
