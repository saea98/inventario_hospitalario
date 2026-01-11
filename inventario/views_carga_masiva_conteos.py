"""
Vista para carga masiva de conteos físicos
Permite registrar los 3 conteos simultáneamente desde un archivo Excel
"""

import pandas as pd
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import datetime

from .models import (
    Lote, LoteUbicacion, RegistroConteoFisico, MovimientoInventario,
    Producto
)

logger = logging.getLogger(__name__)


def carga_masiva_conteos(request):
    """
    Vista para cargar conteos masivos desde un archivo Excel.
    
    Estructura esperada del archivo:
    - CLAVE: Clave CNIS del producto
    - LOTE: Número de lote
    - UBICACIÓN: Ubicación en almacén
    - INVENTARIO: Cantidad para los 3 conteos (mismo valor para 1er, 2do y 3er conteo)
    
    Validaciones:
    - Valida que exista la combinación CLAVE + LOTE + UBICACIÓN
    - Registra errores para registros no encontrados
    - Crea RegistroConteoFisico y MovimientoInventario
    """
    
    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']
        
        try:
            # Leer archivo Excel
            df = pd.read_excel(archivo)
            
            # Validar columnas requeridas
            columnas_requeridas = ['CLAVE', 'LOTE', 'UBICACIÓN', 'INVENTARIO']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                messages.error(
                    request,
                    f"El archivo no tiene las columnas requeridas: {', '.join(columnas_faltantes)}"
                )
                return render(request, 'inventario/conteo_fisico/carga_masiva_conteos.html')
            
            # Procesar conteos
            resultados = {
                'creados': 0,
                'actualizados': 0,
                'errores': [],
                'registros_procesados': []
            }
            
            usuario = request.user
            fecha_carga = timezone.now()
            
            with transaction.atomic():
                for idx, row in df.iterrows():
                    fila = idx + 2  # +2 porque Excel empieza en 1 y hay header
                    
                    try:
                        clave = str(row['CLAVE']).strip()
                        numero_lote = str(row['LOTE']).strip()
                        ubicacion_codigo = str(row['UBICACIÓN']).strip()
                        cantidad = int(row['INVENTARIO'])
                        
                        # Validar que cantidad sea válida
                        if cantidad < 0:
                            raise ValueError("La cantidad no puede ser negativa")
                        
                        # Buscar producto por CLAVE
                        try:
                            producto = Producto.objects.get(clave_cnis=clave)
                        except Producto.DoesNotExist:
                            raise ValueError(f"Producto con clave {clave} no encontrado")
                        
                        # Buscar lote
                        try:
                            lote = Lote.objects.get(
                                numero_lote=numero_lote,
                                producto=producto
                            )
                        except Lote.DoesNotExist:
                            raise ValueError(f"Lote {numero_lote} no encontrado para el producto {clave}")
                        
                        # Buscar ubicación del lote
                        try:
                            lote_ubicacion = LoteUbicacion.objects.get(
                                lote=lote,
                                ubicacion__codigo=ubicacion_codigo
                            )
                        except LoteUbicacion.DoesNotExist:
                            raise ValueError(
                                f"Ubicación {ubicacion_codigo} no encontrada para el lote {numero_lote}"
                            )
                        
                        # Obtener o crear registro de conteo
                        registro_conteo, created = RegistroConteoFisico.objects.get_or_create(
                            lote_ubicacion=lote_ubicacion,
                            defaults={
                                'usuario_creacion': usuario,
                                'primer_conteo': cantidad,
                                'segundo_conteo': cantidad,
                                'tercer_conteo': cantidad,
                                'completado': True
                            }
                        )
                        
                        if not created:
                            # Actualizar registro existente
                            registro_conteo.primer_conteo = cantidad
                            registro_conteo.segundo_conteo = cantidad
                            registro_conteo.tercer_conteo = cantidad
                            registro_conteo.completado = True
                            registro_conteo.usuario_ultima_actualizacion = usuario
                            registro_conteo.save()
                            resultados['actualizados'] += 1
                        else:
                            resultados['creados'] += 1
                        
                        # Crear MovimientoInventario (tercer conteo completado)
                        cantidad_anterior = lote_ubicacion.cantidad
                        cantidad_nueva = cantidad
                        diferencia = cantidad_nueva - cantidad_anterior
                        
                        # Actualizar LoteUbicacion
                        lote_ubicacion.cantidad = cantidad_nueva
                        lote_ubicacion.usuario_asignacion = usuario
                        lote_ubicacion.save()
                        
                        # Sincronizar cantidad del Lote
                        lote.sincronizar_cantidad_disponible()
                        
                        # Determinar tipo de movimiento
                        if diferencia > 0:
                            tipo_mov = 'AJUSTE_POSITIVO'
                        elif diferencia < 0:
                            tipo_mov = 'AJUSTE_NEGATIVO'
                        else:
                            tipo_mov = 'CONTEO_VERIFICADO'
                        
                        # Construir motivo
                        motivo_conteo = f"""Conteo Físico IMSS-Bienestar:
- Primer Conteo: {cantidad}
- Segundo Conteo: {cantidad}
- Tercer Conteo (Definitivo): {cantidad}
- Diferencia: {diferencia:+d}"""
                        
                        # Crear movimiento
                        movimiento = MovimientoInventario.objects.create(
                            lote=lote,
                            tipo_movimiento=tipo_mov,
                            cantidad=abs(diferencia),
                            cantidad_anterior=cantidad_anterior,
                            cantidad_nueva=cantidad_nueva,
                            motivo=motivo_conteo,
                            usuario=usuario,
                            folio=f"CONTEO-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                        )
                        
                        logger.info(
                            f"✅ Conteo registrado: {clave} - Lote {numero_lote} - "
                            f"Ubicación {ubicacion_codigo} - Cantidad: {cantidad}"
                        )
                        
                    except ValueError as e:
                        resultados['errores'].append({
                            'fila': fila,
                            'error': str(e),
                            'clave': row.get('CLAVE', 'N/A'),
                            'lote': row.get('LOTE', 'N/A'),
                            'ubicacion': row.get('UBICACIÓN', 'N/A')
                        })
                        logger.warning(f"⚠️ Error en fila {fila}: {str(e)}")
                    except Exception as e:
                        resultados['errores'].append({
                            'fila': fila,
                            'error': f"Error inesperado: {str(e)}",
                            'clave': row.get('CLAVE', 'N/A'),
                            'lote': row.get('LOTE', 'N/A'),
                            'ubicacion': row.get('UBICACIÓN', 'N/A')
                        })
                        logger.error(f"❌ Error inesperado en fila {fila}: {str(e)}")
            
            # Guardar resultados en sesión
            request.session['carga_conteos_resultado'] = resultados
            
            # Mostrar resumen
            total_procesados = resultados['creados'] + resultados['actualizados']
            total_errores = len(resultados['errores'])
            
            if total_errores > 0:
                messages.warning(
                    request,
                    f"Carga completada con errores. "
                    f"Creados: {resultados['creados']}, "
                    f"Actualizados: {resultados['actualizados']}, "
                    f"Errores: {total_errores}"
                )
            else:
                messages.success(
                    request,
                    f"Carga completada exitosamente. "
                    f"Creados: {resultados['creados']}, "
                    f"Actualizados: {resultados['actualizados']}"
                )
            
            return redirect('logistica:carga_masiva_conteos')
            
        except Exception as e:
            logger.error(f"Error al procesar archivo: {str(e)}")
            messages.error(request, f"Error al procesar el archivo: {str(e)}")
            return render(request, 'inventario/conteo_fisico/carga_masiva_conteos.html')
    
    # GET: Mostrar formulario y resultados previos
    resultados = request.session.pop('carga_conteos_resultado', None)
    
    context = {
        'resultados': resultados,
    }
    
    return render(request, 'inventario/conteo_fisico/carga_masiva_conteos.html', context)
