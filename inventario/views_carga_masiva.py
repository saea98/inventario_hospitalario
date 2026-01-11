import os
import tempfile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.management import call_command
from io import StringIO
import pandas as pd

from .forms_carga_masiva import CargaMasivaLotesForm
from .models import Producto, Almacen, UbicacionAlmacen, Lote, LoteUbicacion, CategoriaProducto
from django.utils import timezone


@login_required
@require_http_methods(["GET", "POST"])
def carga_masiva_lotes(request):
    """Vista para carga masiva de lotes desde archivo Excel"""
    
    if request.method == 'POST':
        form = CargaMasivaLotesForm(request.POST, request.FILES)
        
        if form.is_valid():
            archivo = request.FILES['archivo']
            institucion_id = form.cleaned_data['institucion']
            dry_run = form.cleaned_data['dry_run']
            
            # Guardar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in archivo.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            try:
                # Procesar archivo
                stats = procesar_carga_masiva(
                    tmp_path,
                    institucion_id,
                    request.user,
                    dry_run
                )
                
                # Guardar en sesión para mostrar en template
                request.session['carga_stats'] = stats
                
                return redirect('carga_masiva_resultado')
                
            except Exception as e:
                messages.error(request, f'Error al procesar archivo: {str(e)}')
            finally:
                # Limpiar archivo temporal
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
    else:
        form = CargaMasivaLotesForm()
    
    context = {
        'form': form,
        'titulo': 'Carga Masiva de Lotes',
    }
    
    return render(request, 'inventario/carga_masiva/formulario.html', context)


