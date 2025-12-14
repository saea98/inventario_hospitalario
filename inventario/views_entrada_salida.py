"""
Vistas para los módulos ENTRADA AL ALMACÉN y PROVEEDURÍA
Versión mejorada con flujo de selección producto-lotes en PROVEEDURÍA
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import date

from .models import Lote, MovimientoInventario, Producto, Almacen, Institucion
from .forms_entrada_salida import (
    EntradaAlmacenForm,
    ProveeduriaForm,
    ItemEntradaForm,
    ItemSalidaForm
)


# ============================================================
# ENTRADA AL ALMACÉN - PASO 1
# ============================================================

@login_required
def entrada_almacen_paso1(request):
    """Captura información general de la remisión"""
    
    if request.method == 'POST':
        form = EntradaAlmacenForm(request.POST)
        if form.is_valid():
            # Guardar en sesión
            request.session['entrada_data'] = {
                'numero_remision': form.cleaned_data['numero_remision'],
                'fecha_remision': str(form.cleaned_data['fecha_remision']),
                'numero_pedido': form.cleaned_data['numero_pedido'],
                'proveedor_id': form.cleaned_data['proveedor'].id,
                'proveedor': str(form.cleaned_data['proveedor']),
                'rfc_proveedor': form.cleaned_data['rfc_proveedor'],
                'numero_contrato': form.cleaned_data['numero_contrato'],
                'institucion_id': form.cleaned_data['institucion'].id,
                'almacen_id': form.cleaned_data['almacen'].id,
                'observaciones_generales': form.cleaned_data['observaciones_generales'],
            }
            return redirect('entrada_almacen_paso2')
    else:
        form = EntradaAlmacenForm()
    
    return render(request, 'inventario/entrada_almacen/paso1.html', {
        'form': form,
        'titulo': 'ENTRADA AL ALMACÉN - Paso 1'
    })


# ============================================================
# ENTRADA AL ALMACÉN - PASO 2
# ============================================================

@login_required
def entrada_almacen_paso2(request):
    """Captura items de la remisión"""
    
    entrada_data = request.session.get('entrada_data')
    if not entrada_data:
        messages.error(request, 'Sesión expirada. Por favor, comienza de nuevo.')
        return redirect('entrada_almacen_paso1')
    
    if request.method == 'POST':
        items_json = request.POST.get('items_json', '[]')
        try:
            items = json.loads(items_json)
            if not items:
                messages.error(request, 'Debes agregar al menos un item.')
                return redirect('entrada_almacen_paso2')
            
            request.session['entrada_items'] = items
            return redirect('entrada_almacen_confirmacion')
        except json.JSONDecodeError:
            messages.error(request, 'Error al procesar los items.')
    
    # Obtener productos para el dropdown
    productos = Producto.objects.filter(activo=True).values(
        'id', 'clave_cnis', 'descripcion'
    )
    
    almacen = Almacen.objects.get(id=entrada_data['almacen_id'])
    institucion = Institucion.objects.get(id=entrada_data['institucion_id'])
    
    return render(request, 'inventario/entrada_almacen/paso2.html', {
        'titulo': 'ENTRADA AL ALMACÉN - Paso 2',
        'entrada_data': entrada_data,
        'almacen': almacen,
        'institucion': institucion,
        'productos': list(productos)
    })


# ============================================================
# ENTRADA AL ALMACÉN - CONFIRMACIÓN
# ============================================================

@login_required
def entrada_almacen_confirmacion(request):
    """Confirmación y guardado de entrada"""
    
    entrada_data = request.session.get('entrada_data')
    entrada_items = request.session.get('entrada_items', [])
    
    if not entrada_data or not entrada_items:
        messages.error(request, 'Sesión expirada. Por favor, comienza de nuevo.')
        return redirect('entrada_almacen_paso1')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear lotes e items
                for item in entrada_items:
                    # Crear o actualizar lote
                    lote, created = Lote.objects.get_or_create(
                        numero_lote=item['numero_lote'],
                        producto_id=item['producto_id'],
                        institucion_id=entrada_data['institucion_id'],
                        defaults={
                            'almacen_id': entrada_data['almacen_id'],
                            'cantidad_inicial': item['cantidad_recibida'],
                            'cantidad_disponible': item['cantidad_recibida'],
                            'precio_unitario': item['precio_unitario'],
                            'valor_total': item['importe_total'],
                            'fecha_caducidad': item.get('fecha_caducidad'),
                            'fecha_recepcion': date.today(),
                            'estado': 1,
                            'creado_por': request.user,
                        }
                    )
                    
                    if not created:
                        # Actualizar cantidad si ya existe
                        lote.cantidad_disponible += item['cantidad_recibida']
                        lote.save()
                    
                    # Crear movimiento de entrada
                    MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento='ENTRADA',
                        cantidad=item['cantidad_recibida'],
                        cantidad_anterior=0 if created else lote.cantidad_disponible - item['cantidad_recibida'],
                        cantidad_nueva=lote.cantidad_disponible,
                        motivo='Entrada al almacén',
                        documento_referencia=entrada_data['numero_remision'],
                        usuario=request.user,
                    )
                
                # Limpiar sesión
                del request.session['entrada_data']
                del request.session['entrada_items']
                
                messages.success(
                    request,
                    f'Entrada registrada correctamente. Se procesaron {len(entrada_items)} items.'
                )
                return redirect('lista_lotes')
        
        except Exception as e:
            messages.error(request, f'Error al guardar: {str(e)}')
            return redirect('entrada_almacen_paso2')
    
    # Calcular totales
    total_items = len(entrada_items)
    total_cantidad = sum(item['cantidad_recibida'] for item in entrada_items)
    total_importe = sum(item['importe_total'] for item in entrada_items)
    
    return render(request, 'inventario/entrada_almacen/confirmacion.html', {
        'titulo': 'ENTRADA AL ALMACÉN - Confirmación',
        'entrada_data': entrada_data,
        'entrada_items': entrada_items,
        'total_items': total_items,
        'total_cantidad': total_cantidad,
        'total_importe': total_importe,
    })


# ============================================================
# PROVEEDURÍA - PASO 1
# ============================================================

@login_required
def proveeduria_paso1(request):
    """Captura información general de la solicitud"""
    
    if request.method == 'POST':
        form = ProveeduriaForm(request.POST)
        if form.is_valid():
            # Guardar en sesión
            request.session['proveeduria_data'] = {
                'numero_solicitud': form.cleaned_data['numero_solicitud'],
                'fecha_solicitud': str(form.cleaned_data['fecha_solicitud']),
                'responsable_solicitud': form.cleaned_data['responsable_solicitud'],
                'institucion_origen_id': form.cleaned_data['institucion_origen'].id,
                'almacen_origen_id': form.cleaned_data['almacen_origen'].id,
                'area_destino': form.cleaned_data['area_destino'],
                'observaciones_generales': form.cleaned_data['observaciones_generales'],
            }
            return redirect('proveeduria_paso2')
    else:
        form = ProveeduriaForm()
    
    return render(request, 'inventario/proveeduria/paso1.html', {
        'form': form,
        'titulo': 'Salidas de almacen - Paso 1'
    })


# ============================================================
# PROVEEDURÍA - PASO 2 (MEJORADO)
# ============================================================

@login_required
def proveeduria_paso2(request):
    """Captura items de salida - Flujo: Producto → Lotes disponibles"""
    
    proveeduria_data = request.session.get('proveeduria_data')
    if not proveeduria_data:
        messages.error(request, 'Sesión expirada. Por favor, comienza de nuevo.')
        return redirect('proveeduria_paso1')
    
    if request.method == 'POST':
        items_json = request.POST.get('items_json', '[]')
        try:
            items = json.loads(items_json)
            if not items:
                messages.error(request, 'Debes agregar al menos un item.')
                return redirect('proveeduria_paso2')
            
            request.session['proveeduria_items'] = items
            return redirect('proveeduria_confirmacion')
        except json.JSONDecodeError:
            messages.error(request, 'Error al procesar los items.')
    
    # Obtener productos que tienen lotes disponibles en el almacén
    almacen_id = proveeduria_data['almacen_origen_id']
    
    productos_con_lotes = Producto.objects.filter(
        activo=True,
        lote__almacen_id=almacen_id,
        lote__cantidad_disponible__gt=0,
        lote__estado=1
    ).distinct().values('id', 'clave_cnis', 'descripcion')
    
    almacen = Almacen.objects.get(id=almacen_id)
    
    return render(request, 'inventario/proveeduria/paso2.html', {
        'titulo': 'Salidas de almacen - Paso 2',
        'proveeduria_data': proveeduria_data,
        'almacen': almacen,
        'productos': list(productos_con_lotes),
    })


# ============================================================
# PROVEEDURÍA - CONFIRMACIÓN
# ============================================================

@login_required
def proveeduria_confirmacion(request):
    """Confirmación y guardado de salida"""
    
    proveeduria_data = request.session.get('proveeduria_data')
    proveeduria_items = request.session.get('proveeduria_items', [])
    
    if not proveeduria_data or not proveeduria_items:
        messages.error(request, 'Sesión expirada. Por favor, comienza de nuevo.')
        return redirect('proveeduria_paso1')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear movimientos de salida
                for item in proveeduria_items:
                    lote = Lote.objects.get(id=item['lote_id'])
                    
                    # Validar disponibilidad
                    if lote.cantidad_disponible < item['cantidad_salida']:
                        raise ValueError(
                            f"Cantidad insuficiente en lote {lote.numero_lote}"
                        )
                    
                    # Actualizar cantidad disponible
                    cantidad_anterior = lote.cantidad_disponible
                    lote.cantidad_disponible -= item['cantidad_salida']
                    lote.save()
                    
                    # Crear movimiento
                    MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento='SALIDA',
                        cantidad=item['cantidad_salida'],
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=lote.cantidad_disponible,
                        motivo=item['motivo_salida'],
                        documento_referencia=proveeduria_data['numero_solicitud'],
                        usuario=request.user,
                    )
                
                # Limpiar sesión
                del request.session['proveeduria_data']
                del request.session['proveeduria_items']
                
                messages.success(
                    request,
                    f'Salida registrada correctamente. Se procesaron {len(proveeduria_items)} items.'
                )
                return redirect('lista_movimientos')
        
        except Exception as e:
            messages.error(request, f'Error al guardar: {str(e)}')
            return redirect('proveeduria_paso2')
    
    # Calcular totales
    total_items = len(proveeduria_items)
    total_cantidad = sum(item['cantidad_salida'] for item in proveeduria_items)
    
    return render(request, 'inventario/proveeduria/confirmacion.html', {
        'titulo': 'Salidas de alamcen - Confirmación',
        'proveeduria_data': proveeduria_data,
        'proveeduria_items': proveeduria_items,
        'total_items': total_items,
        'total_cantidad': total_cantidad,
    })


# ============================================================
# ENDPOINTS AJAX
# ============================================================

@login_required
@require_http_methods(["GET"])
def validar_producto_entrada(request):
    """Valida disponibilidad de producto"""
    producto_id = request.GET.get('producto_id')
    
    if not producto_id:
        return JsonResponse({'error': 'Producto no especificado'}, status=400)
    
    try:
        producto = Producto.objects.get(id=producto_id)
        return JsonResponse({
            'id': producto.id,
            'clave_cnis': producto.clave_cnis,
            'descripcion': producto.descripcion,
            'unidad_medida': producto.unidad_medida,
        })
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)


@login_required
@require_http_methods(["GET"])
def validar_lote_proveeduria(request):
    """Valida disponibilidad de lote"""
    lote_id = request.GET.get('lote_id')
    
    if not lote_id:
        return JsonResponse({'error': 'Lote no especificado'}, status=400)
    
    try:
        lote = Lote.objects.get(id=lote_id)
        return JsonResponse({
            'id': lote.id,
            'numero_lote': lote.numero_lote,
            'cantidad_disponible': lote.cantidad_disponible,
            'fecha_caducidad': lote.fecha_caducidad.isoformat() if lote.fecha_caducidad else None,
            'precio_unitario': float(lote.precio_unitario),
            'producto_descripcion': lote.producto.descripcion if lote.producto else '',
        })
    except Lote.DoesNotExist:
        return JsonResponse({'error': 'Lote no encontrado'}, status=404)


# ============================================================
# FUNCIONES AJAX PARA PROVEEDURÍA MEJORADA
# ============================================================

@login_required
@require_http_methods(["GET"])
def obtener_lotes_por_producto(request):
    """
    Obtiene lotes disponibles de un producto específico
    Ordenados por fecha de caducidad (más próximos a caducar primero)
    """
    producto_id = request.GET.get('producto_id')
    almacen_id = request.GET.get('almacen_id')
    
    if not producto_id or not almacen_id:
        return JsonResponse({'error': 'Producto y almacén requeridos'}, status=400)
    
    try:
        # Obtener lotes del producto en el almacén, ordenados por fecha de caducidad
        lotes_queryset = Lote.objects.filter(
            producto_id=producto_id,
            almacen_id=almacen_id,
            cantidad_disponible__gt=0,
            estado=1  # Disponible
        ).select_related('producto').order_by('fecha_caducidad')
        
        lotes = []
        for lote in lotes_queryset:
            # Calcular días para caducidad
            dias_caducidad = None
            if lote.fecha_caducidad:
                delta = lote.fecha_caducidad - date.today()
                dias_caducidad = delta.days
            
            lotes.append({
                'id': lote.id,
                'numero_lote': lote.numero_lote,
                'cantidad_disponible': lote.cantidad_disponible,
                'fecha_caducidad': lote.fecha_caducidad.isoformat() if lote.fecha_caducidad else None,
                'dias_caducidad': dias_caducidad,
                'precio_unitario': float(lote.precio_unitario),
                'producto__descripcion': lote.producto.descripcion if lote.producto else '',
            })
        
        return JsonResponse({'lotes': lotes})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def obtener_lotes_disponibles(request):
    """Obtiene lotes disponibles de un almacén"""
    almacen_id = request.GET.get('almacen_id')
    
    if not almacen_id:
        return JsonResponse({'error': 'Almacén no especificado'}, status=400)
    
    try:
        lotes_queryset = Lote.objects.filter(
            almacen_id=almacen_id,
            cantidad_disponible__gt=0,
            estado=1
        ).select_related('producto')
        
        lotes = []
        for lote in lotes_queryset:
            lotes.append({
                'id': lote.id,
                'numero_lote': lote.numero_lote,
                'cantidad_disponible': lote.cantidad_disponible,
                'fecha_caducidad': lote.fecha_caducidad.isoformat() if lote.fecha_caducidad else None,
                'precio_unitario': float(lote.precio_unitario),
                'producto__descripcion': lote.producto.descripcion if lote.producto else '',
            })
        
        return JsonResponse({'lotes': lotes})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def obtener_detalles_lote(request):
    """Obtiene detalles de un lote específico"""
    lote_id = request.GET.get('lote_id')
    
    if not lote_id:
        return JsonResponse({'error': 'Lote no especificado'}, status=400)
    
    try:
        lote = Lote.objects.select_related('producto').get(id=lote_id)
        return JsonResponse({
            'id': lote.id,
            'numero_lote': lote.numero_lote,
            'cantidad_disponible': lote.cantidad_disponible,
            'fecha_caducidad': lote.fecha_caducidad.isoformat() if lote.fecha_caducidad else None,
            'precio_unitario': float(lote.precio_unitario),
            'producto_id': lote.producto.id if lote.producto else None,
            'producto_descripcion': lote.producto.descripcion if lote.producto else '',
            'producto_clave_cnis': lote.producto.clave_cnis if lote.producto else '',
        })
    except Lote.DoesNotExist:
        return JsonResponse({'error': 'Lote no encontrado'}, status=404)


@login_required
@require_http_methods(["POST"])
def validar_item_entrada(request):
    """Valida un item de entrada"""
    try:
        data = json.loads(request.body)
        producto_id = data.get('producto_id')
        cantidad = data.get('cantidad')
        
        if not producto_id or not cantidad:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        try:
            producto = Producto.objects.get(id=producto_id)
            return JsonResponse({
                'valido': True,
                'producto_id': producto.id,
                'clave_cnis': producto.clave_cnis,
                'descripcion': producto.descripcion,
                'unidad_medida': producto.unidad_medida,
            })
        except Producto.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
