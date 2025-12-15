"""
Vistas Completas para Órdenes de Traslado
Incluye: CRUD, asignación de logística, cambios de estado y notificaciones
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

from .models import (
    OrdenTraslado, ItemTraslado, Almacen, Lote, 
    UbicacionAlmacen, MovimientoInventario, Folio, TipoEntrega
)
from .forms import OrdenTrasladoForm, LogisticaTrasladoForm
from .servicios_notificaciones import notificaciones


# ============================================================================
# VISTAS PARA ÓRDENES DE TRASLADO
# ============================================================================

@login_required
def lista_traslados(request):
    """Lista todas las órdenes de traslado con filtros"""
    traslados = OrdenTraslado.objects.all().order_by('-fecha_creacion')
    
    # Filtros
    estado = request.GET.get('estado')
    almacen_origen = request.GET.get('almacen_origen')
    busqueda = request.GET.get('busqueda')
    
    if estado:
        traslados = traslados.filter(estado=estado)
    
    if almacen_origen:
        traslados = traslados.filter(almacen_origen__id=almacen_origen)
    
    if busqueda:
        traslados = traslados.filter(
            Q(folio__icontains=busqueda) |
            Q(almacen_origen__nombre__icontains=busqueda) |
            Q(almacen_destino__nombre__icontains=busqueda)
        )
    
    # Contar por estado
    estados_count = {
        'creada': OrdenTraslado.objects.filter(estado='creada').count(),
        'logistica_asignada': OrdenTraslado.objects.filter(estado='logistica_asignada').count(),
        'en_transito': OrdenTraslado.objects.filter(estado='en_transito').count(),
        'recibida': OrdenTraslado.objects.filter(estado='recibida').count(),
        'completada': OrdenTraslado.objects.filter(estado='completada').count(),
    }
    
    almacenes = Almacen.objects.all()
    
    context = {
        'traslados': traslados,
        'estados': OrdenTraslado.ESTADOS_TRASLADO,
        'almacenes': almacenes,
        'estados_count': estados_count,
        'estado_seleccionado': estado,
        'almacen_seleccionado': almacen_origen,
        'busqueda': busqueda,
    }
    return render(request, 'inventario/traslados/lista.html', context)


@login_required
def crear_traslado(request):
    """Crear una nueva orden de traslado"""
    if request.method == 'POST':
        form = OrdenTrasladoForm(request.POST)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.usuario_creacion = request.user
            
            # Generar folio automáticamente
            try:
                tipo_entrega = TipoEntrega.objects.get(codigo='TRA')
                folio_obj = Folio.objects.get(tipo_entrega=tipo_entrega)
                orden.folio = folio_obj.generar_folio()
            except:
                orden.folio = f"TRA-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            orden.save()
            
            # Registrar movimiento
            MovimientoInventario.objects.create(
                tipo='traslado',
                descripcion=f'Orden de traslado creada: {orden.folio}',
                usuario=request.user,
                referencia_externa=orden.folio
            )
            
            messages.success(request, f'✓ Orden de traslado creada: {orden.folio}')
            return redirect('logistica:detalle_traslado', pk=orden.pk)
        else:
            messages.error(request, 'Error al crear la orden. Verifica los datos.')
    else:
        form = OrdenTrasladoForm()
    
    return render(request, 'inventario/traslados/crear.html', {'form': form})


@login_required
def detalle_traslado(request, pk):
    """Ver detalles completos de una orden de traslado"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    items = orden.items.all()
    
    # Calcular totales
    total_items = items.count()
    total_cantidad = sum(item.cantidad for item in items)
    
    context = {
        'orden': orden,
        'items': items,
        'total_items': total_items,
        'total_cantidad': total_cantidad,
        'puede_asignar_logistica': orden.estado == 'creada',
        'puede_iniciar_transito': orden.estado == 'logistica_asignada',
        'puede_confirmar_recepcion': orden.estado == 'en_transito',
        'puede_completar': orden.estado == 'recibida',
    }
    return render(request, 'inventario/traslados/detalle.html', context)


@login_required
def editar_traslado(request, pk):
    """Editar una orden de traslado (solo en estado creada)"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    
    if orden.estado != 'creada':
        messages.warning(request, 'Solo se pueden editar órdenes en estado "Creada"')
        return redirect('logistica:detalle_traslado', pk=pk)
    
    if request.method == 'POST':
        form = OrdenTrasladoForm(request.POST, instance=orden)
        if form.is_valid():
            orden = form.save()
            
            # Registrar movimiento
            MovimientoInventario.objects.create(
                tipo='traslado',
                descripcion=f'Orden de traslado editada: {orden.folio}',
                usuario=request.user,
                referencia_externa=orden.folio
            )
            
            messages.success(request, '✓ Orden de traslado actualizada')
            return redirect('logistica:detalle_traslado', pk=orden.pk)
    else:
        form = OrdenTrasladoForm(instance=orden)
    
    return render(request, 'inventario/traslados/editar.html', {
        'form': form,
        'orden': orden
    })


@login_required
def asignar_logistica_traslado(request, pk):
    """Asignar vehículo, chofer y ruta a una orden de traslado"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    
    if orden.estado != 'creada':
        messages.warning(request, 'Solo se puede asignar logística a órdenes en estado "Creada"')
        return redirect('logistica:detalle_traslado', pk=pk)
    
    if request.method == 'POST':
        form = LogisticaTrasladoForm(request.POST, instance=orden)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.estado = 'logistica_asignada'
            orden.save()
            
            # Registrar movimiento
            MovimientoInventario.objects.create(
                tipo='traslado',
                descripcion=f'Logística asignada a traslado: {orden.folio} - Vehículo: {orden.placa_vehiculo}',
                usuario=request.user,
                referencia_externa=orden.folio
            )
            
            # Enviar notificación
            notificaciones.notificar_traslado_logistica_asignada(orden)
            
            messages.success(request, '✓ Logística asignada exitosamente')
            return redirect('logistica:detalle_traslado', pk=orden.pk)
    else:
        form = LogisticaTrasladoForm(instance=orden)
    
    return render(request, 'inventario/traslados/asignar_logistica.html', {
        'form': form,
        'orden': orden
    })


