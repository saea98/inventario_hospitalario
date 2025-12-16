"""
Vistas para Conteo Físico - Validación de Existencias

Basado en el formato IMSS-Bienestar que captura tres conteos:
1. Primer Conteo (validación inicial)
2. Segundo Conteo (validación de diferencias)
3. Tercer Conteo (valor definitivo que se usa como nueva existencia)

Flujo:
1. Buscar lote por CLAVE (CNIS) en inventario_lote
2. Si existe: Cargar datos del sistema
3. Si NO existe: Opción de crear nuevo lote
4. Capturar los tres conteos
5. Usar TERCER CONTEO como cantidad_nueva
6. Crear MovimientoInventario con la diferencia
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

from .models import (
    Lote, Producto, Almacen, UbicacionAlmacen, 
    MovimientoInventario, Institucion
)
from .forms_conteo_fisico import (
    BuscarLoteForm, CapturarConteosForm, 
    CrearLoteManualForm, FiltroConteosForm
)
from .servicios_notificaciones import notificaciones


@login_required
def buscar_lote_conteo(request):
    """
    Vista para buscar un lote por CLAVE (CNIS).
    
    GET: Mostrar formulario de búsqueda
    POST: Buscar lote y redirigir a captura de conteos
    """
    
    institucion = request.user.institucion if hasattr(request.user, 'institucion') else None
    form = BuscarLoteForm(institucion=institucion)
    lote_encontrado = None
    error = None
    
    if request.method == 'POST':
        form = BuscarLoteForm(request.POST, institucion=institucion)
        
        if form.is_valid():
            clave_cnis = form.cleaned_data['clave_cnis'].strip()
            almacen = form.cleaned_data['almacen']
            
            # Buscar lote por CLAVE en el almacén seleccionado
            try:
                lote = Lote.objects.get(
                    producto__clave_cnis=clave_cnis,
                    almacen=almacen
                )
                
                # Redirigir a captura de conteos
                return redirect(
                    'logistica:capturar_conteo_lote',
                    lote_id=lote.id
                )
                
            except Lote.DoesNotExist:
                # Lote no encontrado - Ofrecer opción de crear
                error = f"No se encontró lote con CLAVE: {clave_cnis}"
                
                # Guardar datos en sesión para crear nuevo lote
                request.session['clave_cnis_busqueda'] = clave_cnis
                request.session['almacen_id_busqueda'] = almacen.id
                
                return redirect('logistica:crear_lote_conteo')
            
            except Lote.MultipleObjectsReturned:
                # Múltiples lotes encontrados - Mostrar lista
                lotes = Lote.objects.filter(
                    producto__clave_cnis=clave_cnis,
                    almacen=almacen
                )
                
                return render(request, 'inventario/conteo_fisico/lista.html', {
                    'lotes': lotes,
                    'clave_cnis': clave_cnis,
                    'almacen': almacen
                })
    
    return render(request, 'inventario/conteo_fisico/buscar_lote.html', {
        'form': form,
        'error': error
    })


@login_required
def capturar_conteo_lote(request, lote_id):
    """
    Vista para capturar los tres conteos de un lote específico.
    
    Muestra:
    - Datos del lote (cantidad sistema, precio, etc.)
    - Campos para los tres conteos
    - Cálculos automáticos de diferencias
    
    POST: Guardar conteos y crear MovimientoInventario
    """
    
    lote = get_object_or_404(Lote, id=lote_id)
    producto = lote.producto
    
    if request.method == 'POST':
        form = CapturarConteosForm(request.POST)
        
        if form.is_valid():
            cifra_primer_conteo = form.cleaned_data['cifra_primer_conteo']
            cifra_segundo_conteo = form.cleaned_data.get('cifra_segundo_conteo') or 0
            tercer_conteo = form.cleaned_data['tercer_conteo']  # VALOR DEFINITIVO
            observaciones = form.cleaned_data.get('observaciones', '')
            
            try:
                with transaction.atomic():
                    # Calcular diferencia usando TERCER CONTEO
                    cantidad_anterior = lote.cantidad_disponible
                    cantidad_nueva = tercer_conteo
                    diferencia = cantidad_nueva - cantidad_anterior
                    
                    # Crear MovimientoInventario
                    movimiento = MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento='AJUSTE_CONTEO',
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=cantidad_nueva,
                        diferencia=diferencia,
                        usuario_creacion=request.user,
                        observaciones=f"""Conteo Físico:
