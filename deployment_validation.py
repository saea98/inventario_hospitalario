#!/usr/bin/env python3
"""
Script de validación para despliegue en 3 ambientes:
- Desarrollo (DEV)
- Calidad (QA)
- Productivo (PROD)

Valida:
1. Modelos de LlegadaProveedor e ItemLlegada
2. Formularios con nuevos campos
3. Templates actualizados
4. Migraciones aplicadas
5. Funcionalidad básica de llegadas
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from inventario.llegada_models import LlegadaProveedor, ItemLlegada
from inventario.llegada_forms import LlegadaProveedorForm, ItemLlegadaForm
from inventario.models import CitaProveedor, Almacen, Proveedor


class DeploymentValidator:
    """Validador de despliegue"""
    
    def __init__(self, environment='DEV'):
        self.environment = environment
        self.errors = []
        self.warnings = []
        self.success = []
    
    def validate_models(self):
        """Validar que los modelos existan y tengan los campos correctos"""
        print("\n[1] Validando Modelos...")
        
        try:
            # Verificar que LlegadaProveedor existe
            llegada_model = apps.get_model('inventario', 'LlegadaProveedor')
            print("  ✓ Modelo LlegadaProveedor encontrado")
            
            # Verificar campos
            required_fields = [
                'folio', 'cita', 'proveedor', 'almacen', 'tipo_red',
                'numero_piezas_emitidas', 'numero_piezas_recibidas',
                'observaciones_recepcion', 'estado'
            ]
            
            for field_name in required_fields:
                try:
                    field = llegada_model._meta.get_field(field_name)
                    print(f"  ✓ Campo '{field_name}' existe")
                except:
                    self.errors.append(f"Campo '{field_name}' no existe en LlegadaProveedor")
            
            # Verificar que ItemLlegada existe
            item_model = apps.get_model('inventario', 'ItemLlegada')
            print("  ✓ Modelo ItemLlegada encontrado")
            
            # Verificar campos de ItemLlegada
            item_fields = [
                'llegada', 'producto', 'numero_lote', 'fecha_caducidad',
                'cantidad_emitida', 'cantidad_recibida', 'piezas_por_lote',
                'precio_unitario_sin_iva', 'porcentaje_iva'
            ]
            
            for field_name in item_fields:
                try:
                    field = item_model._meta.get_field(field_name)
                    print(f"  ✓ Campo '{field_name}' existe en ItemLlegada")
                except:
                    self.errors.append(f"Campo '{field_name}' no existe en ItemLlegada")
            
            self.success.append("Modelos validados correctamente")
            
        except Exception as e:
            self.errors.append(f"Error validando modelos: {str(e)}")
    
    def validate_forms(self):
        """Validar que los formularios tengan los campos correctos"""
        print("\n[2] Validando Formularios...")
        
        try:
            # Validar LlegadaProveedorForm
            form = LlegadaProveedorForm()
            required_form_fields = ['cita', 'remision', 'almacen', 'tipo_red']
            
            for field_name in required_form_fields:
                if field_name in form.fields:
                    print(f"  ✓ Campo '{field_name}' en LlegadaProveedorForm")
                else:
                    self.errors.append(f"Campo '{field_name}' falta en LlegadaProveedorForm")
            
            # Validar ItemLlegadaForm
            item_form = ItemLlegadaForm()
            item_form_fields = ['producto', 'numero_lote', 'piezas_por_lote', 'precio_unitario_sin_iva']
            
            for field_name in item_form_fields:
                if field_name in item_form.fields:
                    print(f"  ✓ Campo '{field_name}' en ItemLlegadaForm")
                else:
                    self.errors.append(f"Campo '{field_name}' falta en ItemLlegadaForm")
            
            self.success.append("Formularios validados correctamente")
            
        except Exception as e:
            self.errors.append(f"Error validando formularios: {str(e)}")
    
    def validate_database(self):
        """Validar que la base de datos esté actualizada"""
        print("\n[3] Validando Base de Datos...")
        
        try:
            # Intentar crear una llegada de prueba (sin guardar)
            almacenes = Almacen.objects.filter(activo=True).first()
            if not almacenes:
                self.warnings.append("No hay almacenes activos en la BD")
                return
            
            # Verificar que podemos acceder a los modelos
            llegadas_count = LlegadaProveedor.objects.count()
            items_count = ItemLlegada.objects.count()
            
            print(f"  ✓ Llegadas registradas: {llegadas_count}")
            print(f"  ✓ Items registrados: {items_count}")
            
            self.success.append("Base de datos accesible")
            
        except Exception as e:
            self.errors.append(f"Error accediendo a la BD: {str(e)}")
    
    def validate_templates(self):
        """Validar que los templates existan"""
        print("\n[4] Validando Templates...")
        
        template_path = 'templates/inventario/llegadas/crear_llegada.html'
        if os.path.exists(template_path):
            print(f"  ✓ Template {template_path} existe")
            
            # Verificar que contiene los campos nuevos
            with open(template_path, 'r') as f:
                content = f.read()
                
                required_strings = [
                    'id_almacen',
                    'id_tipo_red',
                    'piezas_por_lote',
                    'validatePiezasSum'
                ]
                
                for req_str in required_strings:
                    if req_str in content:
                        print(f"  ✓ Template contiene '{req_str}'")
                    else:
                        self.warnings.append(f"Template no contiene '{req_str}'")
            
            self.success.append("Templates validados")
        else:
            self.errors.append(f"Template no encontrado: {template_path}")
    
    def validate_calculations(self):
        """Validar que los cálculos de IVA funcionan"""
        print("\n[5] Validando Cálculos...")
        
        try:
            # Crear un ItemLlegada de prueba (sin guardar)
            item = ItemLlegada()
            item.clave = '060001'  # Clave que debe tener IVA 16%
            
            iva = item.calcular_iva_automatico()
            if iva == 16.00:
                print(f"  ✓ IVA automático correcto para clave 060001: {iva}%")
            else:
                self.errors.append(f"IVA incorrecto para clave 060001: {iva}%")
            
            # Probar con clave sin IVA
            item.clave = '010001'
            iva = item.calcular_iva_automatico()
            if iva == 0.00:
                print(f"  ✓ IVA automático correcto para clave 010001: {iva}%")
            else:
                self.errors.append(f"IVA incorrecto para clave 010001: {iva}%")
            
            self.success.append("Cálculos validados")
            
        except Exception as e:
            self.errors.append(f"Error validando cálculos: {str(e)}")
    
    def print_report(self):
        """Imprimir reporte de validación"""
        print("\n" + "="*60)
        print(f"REPORTE DE VALIDACIÓN - AMBIENTE: {self.environment}")
        print("="*60)
        
        if self.success:
            print("\n✓ ÉXITOS:")
            for msg in self.success:
                print(f"  • {msg}")
        
        if self.warnings:
            print("\n⚠ ADVERTENCIAS:")
            for msg in self.warnings:
                print(f"  • {msg}")
        
        if self.errors:
            print("\n✗ ERRORES:")
            for msg in self.errors:
                print(f"  • {msg}")
        
        print("\n" + "="*60)
        
        if self.errors:
            print(f"RESULTADO: FALLÓ ({len(self.errors)} errores)")
            return False
        else:
            print(f"RESULTADO: EXITOSO")
            return True
    
    def run_all_validations(self):
        """Ejecutar todas las validaciones"""
        self.validate_models()
        self.validate_forms()
        self.validate_database()
        self.validate_templates()
        self.validate_calculations()
        
        return self.print_report()


def main():
    """Función principal"""
    # Detectar ambiente
    environment = os.getenv('ENVIRONMENT', 'DEV').upper()
    
    print(f"\n🔍 Iniciando validación de despliegue para ambiente: {environment}")
    
    validator = DeploymentValidator(environment=environment)
    success = validator.run_all_validations()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
