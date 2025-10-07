"""
Procesador de archivos Excel para carga masiva de datos
Maneja los archivos CLUES.xlsx e inventario_hospital.xlsx
"""

import pandas as pd
from datetime import datetime, date
from django.db import transaction
from django.contrib.auth.models import User
from .models import (
    Institucion, Producto, Lote, Proveedor, OrdenSuministro,
    CategoriaProducto, Alcaldia, TipoInstitucion, FuenteFinanciamiento,
    MovimientoInventario
)


class ExcelProcessor:
    def __init__(self):
        self.errores = []
        self.registros_procesados = 0
        self.registros_exitosos = 0
        self.registros_con_error = 0
        self.total_registros = 0

    def procesar_archivo_clues(self, archivo_path):
        """
        Procesa el archivo CLUES.xlsx para cargar instituciones
        """
        try:
            # Leer archivo Excel
            df = pd.read_excel(archivo_path, sheet_name='Hoja1')
            self.total_registros = len(df)
            
            # Limpiar datos
            df = df.dropna(subset=['CLUE', 'DENOMINACION CLUE', 'ALCALDIA'])
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        self._procesar_institucion(row)
                        self.registros_exitosos += 1
                    except Exception as e:
                        self.registros_con_error += 1
                        self.errores.append(f"Fila {index + 2}: {str(e)}")
                    
                    self.registros_procesados += 1
            
            return True
            
        except Exception as e:
            self.errores.append(f"Error general al procesar archivo CLUES: {str(e)}")
            return False

    def _procesar_institucion(self, row):
        """Procesa una fila del archivo CLUES para crear una institución"""
        clue = str(row['CLUE']).strip()
        ib_clue = str(row.get('IB CLUE', '')).strip() if pd.notna(row.get('IB CLUE')) else ''
        denominacion = str(row['DENOMINACION CLUE']).strip()
        alcaldia_nombre = str(row['ALCALDIA']).strip()
        
        # Validaciones básicas
        if not clue or not denominacion or not alcaldia_nombre:
            raise ValueError("CLUE, denominación y alcaldía son obligatorios")
        
        # Obtener o crear alcaldía
        alcaldia, created = Alcaldia.objects.get_or_create(
            nombre=alcaldia_nombre,
            defaults={'activa': True}
        )
        
        # Obtener o crear tipo de institución (basado en denominación)
        tipo_nombre = self._determinar_tipo_institucion(denominacion)
        tipo_institucion, created = TipoInstitucion.objects.get_or_create(
            descripcion=tipo_nombre,
            defaults={'activo': True}
        )
        
        # Crear o actualizar institución
        institucion, created = Institucion.objects.update_or_create(
            clue=clue,
            defaults={
                'ib_clue': ib_clue,
                'denominacion': denominacion,
                'alcaldia': alcaldia,
                'tipo_institucion': tipo_institucion,
                'activa': True
            }
        )
        
        return institucion

    def _determinar_tipo_institucion(self, denominacion):
        """Determina el tipo de institución basado en la denominación"""
        denominacion_lower = denominacion.lower()
        
        if 'hospital' in denominacion_lower:
            if 'pediátrico' in denominacion_lower or 'infantil' in denominacion_lower:
                return 'Hospital Pediátrico'
            elif 'materno' in denominacion_lower:
                return 'Hospital Materno'
            else:
                return 'Hospital General'
        elif 'centro de salud' in denominacion_lower or 'c.s.' in denominacion_lower:
            if 't-i' in denominacion_lower:
                return 'Centro de Salud T-I'
            elif 't-ii' in denominacion_lower:
                return 'Centro de Salud T-II'
            elif 't-iii' in denominacion_lower:
                return 'Centro de Salud T-III'
            else:
                return 'Centro de Salud'
        elif 'clínica' in denominacion_lower:
            return 'Clínica'
        elif 'unidad' in denominacion_lower:
            return 'Unidad de Salud'
        else:
            return 'Otro'

    def procesar_archivo_inventario(self, archivo_path, usuario):
        """
        Procesa el archivo inventario_hospital.xlsx para cargar inventario
        """
        try:
            # Leer archivo Excel
            df = pd.read_excel(archivo_path, sheet_name='Inventario')
            self.total_registros = len(df)
            
            # Limpiar datos
            df = df.dropna(subset=['CLUES ', 'CLAVE/CNIS', 'DESCRIPCIÓN'])
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        self._procesar_lote_inventario(row, usuario)
                        self.registros_exitosos += 1
                    except Exception as e:
                        self.registros_con_error += 1
                        self.errores.append(f"Fila {index + 2}: {str(e)}")
                    
                    self.registros_procesados += 1
            
            return True
            
        except Exception as e:
            self.errores.append(f"Error general al procesar archivo inventario: {str(e)}")
            return False

    def _procesar_lote_inventario(self, row, usuario):
        """Procesa una fila del archivo de inventario para crear un lote"""
        # Extraer datos de la fila
        clue = str(row['CLUES ']).strip()
        clave_cnis = str(row['CLAVE/CNIS']).strip()
        descripcion = str(row['DESCRIPCIÓN']).strip()
        precio_unitario = float(row.get('PRECIO UNITARIO', 0))
        valor_total = float(row.get('VALOR TOTAL ', 0))
        estado = int(row.get('ESTADO DEL INSUMO \n1 = Disponible \n4 = Suspendido \n5 = Deteriorado\n6 =  Caducado', 1))
        cantidad_disponible = int(row.get('INVENTARIO DISPONIBLE', 0))
        unidad_medida = str(row.get('UNIDAD DE MEDIDA', 'PIEZA')).strip()
        numero_lote = str(row.get('LOTE', '')).strip()
        
        # Fechas
        fecha_caducidad = self._procesar_fecha(row.get('FECHA DE CADUCIDAD '))
        fecha_fabricacion = self._procesar_fecha(row.get('FECHA DE FABRICACIÓN '))
        fecha_recepcion = self._procesar_fecha(row.get('FECHA DE RECEPCIÓN'))
        
        # Datos adicionales
        orden_suministro_num = str(row.get('ORDEN DE SUMINISTRO', '')).strip()
        rfc_proveedor = str(row.get('RFC  PROVEEDOR', '')).strip()
        fuente_financiamiento = str(row.get('FUENTE DE FINACIAMIENTO ', '')).strip()
        es_cpm = str(row.get('INSUMO EN CPM', '')).strip().upper() in ['SÍ', 'SI', 'YES', '1', 'TRUE']
        
        # Validaciones básicas
        if not clue or not clave_cnis or not descripcion:
            raise ValueError("CLUE, CLAVE/CNIS y DESCRIPCIÓN son obligatorios")
        
        if cantidad_disponible < 0:
            raise ValueError("La cantidad disponible no puede ser negativa")
        
        if precio_unitario < 0:
            raise ValueError("El precio unitario no puede ser negativo")
        
        # Buscar institución
        try:
            institucion = Institucion.objects.get(clue=clue)
        except Institucion.DoesNotExist:
            raise ValueError(f"No se encontró la institución con CLUE: {clue}")
        
        # Obtener o crear categoría (basada en descripción)
        categoria_nombre = self._determinar_categoria_producto(descripcion)
        categoria, created = CategoriaProducto.objects.get_or_create(
            nombre=categoria_nombre,
            defaults={'activa': True}
        )
        
        # Obtener o crear producto
        producto, created = Producto.objects.update_or_create(
            clave_cnis=clave_cnis,
            defaults={
                'descripcion': descripcion,
                'categoria': categoria,
                'unidad_medida': unidad_medida,
                'precio_unitario_referencia': precio_unitario,
                'es_insumo_cpm': es_cpm,
                'activo': True
            }
        )
        
        # Procesar proveedor si existe
        proveedor = None
        if rfc_proveedor:
            proveedor, created = Proveedor.objects.get_or_create(
                rfc=rfc_proveedor,
                defaults={
                    'razon_social': f'Proveedor {rfc_proveedor}',
                    'activo': True
                }
            )
        
        # Procesar fuente de financiamiento
        fuente = None
        if fuente_financiamiento:
            fuente, created = FuenteFinanciamiento.objects.get_or_create(
                nombre=fuente_financiamiento,
                defaults={'activa': True}
            )
        
        # Procesar orden de suministro
        orden = None
        if orden_suministro_num and proveedor:
            orden, created = OrdenSuministro.objects.get_or_create(
                numero_orden=orden_suministro_num,
                proveedor=proveedor,
                defaults={
                    'fecha_orden': fecha_recepcion or date.today(),
                    'estado': 'ENTREGADA',
                    'fuente_financiamiento': fuente
                }
            )
        
        # Generar número de lote si no existe
        if not numero_lote:
            numero_lote = f"{clave_cnis}-{clue}-{datetime.now().strftime('%Y%m%d')}"
        
        # Crear lote
        lote = Lote.objects.create(
            numero_lote=numero_lote,
            producto=producto,
            institucion=institucion,
            cantidad_inicial=cantidad_disponible,
            cantidad_disponible=cantidad_disponible,
            precio_unitario=precio_unitario,
            fecha_caducidad=fecha_caducidad or date(2025, 12, 31),
            fecha_fabricacion=fecha_fabricacion,
            fecha_recepcion=fecha_recepcion or date.today(),
            estado=estado,
            orden_suministro=orden,
            creado_por=usuario
        )
        
        # Crear movimiento de entrada inicial
        MovimientoInventario.objects.create(
            lote=lote,
            tipo_movimiento='ENTRADA',
            cantidad=cantidad_disponible,
            cantidad_anterior=0,
            cantidad_nueva=cantidad_disponible,
            motivo='Carga inicial desde archivo Excel',
            usuario=usuario
        )
        
        return lote

    def _determinar_categoria_producto(self, descripcion):
        """Determina la categoría del producto basada en la descripción"""
        descripcion_lower = descripcion.lower()
        
        if any(word in descripcion_lower for word in ['medicamento', 'fármaco', 'droga', 'tableta', 'cápsula', 'jarabe']):
            return 'Medicamentos'
        elif any(word in descripcion_lower for word in ['material', 'insumo', 'equipo médico']):
            return 'Material Médico'
        elif any(word in descripcion_lower for word in ['jeringa', 'aguja', 'catéter', 'sonda']):
            return 'Material de Curación'
        elif any(word in descripcion_lower for word in ['reactivo', 'laboratorio', 'análisis']):
            return 'Reactivos de Laboratorio'
        elif any(word in descripcion_lower for word in ['vacuna', 'biológico', 'suero']):
            return 'Biológicos'
        else:
            return 'Otros Insumos'

    def _procesar_fecha(self, fecha_valor):
        """Convierte diferentes formatos de fecha a date object"""
        if pd.isna(fecha_valor) or fecha_valor == '':
            return None
        
        try:
            if isinstance(fecha_valor, datetime):
                return fecha_valor.date()
            elif isinstance(fecha_valor, date):
                return fecha_valor
            elif isinstance(fecha_valor, str):
                # Intentar diferentes formatos
                formatos = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                for formato in formatos:
                    try:
                        return datetime.strptime(fecha_valor, formato).date()
                    except ValueError:
                        continue
                raise ValueError(f"Formato de fecha no reconocido: {fecha_valor}")
            else:
                return None
        except Exception:
            return None

    def obtener_resumen(self):
        """Retorna un resumen del procesamiento"""
        return {
            'total_registros': self.total_registros,
            'registros_procesados': self.registros_procesados,
            'registros_exitosos': self.registros_exitosos,
            'registros_con_error': self.registros_con_error,
            'errores': self.errores
        }