@login_required
def iniciar_transito_traslado(request, pk):
    """Marcar una orden como en tránsito"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    
    if orden.estado != 'logistica_asignada':
        messages.warning(request, 'Solo se pueden iniciar traslados con logística asignada')
        return redirect('logistica:detalle_traslado', pk=pk)
    
    if request.method == 'POST':
        orden.estado = 'en_transito'
        orden.fecha_inicio_transito = timezone.now()
        orden.save()
        
        # Registrar movimiento
        MovimientoInventario.objects.create(
            tipo='traslado',
            descripcion=f'Traslado iniciado: {orden.folio}',
            usuario=request.user,
            referencia_externa=orden.folio
        )
        
        # Enviar notificación
        notificaciones.notificar_traslado_iniciado(orden)
        
        messages.success(request, '✓ Traslado marcado como "En Tránsito"')
        return redirect('logistica:detalle_traslado', pk=orden.pk)
    
    return render(request, 'inventario/traslados/iniciar_transito.html', {'orden': orden})


@login_required
def confirmar_recepcion_traslado(request, pk):
    """Confirmar recepción de una orden en tránsito"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    
    if orden.estado != 'en_transito':
        messages.warning(request, 'Solo se pueden confirmar traslados "En Tránsito"')
        return redirect('logistica:detalle_traslado', pk=pk)
    
    if request.method == 'POST':
        orden.estado = 'recibida'
        orden.fecha_recepcion = timezone.now()
        orden.usuario_recepcion = request.user
        orden.save()
        
        # Registrar movimiento
        MovimientoInventario.objects.create(
            tipo='traslado',
            descripcion=f'Traslado recibido: {orden.folio}',
            usuario=request.user,
            referencia_externa=orden.folio
        )
        
        # Enviar notificación
        notificaciones.notificar_traslado_recibido(orden)
        
        messages.success(request, '✓ Traslado confirmado como "Recibido"')
        return redirect('logistica:detalle_traslado', pk=orden.pk)
    
    return render(request, 'inventario/traslados/confirmar_recepcion.html', {'orden': orden})


@login_required
def completar_traslado(request, pk):
    """Completar una orden de traslado"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    
    if orden.estado != 'recibida':
        messages.warning(request, 'Solo se pueden completar traslados "Recibidos"')
        return redirect('logistica:detalle_traslado', pk=pk)
    
    if request.method == 'POST':
        orden.estado = 'completada'
        orden.fecha_completacion = timezone.now()
        orden.usuario_completacion = request.user
        orden.save()
        
        # Actualizar ubicaciones de los lotes trasladados
        for item in orden.items.all():
            item.lote.ubicacion = item.ubicacion_destino
            item.lote.save()
            
            # Registrar movimiento de actualización de ubicación
            MovimientoInventario.objects.create(
                tipo='traslado',
                descripcion=f'Ubicación actualizada por traslado: {orden.folio}',
                lote=item.lote,
                usuario=request.user,
                referencia_externa=orden.folio
            )
        
        # Registrar movimiento
        MovimientoInventario.objects.create(
            tipo='traslado',
            descripcion=f'Traslado completado: {orden.folio}',
            usuario=request.user,
            referencia_externa=orden.folio
        )
        
        # Enviar notificación
        notificaciones.notificar_traslado_completado(orden)
        
        messages.success(request, '✓ Traslado completado exitosamente')
        return redirect('logistica:detalle_traslado', pk=orden.pk)
    
    return render(request, 'inventario/traslados/completar.html', {'orden': orden})


@login_required
def cancelar_traslado(request, pk):
    """Cancelar una orden de traslado"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    
    # Solo se pueden cancelar órdenes en estado creada o logística asignada
    if orden.estado not in ['creada', 'logistica_asignada']:
        messages.warning(request, 'No se puede cancelar un traslado en este estado')
        return redirect('logistica:detalle_traslado', pk=pk)
    
    if request.method == 'POST':
        razon_cancelacion = request.POST.get('razon_cancelacion', '')
        orden.estado = 'cancelada'
        orden.razon_cancelacion = razon_cancelacion
        orden.save()
        
        # Registrar movimiento
        MovimientoInventario.objects.create(
            tipo='traslado',
            descripcion=f'Traslado cancelado: {orden.folio} - Razón: {razon_cancelacion}',
            usuario=request.user,
            referencia_externa=orden.folio
        )
        
        # Enviar notificación
        notificaciones.notificar_traslado_cancelado(orden)
        
        messages.success(request, '✓ Traslado cancelado')
        return redirect('logistica:lista_traslados')
    
    return render(request, 'inventario/traslados/cancelar.html', {'orden': orden})
