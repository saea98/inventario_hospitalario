"""
Módulo para carga masiva de citas desde órdenes de suministro
"""

import csv
from io import StringIO
from datetime import datetime
from django.db import transaction

from .models import CitaProveedor, Proveedor, Almacen, Producto


class CargaMasivaCitas:
    """Servicio para cargar citas desde archivo CSV"""
    
    def __init__(self):
        self.errores = []
        self.advertencias = []
        self.citas_creadas = 0
        self.citas_skipped = 0
    
    def procesar_archivo(self, archivo):
        """
        Procesa un archivo CSV y crea las citas
        
        Args:
            archivo: Archivo CSV con órdenes de suministro
            
        Returns:
            dict: Resultado del procesamiento
        """
        self.errores = []
        self.advertencias = []
        self.citas_creadas = 0
        self.citas_skipped = 0
        
        try:
            # Leer el archivo
            if isinstance(archivo, str):
                with open(archivo, 'r', encoding='utf-8-sig') as f:
                    contenido = f.read()
            else:
                contenido = archivo.read()
                if isinstance(contenido, bytes):
                    contenido = contenido.decode('utf-8-sig')
            
            # Parsear CSV
            reader = csv.DictReader(StringIO(contenido))
            
            if not reader.fieldnames:
                self.errores.append("El archivo CSV está vacío")
                return self._resultado()
            
            # Validar encabezados
            campos_requeridos = [
                'numero_orden_suministro', 'rfc_proveedor', 'clave_medicamento',
                'codigo_almacen', 'fecha_limite_entrega'
            ]
            
            campos_faltantes = [c for c in campos_requeridos if c not in reader.fieldnames]
            if campos_faltantes:
                self.errores.append(f"Campos faltantes en el CSV: {', '.join(campos_faltantes)}")
                return self._resultado()
            
            # Procesar filas
            with transaction.atomic():
                for num_fila, fila in enumerate(reader, start=2):
                    self._procesar_fila(fila, num_fila)
            
            return self._resultado()
            
        except Exception as e:
            self.errores.append(f"Error al procesar el archivo: {str(e)}")
            return self._resultado()
    
    def _procesar_fila(self, fila, num_fila):
        """Procesa una fila del CSV"""
        
        try:
            # Validar campos requeridos
            numero_orden = fila.get('numero_orden_suministro', '').strip()
            rfc_proveedor = fila.get('rfc_proveedor', '').strip()
            clave_medicamento = fila.get('clave_medicamento', '').strip()
            codigo_almacen = fila.get('codigo_almacen', '').strip()
            fecha_limite_str = fila.get('fecha_limite_entrega', '').strip()
            
            # Validar que no estén vacíos
            if not all([numero_orden, rfc_proveedor, clave_medicamento, codigo_almacen, fecha_limite_str]):
                self.advertencias.append(f"Fila {num_fila}: Campos requeridos vacíos, se omite")
                self.citas_skipped += 1
                return
            
            # Buscar proveedor por RFC
            try:
                proveedor = Proveedor.objects.get(rfc=rfc_proveedor)
            except Proveedor.DoesNotExist:
                self.advertencias.append(f"Fila {num_fila}: Proveedor con RFC '{rfc_proveedor}' no encontrado")
                self.citas_skipped += 1
                return
            
            # Buscar almacén por código
            try:
                almacen = Almacen.objects.get(codigo=codigo_almacen)
            except Almacen.DoesNotExist:
                self.advertencias.append(f"Fila {num_fila}: Almacén con código '{codigo_almacen}' no encontrado, se omite")
                self.citas_skipped += 1
                return
            
            # Buscar producto por clave CNIS
            try:
                producto = Producto.objects.get(clave_cnis=clave_medicamento)
            except Producto.DoesNotExist:
                self.advertencias.append(f"Fila {num_fila}: Producto con clave CNIS '{clave_medicamento}' no encontrado")
                self.citas_skipped += 1
                return
            
            # Parsear fecha
            try:
                fecha_limite = None
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']:
                    try:
                        fecha_limite = datetime.strptime(fecha_limite_str, fmt).date()
                        break
                    except ValueError:
                        continue
                
                if not fecha_limite:
                    self.advertencias.append(f"Fila {num_fila}: Formato de fecha inválido '{fecha_limite_str}'")
                    self.citas_skipped += 1
                    return
                
                # Convertir a datetime (a las 08:00 AM)
                fecha_cita = datetime.combine(fecha_limite, datetime.min.time()).replace(hour=8)
                
            except Exception as e:
                self.advertencias.append(f"Fila {num_fila}: Error al parsear fecha: {str(e)}")
                self.citas_skipped += 1
                return
            
            # Verificar si ya existe una cita similar
            cita_existente = CitaProveedor.objects.filter(
                numero_orden_suministro=numero_orden,
                proveedor=proveedor,
                almacen=almacen
            ).exists()
            
            if cita_existente:
                self.advertencias.append(f"Fila {num_fila}: Cita duplicada (ya existe para esta orden)")
                self.citas_skipped += 1
                return
            
            # Crear la cita
            cita = CitaProveedor.objects.create(
                proveedor=proveedor,
                fecha_cita=fecha_cita,
                almacen=almacen,
                estado='programada',
                numero_orden_suministro=numero_orden,
                numero_contrato=fila.get('numero_contrato', '').strip() or None,
                clave_medicamento=clave_medicamento,
                tipo_transporte=fila.get('tipo_transporte', '').strip() or None,
                fecha_expedicion=self._parsear_fecha(fila.get('fecha_expedicion', '').strip()),
                fecha_limite_entrega=fecha_limite,
                numero_orden_remision=fila.get('numero_orden_remision', '').strip() or None,
                observaciones=f"Cargada desde orden de suministro: {numero_orden}"
            )
            
            self.citas_creadas += 1
            
        except Exception as e:
            self.errores.append(f"Fila {num_fila}: Error inesperado: {str(e)}")
            self.citas_skipped += 1
    
    def _parsear_fecha(self, fecha_str):
        """Parsea una fecha en diferentes formatos"""
        if not fecha_str:
            return None
        
        for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
            try:
                return datetime.strptime(fecha_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _resultado(self):
        """Retorna el resultado del procesamiento"""
        return {
            'citas_creadas': self.citas_creadas,
            'citas_skipped': self.citas_skipped,
            'errores': self.errores,
            'advertencias': self.advertencias,
            'exito': len(self.errores) == 0
        }