- Primer Conteo: {cifra_primer_conteo}
- Segundo Conteo: {cifra_segundo_conteo if cifra_segundo_conteo > 0 else 'No capturado'}
- Tercer Conteo (Definitivo): {tercer_conteo}
- Diferencia: {diferencia:+d}
{f'- Observaciones: {observaciones}' if observaciones else ''}"""
                    )
                    
                    # Actualizar cantidad disponible en el lote
                    lote.cantidad_disponible = cantidad_nueva
                    lote.valor_total = cantidad_nueva * (lote.precio_unitario or 0)
                    lote.save()
                    
                    # Notificar
                    try:
                        notificaciones.notificar_conteo_completado(
                            lote=lote,
                            usuario=request.user,
                            diferencia=diferencia
                        )
                    except Exception as e:
                        print(f"Error al notificar: {e}")
                    
                    messages.success(
                        request,
                        f'✓ Conteo registrado exitosamente. '
                        f'Diferencia: {diferencia:+d} unidades. '
                        f'Folio: {movimiento.folio}'
                    )
                    
                    return redirect(
                        'logistica:detalle_movimiento_conteo',
                        movimiento_id=movimiento.id
                    )
                    
            except Exception as e:
                messages.error(request, f'Error al guardar conteo: {str(e)}')
    else:
        form = CapturarConteosForm()
    
    # Calcular valores para mostrar
    contexto = {
        'lote': lote,
        'producto': producto,
        'form': form,
        'cantidad_sistema': lote.cantidad_disponible,
        'precio_unitario': lote.precio_unitario or 0,
        'valor_sistema': (lote.cantidad_disponible or 0) * (lote.precio_unitario or 0),
    }
    
    return render(request, 'inventario/conteo_fisico/capturar_conteo.html', contexto)


@login_required
def crear_lote_conteo(request):
    """
    Vista para crear un nuevo lote si no existe en el sistema.
    
    Se utiliza cuando la búsqueda por CLAVE no encuentra resultados.
    """
    
    clave_cnis = request.session.get('clave_cnis_busqueda')
    almacen_id = request.session.get('almacen_id_busqueda')
    
    if not clave_cnis or not almacen_id:
        messages.error(request, 'Datos de búsqueda no disponibles')
        return redirect('logistica:buscar_lote_conteo')
    
    almacen = get_object_or_404(Almacen, id=almacen_id)
    
    # Buscar o crear producto por CLAVE
    try:
        producto = Producto.objects.get(clave_cnis=clave_cnis)
    except Producto.DoesNotExist:
        # Crear producto con CLAVE
        producto = Producto.objects.create(
            clave_cnis=clave_cnis,
            nombre=f"Producto {clave_cnis}",
            descripcion="Creado automáticamente durante conteo físico"
        )
    
    if request.method == 'POST':
        form = CrearLoteManualForm(request.POST)
        
        if form.is_valid():
            lote = form.save(commit=False)
            lote.producto = producto
            lote.almacen = almacen
            lote.save()
            
            messages.success(request, f'Lote {lote.numero_lote} creado exitosamente')
            
            # Limpiar sesión
            del request.session['clave_cnis_busqueda']
            del request.session['almacen_id_busqueda']
            
            # Redirigir a captura de conteos
            return redirect(
                'logistica:capturar_conteo_lote',
                lote_id=lote.id
            )
    else:
        form = CrearLoteManualForm()
    
    return render(request, 'inventario/conteo_fisico/crear.html', {
        'form': form,
        'clave_cnis': clave_cnis,
        'almacen': almacen,
        'producto': producto
    })


@login_required
def historial_conteos(request):
    """
    Vista para ver el historial de conteos realizados.
    
    Muestra:
    - Lista de movimientos de tipo AJUSTE_CONTEO
    - Filtros por almacén, fecha, búsqueda
    - Estadísticas de conteos
    """
    
    institucion = request.user.institucion if hasattr(request.user, 'institucion') else None
    
    # Obtener movimientos de conteo
    movimientos = MovimientoInventario.objects.filter(
        tipo_movimiento='AJUSTE_CONTEO'
    ).select_related('lote', 'lote__producto', 'lote__almacen', 'usuario_creacion')
    
    if institucion:
        movimientos = movimientos.filter(lote__almacen__institucion=institucion)
    
    # Aplicar filtros
    form = FiltroConteosForm(institucion=institucion)
    
    if request.method == 'GET':
        almacen_id = request.GET.get('almacen')
        busqueda = request.GET.get('busqueda')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if almacen_id:
            movimientos = movimientos.filter(lote__almacen_id=almacen_id)
        
        if busqueda:
            movimientos = movimientos.filter(
                Q(lote__producto__clave_cnis__icontains=busqueda) |
                Q(lote__numero_lote__icontains=busqueda) |
                Q(folio__icontains=busqueda)
            )
        
        if fecha_desde:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            movimientos = movimientos.filter(fecha_creacion__date__gte=fecha_desde_obj)
        
        if fecha_hasta:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            movimientos = movimientos.filter(fecha_creacion__date__lte=fecha_hasta_obj)
    
    # Ordenar por fecha descendente
    movimientos = movimientos.order_by('-fecha_creacion')
    
    # Estadísticas
    total_conteos = movimientos.count()
    total_diferencias = sum(abs(m.diferencia) for m in movimientos)
    conteos_con_diferencia = movimientos.exclude(diferencia=0).count()
    
    contexto = {
        'movimientos': movimientos,
        'form': form,
        'estadisticas': {
            'total': total_conteos,
            'con_diferencia': conteos_con_diferencia,
            'total_diferencias': total_diferencias,
        }
    }
    
    return render(request, 'inventario/conteo_fisico/historial_conteos.html', contexto)


@login_required
def detalle_movimiento_conteo(request, movimiento_id):
    """
    Vista para ver el detalle de un movimiento de conteo.
    
    Muestra:
    - Información del lote y producto
    - Los tres conteos capturados
    - Diferencias calculadas
    - Importes
    """
    
    movimiento = get_object_or_404(MovimientoInventario, id=movimiento_id)
    lote = movimiento.lote
    producto = lote.producto
    
    # Calcular importes
    importe_anterior = (movimiento.cantidad_anterior or 0) * (lote.precio_unitario or 0)
    importe_nueva = (movimiento.cantidad_nueva or 0) * (lote.precio_unitario or 0)
    importe_diferencia = (movimiento.diferencia or 0) * (lote.precio_unitario or 0)
    
    contexto = {
        'movimiento': movimiento,
        'lote': lote,
        'producto': producto,
        'importe_anterior': importe_anterior,
        'importe_nueva': importe_nueva,
        'importe_diferencia': importe_diferencia,
    }
    
    return render(request, 'inventario/conteo_fisico/detalle_movimiento.html', contexto)


@login_required
def api_obtener_lote_info(request):
    """
    API AJAX para obtener información de un lote por CLAVE.
    
    Retorna JSON con:
    - Información del lote
    - Cantidad sistema
    - Precio unitario
    - Valor total
    """
    
    clave_cnis = request.GET.get('clave_cnis', '').strip()
    almacen_id = request.GET.get('almacen_id')
    
    if not clave_cnis or not almacen_id:
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
    
    try:
        lote = Lote.objects.get(
            producto__clave_cnis=clave_cnis,
            almacen_id=almacen_id
        )
        
        return JsonResponse({
            'encontrado': True,
            'lote_id': lote.id,
            'numero_lote': lote.numero_lote,
            'cantidad_sistema': lote.cantidad_disponible,
            'precio_unitario': float(lote.precio_unitario or 0),
            'valor_total': float(lote.valor_total or 0),
            'fecha_caducidad': lote.fecha_caducidad.isoformat() if lote.fecha_caducidad else None,
            'ubicacion': str(lote.ubicacion) if lote.ubicacion else 'No especificada',
        })
        
    except Lote.DoesNotExist:
        return JsonResponse({'encontrado': False})
    
    except Lote.MultipleObjectsReturned:
        lotes = Lote.objects.filter(
            producto__clave_cnis=clave_cnis,
            almacen_id=almacen_id
        ).values('id', 'numero_lote', 'cantidad_disponible')
        
        return JsonResponse({
            'encontrado': False,
            'multiples': True,
            'lotes': list(lotes)
        })
