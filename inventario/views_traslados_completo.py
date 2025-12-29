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
import logging

from .models import (
    OrdenTraslado, ItemTraslado, Almacen, Lote, 
    UbicacionAlmacen, MovimientoInventario, Folio, TipoEntrega
)
from .forms import OrdenTrasladoForm, LogisticaTrasladoForm
from .servicios_notificaciones import notificaciones

logger = logging.getLogger(__name__)


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
        orden.fecha_salida = timezone.now()
        orden.save()
        
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
        orden.fecha_llegada_real = timezone.now()
        orden.save()
        
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
        orden.save()
        
        # Registrar movimientos de traslado completado
        for item in orden.items.all():
            if item.cantidad_recibida > 0:
                MovimientoInventario.objects.create(
                    lote=item.lote,
                    tipo_movimiento='Salida por Traslado',
                    cantidad_anterior=item.lote.cantidad_disponible,
                    cantidad=item.cantidad_recibida,
                    cantidad_nueva=max(0, item.lote.cantidad_disponible - item.cantidad_recibida),
                    motivo=f'Traslado completado: {orden.folio}',
                    folio=orden.folio,
                    usuario=request.user,
                    documento_referencia=orden.folio,
                    institucion_destino=orden.almacen_destino.institucion
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
        orden.estado = 'cancelada'
        orden.save()
        
        # Enviar notificación
        notificaciones.notificar_traslado_cancelado(orden)
        
        messages.success(request, '✓ Traslado cancelado')
        return redirect('logistica:lista_traslados')
    
    return render(request, 'inventario/traslados/cancelar.html', {'orden': orden})



# ============================================================================
# VISTAS PARA ITEMS DE TRASLADO
# ============================================================================

@login_required
def agregar_item_traslado(request, pk):
    """Agregar un item a una orden de traslado"""
    from .forms import ItemTrasladoForm
    
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    
    # Solo se pueden agregar items en estado creada
    if orden.estado != 'creada':
        messages.warning(request, 'Solo se pueden agregar items a traslados en estado "Creada"')
        return redirect('logistica:detalle_traslado', pk=pk)
    
    if request.method == 'POST':
        form = ItemTrasladoForm(request.POST, almacen_origen=orden.almacen_origen)
        if form.is_valid():
            item = form.save(commit=False)
            item.orden_traslado = orden
            item.save()
            
            messages.success(request, f'✓ Item agregado: {item.lote.numero_lote} - {item.cantidad} unidades')
            return redirect('logistica:detalle_traslado', pk=orden.pk)
    else:
        form = ItemTrasladoForm(almacen_origen=orden.almacen_origen)
    
    return render(request, 'inventario/traslados/agregar_item.html', {
        'form': form,
        'orden': orden
    })


@login_required
def eliminar_item_traslado(request, pk, item_id):
    """Eliminar un item de una orden de traslado"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    item = get_object_or_404(ItemTraslado, id=item_id, orden_traslado=orden)
    
    # Solo se pueden eliminar items en estado creada
    if orden.estado != 'creada':
        messages.warning(request, 'Solo se pueden eliminar items de traslados en estado "Creada"')
        return redirect('logistica:detalle_traslado', pk=pk)
    
    if request.method == 'POST':
        numero_lote = item.lote.numero_lote
        cantidad = item.cantidad
        item.delete()
        
        messages.success(request, f'✓ Item eliminado: {numero_lote} - {cantidad} unidades')
        return redirect('logistica:detalle_traslado', pk=orden.pk)
    
    return render(request, 'inventario/traslados/confirmar_eliminar_item.html', {
        'orden': orden,
        'item': item
    })


@login_required
def validar_llegada_traslado(request, pk):
    """Validar la llegada de items en un traslado"""
    from .forms import ValidarItemTrasladoForm
    
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    
    # Solo se pueden validar traslados en tránsito
    if orden.estado != 'en_transito':
        messages.warning(request, 'Solo se pueden validar traslados "En Tránsito"')
        return redirect('logistica:detalle_traslado', pk=pk)
    
    items = orden.items.all()
    
    if request.method == 'POST':
        # Procesar validación de todos los items
        todos_validados = True
        
        for item in items:
            cantidad_recibida = request.POST.get(f'item_{item.id}_cantidad_recibida')
            
            if cantidad_recibida is not None:
                try:
                    cantidad_recibida = int(cantidad_recibida)
                    
                    if cantidad_recibida > item.cantidad:
                        messages.error(request, f'La cantidad recibida para {item.lote.numero_lote} no puede ser mayor a {item.cantidad}')
                        todos_validados = False
                    else:
                        item.cantidad_recibida = cantidad_recibida
                        item.estado = 'recibido'
                        item.save()
                        
                        # Si la cantidad recibida es menor, registrar discrepancia
                        if cantidad_recibida < item.cantidad:
                            diferencia = item.cantidad - cantidad_recibida
                            logger.warning(f'Discrepancia en traslado {orden.folio}: {item.lote.numero_lote} - Faltaron {diferencia} unidades')
                
                except ValueError:
                    messages.error(request, f'Cantidad inválida para {item.lote.numero_lote}')
                    todos_validados = False
        
        if todos_validados:
            # Marcar la orden como recibida
            orden.estado = 'recibida'
            orden.fecha_llegada_real = timezone.now()
            orden.save()
            
            # Generar movimientos de entrada en el almacén destino
            for item in items:
                if item.cantidad_recibida > 0:
                    # Crear nuevo lote en el almacén destino o actualizar cantidad
                    lote_destino = Lote.objects.filter(
                        numero_lote=item.lote.numero_lote,
                        almacen=orden.almacen_destino
                    ).first()
                    
                    if lote_destino:
                        # Actualizar cantidad del lote existente
                        lote_destino.cantidad_disponible += item.cantidad_recibida
                        lote_destino.save()
                    else:
                        # Crear nuevo lote en el almacén destino
                        lote_destino = Lote.objects.create(
                            numero_lote=item.lote.numero_lote,
                            producto=item.lote.producto,
                            almacen=orden.almacen_destino,
                            institucion=item.lote.institucion,
                            cantidad_disponible=item.cantidad_recibida,
                            cantidad_inicial=item.cantidad_recibida,
                            precio_unitario=item.lote.precio_unitario,
                            fecha_fabricacion=item.lote.fecha_fabricacion,
                            fecha_caducidad=item.lote.fecha_caducidad,
                            fecha_recepcion=timezone.now(),
                            estado=1
                        )
                    
                    # Registrar movimiento de entrada
                    MovimientoInventario.objects.create(
                        lote=lote_destino,
                        tipo_movimiento='Entrada por Traslado',
                        cantidad_anterior=0,
                        cantidad=item.cantidad_recibida,
                        cantidad_nueva=lote_destino.cantidad_disponible,
                        usuario=request.user,
                        documento_referencia=orden.folio,
                        folio=orden.folio,
                        institucion_destino=orden.almacen_destino.institucion,
                        motivo=f'Recepción de traslado desde {orden.almacen_origen.nombre}'
                    )
            
            messages.success(request, '✓ Traslado validado y completado exitosamente')
            return redirect('logistica:detalle_traslado', pk=orden.pk)
    
    # Preparar formularios para cada item
    item_forms = []
    for item in items:
        form = ValidarItemTrasladoForm(instance=item)
        item_forms.append({
            'item': item,
            'form': form
        })
    
    return render(request, 'inventario/traslados/validar_llegada.html', {
        'orden': orden,
        'item_forms': item_forms,
        'items': items
    })
