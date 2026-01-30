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

from .forms_carga_masiva import CargaMasivaLotesForm, CargaMasivaOrdenesSuministroForm
from .models import (
    Producto, Almacen, UbicacionAlmacen, Lote, LoteUbicacion, CategoriaProducto,
    OrdenSuministro, Proveedor, Institucion
)
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
                # Obtener opción de actualizar cantidad
                # Django BooleanField siempre incluye el campo en cleaned_data (True si marcado, False si no)
                actualizar_cantidad = form.cleaned_data.get('actualizar_cantidad', True)
                
                # Procesar archivo
                stats = procesar_carga_masiva(
                    tmp_path,
                    institucion_id,
                    request.user,
                    dry_run,
                    actualizar_cantidad
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


def procesar_carga_masiva(archivo_path, institucion_id, usuario, dry_run=False, actualizar_cantidad=True):
    """Procesa archivo Excel y carga lotes
    
    Args:
        archivo_path: Ruta del archivo Excel
        institucion_id: ID de la institución
        usuario: Usuario que realiza la carga
        dry_run: Si es True, solo muestra cambios sin aplicarlos
        actualizar_cantidad: Si es True, actualiza las cantidades. Si es False, solo actualiza otros campos.
    """
    
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
                # Primero verificar si el lote ya existe
                try:
                    lote = Lote.objects.get(
                        numero_lote=lote_numero,
                        producto=producto,
                        institucion_id=institucion_id
                    )
                    lote_creado = False
                except Lote.DoesNotExist:
                    lote = None
                    lote_creado = True
                
                if lote_creado:
                    # LOTE NUEVO: Siempre establecer cantidades (campo obligatorio)
                    # Si actualizar_cantidad=False, usar la cantidad del Excel pero no actualizar después
                    defaults_lote = {
                        'cantidad_inicial': cantidad,
                        'cantidad_disponible': cantidad,
                        'precio_unitario': 0,
                        'valor_total': 0,
                        'fecha_recepcion': timezone.now().date(),
                        'fecha_caducidad': fecha_caducidad,
                        'almacen': almacen,
                        'creado_por': usuario,
                    }
                    
                    lote = Lote.objects.create(
                        numero_lote=lote_numero,
                        producto=producto,
                        institucion_id=institucion_id,
                        **defaults_lote
                    )
                    stats['lotes_creados'] += 1
                else:
                    # LOTE EXISTENTE: Solo actualizar cantidades si está habilitado
                    # Actualizar fecha de caducidad si cambió
                    if fecha_caducidad and lote.fecha_caducidad != fecha_caducidad:
                        lote.fecha_caducidad = fecha_caducidad
                    
                    # Actualizar almacén si cambió
                    if lote.almacen != almacen:
                        lote.almacen = almacen
                    
                    # Actualizar cantidades solo si está habilitado
                    if actualizar_cantidad:
                        lote.cantidad_inicial = cantidad
                        lote.cantidad_disponible = cantidad
                    
                    lote.save()
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
                # Verificar si la ubicación ya existe para este lote
                try:
                    lote_ubicacion = LoteUbicacion.objects.get(
                        lote=lote,
                        ubicacion=ubicacion
                    )
                    ubicacion_creada = False
                except LoteUbicacion.DoesNotExist:
                    lote_ubicacion = None
                    ubicacion_creada = True
                
                if ubicacion_creada:
                    # UBICACIÓN NUEVA: Siempre establecer cantidad (campo obligatorio)
                    # Si actualizar_cantidad=False, usar la cantidad del Excel pero no actualizar después
                    lote_ubicacion = LoteUbicacion.objects.create(
                        lote=lote,
                        ubicacion=ubicacion,
                        cantidad=cantidad,
                        usuario_asignacion=usuario,
                    )
                else:
                    # UBICACIÓN EXISTENTE: Solo actualizar cantidad si está habilitado
                    if actualizar_cantidad and lote_ubicacion.cantidad != cantidad:
                        lote_ubicacion.cantidad = cantidad
                        lote_ubicacion.usuario_asignacion = usuario
                        lote_ubicacion.save()
                
                # Sincronizar cantidad total del lote solo si se actualizan cantidades
                if actualizar_cantidad:
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


def _procesar_fecha_orden(valor):
    """Convierte valor a date para órdenes."""
    if pd.isna(valor) or valor == '':
        return None
    try:
        if hasattr(valor, 'date'):
            return valor.date()
        from datetime import date, datetime
        if isinstance(valor, date):
            return valor
        if isinstance(valor, str):
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(valor.strip(), fmt).date()
                except ValueError:
                    continue
        return pd.to_datetime(valor).date()
    except Exception:
        return None


def procesar_carga_masiva_ordenes(archivo_path, partida_default='N/A', dry_run=False):
    """
    Procesa Excel para crear órdenes de suministro y vincular lotes.
    Columnas: CLUES, ORDEN DE SUMINISTRO, RFC, CLAVE, LOTE, F_REC
    """
    try:
        df = pd.read_excel(archivo_path)
    except Exception as e:
        raise Exception(f'Error al leer archivo: {str(e)}')

    columnas_requeridas = ['ORDEN DE SUMINISTRO', 'RFC', 'CLAVE', 'LOTE', 'CLUES']
    columnas_excel = [str(c).strip() for c in df.columns]
    faltantes = [c for c in columnas_requeridas if c not in columnas_excel]
    if faltantes:
        raise Exception(f'Columnas requeridas faltantes: {faltantes}')

    partida_default = str(partida_default or 'N/A')[:20]
    stats = {
        'total_registros': len(df),
        'ordenes_creadas': 0,
        'ordenes_existentes': 0,
        'lotes_vinculados': 0,
        'lotes_no_encontrados': 0,
        'productos_no_encontrados': 0,
        'instituciones_no_encontradas': 0,
        'omitidos': 0,
        'errores': 0,
        'errores_detalle': [],
        'dry_run': dry_run,
    }
    cache_ordenes = {}

    if not dry_run:
        transaction.set_autocommit(False)

    try:
        for idx, row in df.iterrows():
            try:
                clave = str(row.get('CLAVE', '')).strip()
                if clave in ('S/CLAVE', 'nan', ''):
                    stats['omitidos'] += 1
                    continue

                orden_numero = str(row.get('ORDEN DE SUMINISTRO', '')).strip()[:200]
                rfc = str(row.get('RFC', '')).strip()[:13]
                lote_numero = str(row.get('LOTE', '')).strip()[:50]
                clues = str(row.get('CLUES', '')).strip()

                if not orden_numero or not rfc or not lote_numero or not clues:
                    stats['errores'] += 1
                    stats['errores_detalle'].append(
                        f"Fila {idx+2}: Datos incompletos"
                    )
                    continue

                try:
                    proveedor = Proveedor.objects.get(rfc=rfc)
                except Proveedor.DoesNotExist:
                    proveedor = Proveedor.objects.create(
                        rfc=rfc, razon_social=f'Proveedor {rfc}', activo=True
                    )

                try:
                    producto = Producto.objects.get(clave_cnis=clave)
                    partida = (producto.partida_presupuestal or partida_default)[:20]
                except Producto.DoesNotExist:
                    stats['productos_no_encontrados'] += 1
                    stats['errores_detalle'].append(
                        f"Fila {idx+2}: Producto '{clave}' no existe"
                    )
                    continue

                try:
                    institucion = Institucion.objects.get(clue=clues)
                except Institucion.DoesNotExist:
                    stats['instituciones_no_encontradas'] += 1
                    stats['errores_detalle'].append(
                        f"Fila {idx+2}: Institución CLUES '{clues}' no existe"
                    )
                    continue

                cache_key = orden_numero
                if cache_key in cache_ordenes:
                    orden = cache_ordenes[cache_key]
                else:
                    f_rec = _procesar_fecha_orden(row.get('F_REC'))
                    fecha_orden = f_rec or timezone.now().date()
                    orden, creada = OrdenSuministro.objects.get_or_create(
                        numero_orden=orden_numero,
                        defaults={
                            'proveedor': proveedor,
                            'partida_presupuestal': partida,
                            'fecha_orden': fecha_orden,
                            'activo': True,
                        }
                    )
                    cache_ordenes[cache_key] = orden
                    if creada:
                        stats['ordenes_creadas'] += 1
                    else:
                        stats['ordenes_existentes'] += 1

                try:
                    lote = Lote.objects.get(
                        numero_lote=lote_numero,
                        producto=producto,
                        institucion=institucion,
                    )
                    if lote.orden_suministro_id != orden.id:
                        if not dry_run:
                            lote.orden_suministro = orden
                            lote.save()
                        stats['lotes_vinculados'] += 1
                except Lote.DoesNotExist:
                    stats['lotes_no_encontrados'] += 1
                    stats['errores_detalle'].append(
                        f"Fila {idx+2}: Lote no encontrado (LOTE={lote_numero}, CLAVE={clave})"
                    )
                except Lote.MultipleObjectsReturned:
                    lote = Lote.objects.filter(
                        numero_lote=lote_numero,
                        producto=producto,
                        institucion=institucion,
                    ).first()
                    if not dry_run and lote and lote.orden_suministro_id != orden.id:
                        lote.orden_suministro = orden
                        lote.save()
                    stats['lotes_vinculados'] += 1

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


@login_required
@require_http_methods(["GET", "POST"])
def carga_masiva_ubicaciones_almacen(request):
    """Vista para carga masiva de actualización de almacen_id en UbicacionAlmacen desde archivo Excel"""
    
    if request.method == 'POST':
        if 'archivo_excel' not in request.FILES:
            messages.error(request, 'Por favor, selecciona un archivo Excel.')
            return render(request, 'inventario/carga_masiva/ubicaciones_almacen.html', {})
        
        archivo = request.FILES['archivo_excel']
        
        # Validar extensión
        if not archivo.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'El archivo debe ser un Excel (.xlsx o .xls)')
            return render(request, 'inventario/carga_masiva/ubicaciones_almacen.html', {})
        
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            for chunk in archivo.chunks():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        try:
            # Leer archivo Excel
            try:
                df = pd.read_excel(tmp_path)
                # Normalizar nombres de columnas (minúsculas, sin espacios)
                df.columns = [col.strip().lower() for col in df.columns]
            except Exception as e:
                messages.error(request, f'Error al leer el archivo Excel: {str(e)}')
                return render(request, 'inventario/carga_masiva/ubicaciones_almacen.html', {})
            
            # Validar columnas requeridas
            columnas_requeridas = ['ubicación', 'zona']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                messages.error(
                    request, 
                    f'Faltan las siguientes columnas en el archivo: {", ".join(columnas_faltantes)}. '
                    f'Las columnas deben llamarse exactamente: "ubicación" y "zona"'
                )
                return render(request, 'inventario/carga_masiva/ubicaciones_almacen.html', {})
            
            # Estadísticas
            stats = {
                'total_registros': len(df),
                'actualizados': 0,
                'no_encontrados_ubicacion': [],
                'no_encontrados_almacen': [],
                'errores': [],
            }
            
            # Procesar cada fila
            with transaction.atomic():
                for idx, row in df.iterrows():
                    try:
                        ubicacion_codigo = str(row.get('ubicación', '')).strip()
                        zona_nombre = str(row.get('zona', '')).strip()
                        
                        # Validar que no estén vacíos
                        if not ubicacion_codigo or not zona_nombre:
                            stats['errores'].append({
                                'fila': idx + 2,
                                'ubicacion': ubicacion_codigo or '(vacío)',
                                'zona': zona_nombre or '(vacío)',
                                'mensaje': 'Ubicación o zona vacía'
                            })
                            continue
                        
                        # Buscar UbicacionAlmacen por código
                        try:
                            ubicacion = UbicacionAlmacen.objects.get(codigo=ubicacion_codigo)
                        except UbicacionAlmacen.DoesNotExist:
                            stats['no_encontrados_ubicacion'].append({
                                'fila': idx + 2,
                                'codigo': ubicacion_codigo
                            })
                            continue
                        except UbicacionAlmacen.MultipleObjectsReturned:
                            # Si hay múltiples, tomar el primero
                            ubicacion = UbicacionAlmacen.objects.filter(codigo=ubicacion_codigo).first()
                        
                        # Buscar Almacen por nombre
                        try:
                            almacen = Almacen.objects.get(nombre=zona_nombre)
                        except Almacen.DoesNotExist:
                            stats['no_encontrados_almacen'].append({
                                'fila': idx + 2,
                                'nombre': zona_nombre,
                                'ubicacion': ubicacion_codigo
                            })
                            continue
                        except Almacen.MultipleObjectsReturned:
                            # Si hay múltiples, tomar el primero
                            almacen = Almacen.objects.filter(nombre=zona_nombre).first()
                        
                        # Actualizar almacen_id
                        if ubicacion.almacen_id != almacen.id:
                            ubicacion.almacen = almacen
                            ubicacion.save()
                            stats['actualizados'] += 1
                        
                    except Exception as e:
                        stats['errores'].append({
                            'fila': idx + 2,
                            'ubicacion': str(row.get('ubicación', '')),
                            'zona': str(row.get('zona', '')),
                            'mensaje': str(e)
                        })
            
            # Preparar mensajes de resultado
            if stats['actualizados'] > 0:
                messages.success(
                    request, 
                    f'✅ Se actualizaron {stats["actualizados"]} ubicaciones correctamente.'
                )
            
            if stats['no_encontrados_ubicacion']:
                total_no_ubic = len(stats['no_encontrados_ubicacion'])
                messages.warning(
                    request, 
                    f'⚠️ {total_no_ubic} ubicación(es) no encontrada(s) en el sistema. '
                    f'Primeras 5: {", ".join([u["codigo"] for u in stats["no_encontrados_ubicacion"][:5]])}'
                )
            
            if stats['no_encontrados_almacen']:
                total_no_alm = len(stats['no_encontrados_almacen'])
                messages.warning(
                    request, 
                    f'⚠️ {total_no_alm} almacén(es) no encontrado(s) en el sistema. '
                    f'Primeras 5: {", ".join([a["nombre"] for a in stats["no_encontrados_almacen"][:5]])}'
                )
            
            if stats['errores']:
                total_errores = len(stats['errores'])
                messages.error(
                    request, 
                    f'❌ {total_errores} error(es) durante el procesamiento. '
                    f'Revisa los detalles en la tabla de resultados.'
                )
            
            # Guardar estadísticas en sesión para mostrar en template
            request.session['carga_ubicaciones_stats'] = stats
            
            return render(request, 'inventario/carga_masiva/ubicaciones_almacen.html', {
                'stats': stats,
                'mostrar_resultados': True
            })
            
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
        finally:
            # Limpiar archivo temporal
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    # GET request - mostrar formulario
    stats = request.session.pop('carga_ubicaciones_stats', None)
    context = {
        'stats': stats,
        'mostrar_resultados': stats is not None if stats else False
    }
    
    return render(request, 'inventario/carga_masiva/ubicaciones_almacen.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def carga_masiva_ordenes_suministro(request):
    """Vista para carga masiva de órdenes de suministro desde Excel."""
    if request.method == 'POST':
        form = CargaMasivaOrdenesSuministroForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            partida_default = form.cleaned_data.get('partida_default', 'N/A')
            dry_run = form.cleaned_data.get('dry_run', False)

            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in archivo.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            try:
                stats = procesar_carga_masiva_ordenes(
                    tmp_path, partida_default=partida_default, dry_run=dry_run
                )
                request.session['carga_ordenes_stats'] = stats
                return redirect('carga_masiva_ordenes_resultado')
            except Exception as e:
                messages.error(request, f'Error al procesar archivo: {str(e)}')
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = CargaMasivaOrdenesSuministroForm()

    context = {
        'form': form,
        'titulo': 'Carga Masiva de Órdenes de Suministro',
    }
    return render(request, 'inventario/carga_masiva/ordenes_suministro.html', context)


@login_required
@require_http_methods(["GET"])
def carga_masiva_ordenes_resultado(request):
    """Muestra resultado de carga masiva de órdenes."""
    stats = request.session.pop('carga_ordenes_stats', None)
    if not stats:
        return redirect('carga_masiva_ordenes_suministro')

    context = {
        'stats': stats,
        'titulo': 'Resultado - Carga Órdenes de Suministro',
    }
    return render(request, 'inventario/carga_masiva/resultado_ordenes.html', context)
