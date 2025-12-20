#!/usr/bin/env python
"""
Script automatizado para probar el sistema de roles
Verifica que cada usuario solo vea las funcionalidades asignadas
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth.models import Group

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_hospitalario.settings')
django.setup()

from inventario.models import User

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

class PruebasRoles:
    def __init__(self):
        self.client = Client()
        self.resultados = {
            'exitosas': 0,
            'fallidas': 0,
            'errores': []
        }
    
    def pruebar_usuario(self, username, config):
        """Prueba un usuario específico"""
        print(f"\n{'='*70}")
        print(f"🧪 PROBANDO USUARIO: {username} ({config['rol']})")
        print(f"{'='*70}")
        
        # Intentar login
        try:
            login_exitoso = self.client.login(
                username=username,
                password=config['password']
            )
            
            if not login_exitoso:
                print(f"❌ No se pudo iniciar sesión")
                self.resultados['fallidas'] += 1
                return
            
            print(f"✅ Login exitoso")
            
            # Probar URLs permitidas
            print(f"\n📍 Probando URLs permitidas:")
            for url in config['urls_permitidas']:
                response = self.client.get(url)
                if response.status_code in [200, 302]:  # 200 OK, 302 redirect
                    print(f"  ✅ {url} - Status: {response.status_code}")
                    self.resultados['exitosas'] += 1
                else:
                    print(f"  ❌ {url} - Status: {response.status_code}")
                    self.resultados['fallidas'] += 1
                    self.resultados['errores'].append({
                        'usuario': username,
                        'url': url,
                        'status': response.status_code,
                        'tipo': 'URL permitida con error'
                    })
            
            # Probar URLs denegadas
            print(f"\n🚫 Probando URLs denegadas:")
            for url in config['urls_denegadas']:
                response = self.client.get(url, follow=True)
                # Esperamos 403 (Forbidden) o redirección a login
                if response.status_code == 403 or '/login' in response.request['PATH_INFO']:
                    print(f"  ✅ {url} - Acceso denegado correctamente")
                    self.resultados['exitosas'] += 1
                else:
                    print(f"  ⚠️  {url} - Status: {response.status_code} (Se esperaba 403)")
                    self.resultados['fallidas'] += 1
                    self.resultados['errores'].append({
                        'usuario': username,
                        'url': url,
                        'status': response.status_code,
                        'tipo': 'URL denegada sin bloqueo'
                    })
            
            # Logout
            self.client.logout()
            print(f"\n✅ Logout exitoso")
            
        except Exception as e:
            print(f"❌ Error durante prueba: {str(e)}")
            self.resultados['fallidas'] += 1
            self.resultados['errores'].append({
                'usuario': username,
                'error': str(e),
                'tipo': 'Excepción'
            })
    
    def ejecutar_todas_las_pruebas(self):
        """Ejecuta pruebas para todos los usuarios"""
        print("\n" + "="*70)
        print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE ROLES")
        print("="*70)
        
        for username, config in USUARIOS_PRUEBA.items():
            # Verificar que el usuario existe
            try:
                user = User.objects.get(username=username)
                self.pruebar_usuario(username, config)
            except User.DoesNotExist:
                print(f"\n⚠️  Usuario '{username}' no encontrado")
                self.resultados['fallidas'] += 1
        
        self.mostrar_resumen()
    
    def mostrar_resumen(self):
        """Muestra un resumen de las pruebas"""
        print("\n" + "="*70)
        print("📊 RESUMEN DE PRUEBAS")
        print("="*70)
        
        total = self.resultados['exitosas'] + self.resultados['fallidas']
        porcentaje = (self.resultados['exitosas'] / total * 100) if total > 0 else 0
        
        print(f"\n✅ Pruebas exitosas: {self.resultados['exitosas']}")
        print(f"❌ Pruebas fallidas: {self.resultados['fallidas']}")
        print(f"📈 Tasa de éxito: {porcentaje:.1f}%")
        
        if self.resultados['errores']:
            print(f"\n⚠️  ERRORES ENCONTRADOS ({len(self.resultados['errores'])}):")
            print("-" * 70)
            for error in self.resultados['errores']:
                print(f"\n  Usuario: {error.get('usuario', 'N/A')}")
                print(f"  URL: {error.get('url', 'N/A')}")
                print(f"  Tipo: {error.get('tipo', 'N/A')}")
                if 'status' in error:
                    print(f"  Status: {error['status']}")
                if 'error' in error:
                    print(f"  Error: {error['error']}")
        
        print("\n" + "="*70)
        if self.resultados['fallidas'] == 0:
            print("✨ ¡TODAS LAS PRUEBAS EXITOSAS!")
        else:
            print(f"⚠️  {self.resultados['fallidas']} pruebas fallidas - Revisar arriba")
        print("="*70 + "\n")

if __name__ == '__main__':
    pruebas = PruebasRoles()
    pruebas.ejecutar_todas_las_pruebas()
