"""
Comando de Django para probar el sistema de roles
Verifica que cada usuario solo vea las funcionalidades asignadas
"""

from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import Group
from inventario.models import User

class Command(BaseCommand):
    help = 'Prueba el sistema de gestión de roles'

    # Usuarios de prueba
    USUARIOS_PRUEBA = {
        'revision1': {
            'password': 'revision123',
            'rol': 'Revisión',
            'urls_permitidas': [
                '/logistica/citas/',
                '/solicitudes/',
                '/dashboard/',
            ],
            'urls_denegadas': [
                '/picking/',
                '/admin-roles/',
                '/instituciones/',
            ]
        },
        'almacenero1': {
            'password': 'almacen123',
            'rol': 'Almacenero',
            'urls_permitidas': [
                '/picking/',
                '/entrada_almacen/paso1/',
                '/lotes/',
                '/dashboard/',
            ],
            'urls_denegadas': [
                '/admin-roles/',
                '/instituciones/',
                '/logistica/citas/',
            ]
        },
        'supervision1': {
            'password': 'supervision123',
            'rol': 'Supervisión',
            'urls_permitidas': [
                '/picking/',
                '/entrada_almacen/paso1/',
                '/lotes/',
                '/logistica/pedidos/',
                '/reportes_devoluciones/reporte_general/',
                '/dashboard/',
            ],
            'urls_denegadas': [
                '/admin-roles/',
                '/instituciones/',
            ]
        },
        'calidad1': {
            'password': 'calidad123',
            'rol': 'Control Calidad',
            'urls_permitidas': [
                '/entrada_almacen/paso1/',
                '/lotes/',
                '/dashboard/',
            ],
            'urls_denegadas': [
                '/picking/',
                '/admin-roles/',
                '/reportes_devoluciones/',
            ]
        },
        'facturacion1': {
            'password': 'factura123',
            'rol': 'Facturación',
            'urls_permitidas': [
                '/lotes/',
                '/dashboard/',
            ],
            'urls_denegadas': [
                '/picking/',
                '/entrada_almacen/paso1/',
                '/admin-roles/',
            ]
        },
        'logistica1': {
            'password': 'logistica123',
            'rol': 'Logística',
            'urls_permitidas': [
                '/logistica/traslados/',
                '/lotes/',
                '/dashboard/',
            ],
            'urls_denegadas': [
                '/picking/',
                '/entrada_almacen/paso1/',
                '/admin-roles/',
            ]
        },
        'recepcion1': {
            'password': 'recepcion123',
            'rol': 'Recepción',
            'urls_permitidas': [
                '/logistica/llegadas/',
                '/lotes/',
                '/dashboard/',
            ],
            'urls_denegadas': [
                '/picking/',
                '/entrada_almacen/paso1/',
                '/admin-roles/',
            ]
        },
        'conteo1': {
            'password': 'conteo123',
            'rol': 'Conteo',
            'urls_permitidas': [
                '/logistica/conteo/',
                '/lotes/',
                '/dashboard/',
            ],
            'urls_denegadas': [
                '/picking/',
                '/entrada_almacen/paso1/',
                '/admin-roles/',
            ]
        },
        'gestor1': {
            'password': 'gestor123',
            'rol': 'Gestor de Inventario',
            'urls_permitidas': [
                '/movimientos/',
                '/logistica/pedidos/',
                '/lotes/',
                '/dashboard/',
            ],
            'urls_denegadas': [
                '/admin-roles/',
                '/instituciones/',
            ]
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = Client()
        self.resultados = {
            'exitosas': 0,
            'fallidas': 0,
            'errores': []
        }

    def pruebar_usuario(self, username, config):
        """Prueba un usuario específico"""
        self.stdout.write(self.style.SUCCESS(f"\n{'='*70}"))
        self.stdout.write(self.style.SUCCESS(f"🧪 PROBANDO USUARIO: {username} ({config['rol']})"))
        self.stdout.write(self.style.SUCCESS(f"{'='*70}"))

        try:
            # Intentar login
            login_exitoso = self.client.login(
                username=username,
                password=config['password']
            )

            if not login_exitoso:
                self.stdout.write(self.style.ERROR(f"❌ No se pudo iniciar sesión"))
                self.resultados['fallidas'] += 1
                return

            self.stdout.write(self.style.SUCCESS(f"✅ Login exitoso"))

            # Probar URLs permitidas
            self.stdout.write(self.style.WARNING(f"\n📍 Probando URLs permitidas:"))
            for url in config['urls_permitidas']:
                response = self.client.get(url)
                if response.status_code in [200, 302]:
                    self.stdout.write(self.style.SUCCESS(f"  ✅ {url} - Status: {response.status_code}"))
                    self.resultados['exitosas'] += 1
                else:
                    self.stdout.write(self.style.ERROR(f"  ❌ {url} - Status: {response.status_code}"))
                    self.resultados['fallidas'] += 1
                    self.resultados['errores'].append({
                        'usuario': username,
                        'url': url,
                        'status': response.status_code,
                        'tipo': 'URL permitida con error'
                    })

            # Probar URLs denegadas
            self.stdout.write(self.style.WARNING(f"\n🚫 Probando URLs denegadas:"))
            for url in config['urls_denegadas']:
                response = self.client.get(url, follow=True)
                if response.status_code == 403 or '/login' in response.request['PATH_INFO']:
                    self.stdout.write(self.style.SUCCESS(f"  ✅ {url} - Acceso denegado correctamente"))
                    self.resultados['exitosas'] += 1
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  {url} - Status: {response.status_code} (Se esperaba 403)"))
                    self.resultados['fallidas'] += 1
                    self.resultados['errores'].append({
                        'usuario': username,
                        'url': url,
                        'status': response.status_code,
                        'tipo': 'URL denegada sin bloqueo'
                    })

            # Logout
            self.client.logout()
            self.stdout.write(self.style.SUCCESS(f"\n✅ Logout exitoso"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error durante prueba: {str(e)}"))
            self.resultados['fallidas'] += 1
            self.resultados['errores'].append({
                'usuario': username,
                'error': str(e),
                'tipo': 'Excepción'
            })

    def mostrar_resumen(self):
        """Muestra un resumen de las pruebas"""
        self.stdout.write(self.style.SUCCESS(f"\n{'='*70}"))
        self.stdout.write(self.style.SUCCESS(f"📊 RESUMEN DE PRUEBAS"))
        self.stdout.write(self.style.SUCCESS(f"{'='*70}"))

        total = self.resultados['exitosas'] + self.resultados['fallidas']
        porcentaje = (self.resultados['exitosas'] / total * 100) if total > 0 else 0

        self.stdout.write(self.style.SUCCESS(f"\n✅ Pruebas exitosas: {self.resultados['exitosas']}"))
        self.stdout.write(self.style.ERROR(f"❌ Pruebas fallidas: {self.resultados['fallidas']}"))
        self.stdout.write(self.style.WARNING(f"📈 Tasa de éxito: {porcentaje:.1f}%"))

        if self.resultados['errores']:
            self.stdout.write(self.style.ERROR(f"\n⚠️  ERRORES ENCONTRADOS ({len(self.resultados['errores'])})"))
            self.stdout.write("-" * 70)
            for error in self.resultados['errores']:
                self.stdout.write(f"\n  Usuario: {error.get('usuario', 'N/A')}")
                self.stdout.write(f"  URL: {error.get('url', 'N/A')}")
                self.stdout.write(f"  Tipo: {error.get('tipo', 'N/A')}")
                if 'status' in error:
                    self.stdout.write(f"  Status: {error['status']}")
                if 'error' in error:
                    self.stdout.write(f"  Error: {error['error']}")

        self.stdout.write(self.style.SUCCESS(f"\n{'='*70}"))
        if self.resultados['fallidas'] == 0:
            self.stdout.write(self.style.SUCCESS(f"✨ ¡TODAS LAS PRUEBAS EXITOSAS!"))
        else:
            self.stdout.write(self.style.ERROR(f"⚠️  {self.resultados['fallidas']} pruebas fallidas - Revisar arriba"))
        self.stdout.write(self.style.SUCCESS(f"{'='*70}\n"))

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n" + "="*70))
        self.stdout.write(self.style.SUCCESS("🚀 INICIANDO PRUEBAS DEL SISTEMA DE ROLES"))
        self.stdout.write(self.style.SUCCESS("="*70))

        for username, config in self.USUARIOS_PRUEBA.items():
            try:
                user = User.objects.get(username=username)
                self.pruebar_usuario(username, config)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"\n⚠️  Usuario '{username}' no encontrado"))
                self.resultados['fallidas'] += 1

        self.mostrar_resumen()
