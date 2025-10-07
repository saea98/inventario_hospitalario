# VISTAS FALTANTES PARA AGREGAR AL FINAL DE views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q


@login_required
def editar_lote(request, pk):
    """Vista para editar un lote"""
    lote = get_object_or_404(Lote, pk=pk)
    
    if request.method == 'POST':
        form = LoteForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lote actualizado exitosamente.')
            return redirect('detalle_lote', pk=lote.pk)
    else:
        form = LoteForm(instance=lote)
    
    return render(request, 'inventario/lotes/form.html', {
        'form': form,
        'lote': lote,
        'titulo': 'Editar Lote'
    })


@login_required
def eliminar_lote(request, pk):
    """Vista para eliminar un lote"""
    lote = get_object_or_404(Lote, pk=pk)
    
    if request.method == 'POST':
        # Verificar si tiene movimientos
        if MovimientoInventario.objects.filter(lote=lote).exists():
            messages.error(request, 'No se puede eliminar el lote porque tiene movimientos asociados.')
            return redirect('detalle_lote', pk=lote.pk)
        
        lote.delete()
        messages.success(request, 'Lote eliminado exitosamente.')
        return redirect('lista_lotes')
    
    return render(request, 'inventario/lotes/confirmar_eliminar.html', {
        'lote': lote
    })


@login_required
def eliminar_producto(request, pk):
    """Vista para eliminar un producto"""
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        # Verificar si tiene lotes asociados
        if Lote.objects.filter(producto=producto).exists():
            messages.error(request, 'No se puede eliminar el producto porque tiene lotes asociados.')
            return redirect('detalle_producto', pk=producto.pk)
        
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect('lista_productos')
    
    return render(request, 'inventario/productos/confirmar_eliminar.html', {
        'producto': producto
    })


@login_required
def crear_movimiento(request):
    """Vista para crear un movimiento de inventario"""
    if request.method == 'POST':
        lote_id = request.POST.get('lote_id')
        tipo_movimiento = request.POST.get('tipo_movimiento')
        cantidad = int(request.POST.get('cantidad', 0))
        motivo = request.POST.get('motivo')
        documento_referencia = request.POST.get('documento_referencia', '')
        
        try:
            lote = Lote.objects.get(pk=lote_id)
            
            # Validar cantidad según tipo de movimiento
            if tipo_movimiento == 'SALIDA' and cantidad > lote.cantidad_disponible:
                messages.error(request, 'No hay suficiente cantidad disponible.')
                return redirect('lista_lotes')
            
            # Calcular nueva cantidad
            cantidad_anterior = lote.cantidad_disponible
            if tipo_movimiento == 'ENTRADA':
                nueva_cantidad = cantidad_anterior + cantidad
            elif tipo_movimiento == 'SALIDA':
                nueva_cantidad = cantidad_anterior - cantidad
            elif tipo_movimiento == 'AJUSTE':
                nueva_cantidad = cantidad  # En ajuste, la cantidad es el nuevo total
            else:  # TRANSFERENCIA
                nueva_cantidad = cantidad_anterior - cantidad
            
            # Validar que la nueva cantidad no sea negativa
            if nueva_cantidad < 0:
                messages.error(request, 'La cantidad resultante no puede ser negativa.')
                return redirect('lista_lotes')
            
            # Crear movimiento
            MovimientoInventario.objects.create(
                lote=lote,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad,
                cantidad_anterior=cantidad_anterior,
                cantidad_nueva=nueva_cantidad,
                motivo=motivo,
                documento_referencia=documento_referencia,
                usuario=request.user
            )
            
            # Actualizar cantidad del lote
            lote.cantidad_disponible = nueva_cantidad
            lote.save()
            
            messages.success(request, 'Movimiento registrado exitosamente.')
            
        except Lote.DoesNotExist:
            messages.error(request, 'Lote no encontrado.')
        except ValueError:
            messages.error(request, 'Cantidad inválida.')
        except Exception as e:
            messages.error(request, f'Error al registrar movimiento: {str(e)}')
    
    return redirect('lista_lotes')