def procesar_carga_masiva(archivo_path, institucion_id, usuario, dry_run=False):
    """Procesa archivo Excel y carga lotes"""
    
    # Leer archivo
    try:
        df = pd.read_excel(archivo_path)
    except Exception as e:
        raise Exception(f'Error al leer archivo: {str(e)}')
    
    # Estadísticas
    stats = {
        'total_registros': len(df),
        'procesados': 0,
        'omitidos': 0,
        'productos_creados': 0,
        'ubicaciones_creadas': 0,
        'lotes_creados': 0,
        'lotes_actualizados': 0,
        'ubicaciones_eliminadas': 0,
        'ajustes_previos': 0,
        'errores': 0,
        'errores_detalle': [],
        'dry_run': dry_run,
    }
    
    if not dry_run:
        transaction.set_autocommit(False)
    
    try:
        for idx, row in df.iterrows():
            try:
                # 1. VALIDAR: Omitir si CLAVE es 'S/CLAVE'
                clave = str(row.get('CLAVE', '')).strip()
                if clave == 'S/CLAVE' or clave == 'nan':
                    stats['omitidos'] += 1
                    continue
                
                # Obtener datos
                almacen_id = int(row.get('almcen', 1))
                descripcion = str(row.get('DESCRIPCION', '')).strip()
                lote_numero = str(row.get('LOTE', '')).strip()
                caducidad_str = row.get('CADUCIDAD', '')
                ubicacion_codigo = str(row.get('UBICACIÓN', '')).strip()
                cantidad = int(row.get('INVENTARIO', 0))
                
                # Validar datos mínimos
                if not clave or not lote_numero or not ubicacion_codigo:
                    stats['errores'] += 1
                    stats['errores_detalle'].append(
                        f"Fila {idx+2}: Datos incompletos"
                    )
                    continue
                
                # 2. CREAR O OBTENER PRODUCTO
                # Obtener o crear categoría por defecto
                categoria, _ = CategoriaProducto.objects.get_or_create(
                    nombre='Sin Categoría',
                    defaults={'descripcion': 'Categoría por defecto para carga masiva'}
                )
                
                producto, producto_creado = Producto.objects.get_or_create(
                    clave_cnis=clave,
                    defaults={
                        'descripcion': descripcion or f'Producto {clave}',
                        'categoria': categoria,
                        'unidad_medida': 'PIEZA',
                        'es_insumo_cpm': False,
                    }
                )
                if producto_creado:
                    stats['productos_creados'] += 1
                
                # 3. OBTENER ALMACÉN
                try:
                    almacen = Almacen.objects.get(id=almacen_id)
                except Almacen.DoesNotExist:
                    stats['errores'] += 1
                    stats['errores_detalle'].append(
                        f"Fila {idx+2}: Almacén {almacen_id} no existe"
                    )
                    continue
                
                # 4. CREAR O OBTENER UBICACIÓN
                ubicacion, ubicacion_creada = UbicacionAlmacen.objects.get_or_create(
                    codigo=ubicacion_codigo,
                    almacen=almacen,
                    defaults={
                        'descripcion': ubicacion_codigo,
                        'activo': True,
                    }
                )
                if ubicacion_creada:
                    stats['ubicaciones_creadas'] += 1
                
                # 5. PROCESAR FECHA DE CADUCIDAD
                fecha_caducidad = None
                if pd.notna(caducidad_str) and caducidad_str != 'S/C':
                    try:
                        if isinstance(caducidad_str, str):
                            fecha_caducidad = pd.to_datetime(caducidad_str).date()
                        else:
                            fecha_caducidad = caducidad_str.date() if hasattr(caducidad_str, 'date') else caducidad_str
                    except:
                        pass
                
                # 6. CREAR O ACTUALIZAR LOTE
                lote, lote_creado = Lote.objects.get_or_create(
                    numero_lote=lote_numero,
                    producto=producto,
                    institucion_id=institucion_id,
                    defaults={
                        'cantidad_inicial': cantidad,
                        'cantidad_disponible': cantidad,
                        'precio_unitario': 0,
                        'valor_total': 0,
                        'fecha_recepcion': timezone.now().date(),
                        'fecha_caducidad': fecha_caducidad,
                        'almacen': almacen,
                        'creado_por': usuario,
                    }
                )
                
                if lote_creado:
                    stats['lotes_creados'] += 1
                else:
                    # Actualizar fecha de caducidad si cambió
                    if fecha_caducidad and lote.fecha_caducidad != fecha_caducidad:
                        lote.fecha_caducidad = fecha_caducidad
                    stats['lotes_actualizados'] += 1
                
                # 7. LIMPIAR UBICACIONES PREVIAS AL 30 DE DICIEMBRE (si aplica)
                # Solo para productos que NO inician con '060'
                if not clave.startswith('060'):
                    fecha_limite = timezone.datetime(2025, 12, 30).date()
                    ubicaciones_previas = LoteUbicacion.objects.filter(
                        lote=lote,
                        fecha_asignacion__lt=fecha_limite
                    ).exclude(ubicacion=ubicacion)
                    
                    for ub_previa in ubicaciones_previas:
                        # Crear movimiento de ajuste previo a conteo
                        if ub_previa.cantidad > 0:
                            from .models import MovimientoInventario
                            MovimientoInventario.objects.create(
                                lote=lote,
                                tipo_movimiento='AJUSTE_NEGATIVO',
                                cantidad=ub_previa.cantidad,
                                cantidad_anterior=ub_previa.cantidad,
                                cantidad_nueva=0,
                                motivo=f"Ajuste previo a conteo - Eliminación de ubicación previa ({ub_previa.ubicacion.codigo})",
                                usuario=usuario,
                                folio=f"AJUSTE-PREVIO-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                            )
                        
                        # Eliminar ubicación previa
                        ub_previa.delete()
                        stats['ubicaciones_eliminadas'] += 1
                        if ub_previa.cantidad > 0:
                            stats['ajustes_previos'] += 1
                
                # 8. CREAR O ACTUALIZAR LOTE_UBICACION
                lote_ubicacion, _ = LoteUbicacion.objects.get_or_create(
                    lote=lote,
                    ubicacion=ubicacion,
                    defaults={
                        'cantidad': cantidad,
                        'usuario_asignacion': usuario,
                    }
                )
                
                # Actualizar cantidad si cambió
                if lote_ubicacion.cantidad != cantidad:
                    lote_ubicacion.cantidad = cantidad
                    lote_ubicacion.usuario_asignacion = usuario
                    lote_ubicacion.save()
                
                # Guardar lote con cambios
                if not lote_creado:
                    lote.save()
                
                # Sincronizar cantidad total del lote
                lote.sincronizar_cantidad_disponible()
                
                stats['procesados'] += 1
                
            except Exception as e:
                stats['errores'] += 1
                stats['errores_detalle'].append(f"Fila {idx+2}: {str(e)}")
        
        if not dry_run:
            transaction.commit()
    
    except Exception as e:
        if not dry_run:
            transaction.rollback()
        raise e
    finally:
        if not dry_run:
            transaction.set_autocommit(True)
    
    return stats


@login_required
@require_http_methods(["GET"])
def carga_masiva_resultado(request):
    """Muestra resultado de carga masiva"""
    
    stats = request.session.pop('carga_stats', None)
    
    if not stats:
        return redirect('carga_masiva_lotes')
    
    # Calcular porcentajes
    if stats['total_registros'] > 0:
        stats['porcentaje_procesados'] = round(
            (stats['procesados'] / stats['total_registros']) * 100, 1
        )
        stats['porcentaje_errores'] = round(
            (stats['errores'] / stats['total_registros']) * 100, 1
        )
    
    context = {
        'stats': stats,
        'titulo': 'Resultado de Carga Masiva',
    }
    
    return render(request, 'inventario/carga_masiva/resultado.html', context)