@login_required
def lista_movimientos(request):
    """Vista para listar movimientos de inventario"""
    movimientos = MovimientoInventario.objects.select_related(
        'lote__producto', 'lote__institucion', 'usuario'
    ).order_by('-fecha_movimiento')
    
    # Filtros
    search = request.GET.get('search')
    if search:
        movimientos = movimientos.filter(
            Q(lote__numero_lote__icontains=search) |
            Q(lote__producto__clave_cnis__icontains=search) |
            Q(lote__producto__descripcion__icontains=search) |
            Q(motivo__icontains=search) |
            Q(documento_referencia__icontains=search)
        )
    
    tipo_movimiento = request.GET.get('tipo_movimiento')
    if tipo_movimiento:
        movimientos = movimientos.filter(tipo_movimiento=tipo_movimiento)
    
    institucion_id = request.GET.get('institucion')
    if institucion_id:
        movimientos = movimientos.filter(lote__institucion_id=institucion_id)
    
    # Filtros de fecha
    fecha_desde = request.GET.get('fecha_desde')
    if fecha_desde:
        try:
            from datetime import datetime
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            movimientos = movimientos.filter(fecha_movimiento__date__gte=fecha_desde_obj)
        except ValueError:
            pass
    
    fecha_hasta = request.GET.get('fecha_hasta')
    if fecha_hasta:
        try:
            from datetime import datetime
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            movimientos = movimientos.filter(fecha_movimiento__date__lte=fecha_hasta_obj)
        except ValueError:
            pass
    
    # Paginación
    paginator = Paginator(movimientos, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas para el contexto
    instituciones = Institucion.objects.filter(activa=True).order_by('denominacion')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'tipo_movimiento_selected': tipo_movimiento,
        'institucion_selected': institucion_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'instituciones': instituciones,
        'tipos_movimiento': MovimientoInventario.TIPOS_MOVIMIENTO,
    }
    
    return render(request, 'inventario/movimientos/lista.html', context)


@login_required
@require_http_methods(["POST"])
def marcar_lote_caducado(request, pk):
    """Vista AJAX para marcar un lote como caducado"""
    try:
        lote = Lote.objects.get(pk=pk)
        
        # Cambiar estado a caducado
        lote.estado = 6  # Caducado
        lote.save()
        
        # Crear movimiento de ajuste para registrar la acción
        MovimientoInventario.objects.create(
            lote=lote,
            tipo_movimiento='AJUSTE',
            cantidad=0,
            cantidad_anterior=lote.cantidad_disponible,
            cantidad_nueva=0,
            motivo='Producto marcado como caducado por el sistema',
            usuario=request.user
        )
        
        # Actualizar cantidad disponible a 0
        lote.cantidad_disponible = 0
        lote.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Lote marcado como caducado exitosamente'
        })
        
    except Lote.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Lote no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error al marcar como caducado: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def crear_alerta_lote(request, pk):
    """Vista AJAX para crear una alerta para un lote"""
    try:
        lote = Lote.objects.get(pk=pk)
        
        # Verificar si ya existe una alerta activa para este lote
        alerta_existente = AlertaCaducidad.objects.filter(
            lote=lote,
            activa=True
        ).first()
        
        if alerta_existente:
            return JsonResponse({
                'success': True, 
                'message': 'Ya existe una alerta activa para este lote'
            })
        
        # Crear nueva alerta
        alerta = AlertaCaducidad.objects.create(
            lote=lote,
            fecha_alerta=timezone.now().date(),
            tipo_alerta='CADUCIDAD',
            mensaje=f'Producto próximo a caducar: {lote.producto.descripcion} (Lote: {lote.numero_lote})',
            activa=True,
            creada_por=request.user
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Alerta creada exitosamente',
            'alerta_id': alerta.id
        })
        
    except Lote.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Lote no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error al crear alerta: {str(e)}'
        })
