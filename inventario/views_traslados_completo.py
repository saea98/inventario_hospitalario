"""
Vistas Completas para Órdenes de Traslado
Incluye: CRUD, asignación de logística, cambios de estado y notificaciones
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.urls import reverse
from django.urls import NoReverseMatch
from datetime import datetime
import logging

from .models import (
    OrdenTraslado, ItemTraslado, Almacen, Lote,
    OrdenSuministro,
    UbicacionAlmacen, MovimientoInventario, Folio, TipoEntrega
)
from .pedidos_models import SolicitudPedido, PropuestaPedido, LoteAsignado
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
def datos_traslado_desde_orden_suministro(request):
    """
    API JSON: dados para llenar una orden de traslado desde una orden de suministro.
    GET: orden_suministro_id=...
    Retorna: almacen_origen { id, nombre }, numero_orden, items [ { lote_id, numero_lote, producto, cantidad_disponible } ]
    """
    orden_suministro_id = request.GET.get('orden_suministro_id', '').strip()
    if not orden_suministro_id:
        return JsonResponse({'error': 'Falta orden_suministro_id'}, status=400)
    try:
        orden_suministro = OrdenSuministro.objects.get(pk=orden_suministro_id, activo=True)
    except OrdenSuministro.DoesNotExist:
        return JsonResponse({'error': 'Orden de suministro no encontrada'}, status=404)
    lotes = Lote.objects.filter(
        orden_suministro=orden_suministro,
        cantidad_disponible__gt=0,
        estado=1
    ).select_related('almacen', 'producto')
    if not lotes.exists():
        return JsonResponse({
            'error': 'No hay lotes disponibles con existencia para esta orden de suministro',
            'almacen_origen': None,
            'items': []
        })
    # Agrupar por almacén y elegir el almacén con más cantidad total
    by_almacen = lotes.values('almacen').annotate(total=Sum('cantidad_disponible')).order_by('-total')
    if not by_almacen or not by_almacen[0]['almacen']:
        return JsonResponse({'error': 'Los lotes no tienen almacén asignado', 'almacen_origen': None, 'items': []})
    almacen_id = by_almacen[0]['almacen']
    almacen = Almacen.objects.get(pk=almacen_id)
    items_lotes = lotes.filter(almacen_id=almacen_id)
    items = [
        {
            'lote_id': l.id,
            'numero_lote': l.numero_lote or '',
            'producto': (l.producto.clave_cnis or '') + ' - ' + (l.producto.descripcion or '')[:80],
            'cantidad_disponible': l.cantidad_disponible,
        }
        for l in items_lotes
    ]
    return JsonResponse({
        'numero_orden': orden_suministro.numero_orden,
        'almacen_origen': {'id': almacen.id, 'nombre': almacen.nombre},
        'items': items,
    })


@login_required
def datos_traslado_desde_folio_pedido(request):
    """
    API JSON: datos para llenar una orden de traslado desde el folio de pedido (observaciones_solicitud).
    Los datos se obtienen directamente de la tabla de propuesta de suministro (LoteAsignado surtido).
    GET: folio=... (valor de observaciones_solicitud de la solicitud de pedido)
    Retorna: almacen_origen { id, nombre }, folio_pedido, items [ { lote_id, numero_lote, producto, cantidad_disponible } ]
    """
    folio = (request.GET.get('folio') or '').strip()
    if not folio:
        return JsonResponse({'error': 'Falta el folio del pedido'}, status=400)
    solicitud = SolicitudPedido.objects.filter(
        observaciones_solicitud__iexact=folio
    ).select_related('propuesta_pedido').first()
    if not solicitud:
        return JsonResponse({'error': 'No se encontró solicitud con ese folio de pedido'}, status=404)
    try:
        propuesta = solicitud.propuesta_pedido
    except PropuestaPedido.DoesNotExist:
        return JsonResponse({'error': 'La solicitud no tiene propuesta de suministro'}, status=404)
    asignaciones = LoteAsignado.objects.filter(
        item_propuesta__propuesta=propuesta,
        surtido=True
    ).select_related(
        'lote_ubicacion__lote__producto',
        'lote_ubicacion__ubicacion__almacen',
    )
    if not asignaciones.exists():
        return JsonResponse({
            'error': 'No hay ítems surtidos en la propuesta para este pedido',
            'almacen_origen': None,
            'items': [],
        })
    by_almacen = {}
    for la in asignaciones:
        if not la.lote_ubicacion or not la.lote_ubicacion.lote:
            continue
        lote = la.lote_ubicacion.lote
        almacen = None
        if la.lote_ubicacion.ubicacion:
            almacen = la.lote_ubicacion.ubicacion.almacen
        if not almacen and lote.almacen_id:
            almacen = lote.almacen
        if not almacen:
            continue
        aid = almacen.id
        if aid not in by_almacen:
            by_almacen[aid] = {'almacen': almacen, 'items': []}
        by_almacen[aid]['items'].append({
            'lote_id': lote.id,
            'numero_lote': lote.numero_lote or '',
            'producto': (lote.producto.clave_cnis or '') + ' - ' + (lote.producto.descripcion or '')[:80],
            'cantidad_disponible': la.cantidad_asignada,
        })
    if not by_almacen:
        return JsonResponse({'error': 'Los ítems surtidos no tienen almacén asignado', 'almacen_origen': None, 'items': []})
    almacen_id = max(by_almacen.keys(), key=lambda aid: sum(it['cantidad_disponible'] for it in by_almacen[aid]['items']))
    almacen = by_almacen[almacen_id]['almacen']
    items = by_almacen[almacen_id]['items']
    return JsonResponse({
        'folio_pedido': folio,
        'almacen_origen': {'id': almacen.id, 'nombre': almacen.nombre},
        'items': items,
    })


@login_required
def crear_traslado(request):
    """Crear una nueva orden de traslado. Opcional: cargar datos desde folio de pedido (propuesta suministro) o desde orden de suministro."""
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
            except Exception:
                orden.folio = f"TRA-{timezone.now().strftime('%Y%m%d%H%M%S')}"

            orden.save()

            # Si se cargó desde folio de pedido (propuesta suministro), crear items desde LoteAsignado surtido
            folio_pedido = request.POST.get('folio_pedido', '').strip()
            if folio_pedido:
                try:
                    solicitud = SolicitudPedido.objects.filter(
                        observaciones_solicitud__iexact=folio_pedido
                    ).first()
                    if not solicitud:
                        solicitud = SolicitudPedido.objects.filter(
                            observaciones_solicitud__icontains=folio_pedido
                        ).first()
                    if solicitud:
                        try:
                            propuesta = solicitud.propuesta_pedido
                        except PropuestaPedido.DoesNotExist:
                            propuesta = None
                        if propuesta:
                            asignaciones = LoteAsignado.objects.filter(
                                item_propuesta__propuesta=propuesta,
                                surtido=True,
                            ).select_related(
                                'lote_ubicacion__lote',
                                'lote_ubicacion__ubicacion__almacen',
                            )
                            creados = 0
                            almacen_origen_id = orden.almacen_origen_id
                            for la in asignaciones:
                                if not la.lote_ubicacion or not la.lote_ubicacion.lote:
                                    continue
                                lote = la.lote_ubicacion.lote
                                ub = la.lote_ubicacion.ubicacion
                                en_almacen_origen = (
                                    (lote.almacen_id == almacen_origen_id)
                                    or (ub and getattr(ub, 'almacen_id', None) == almacen_origen_id)
                                )
                                if not en_almacen_origen:
                                    continue
                                ItemTraslado.objects.create(
                                    orden_traslado=orden,
                                    lote=lote,
                                    cantidad=la.cantidad_asignada,
                                    estado='pendiente',
                                )
                                creados += 1
                            if creados:
                                messages.success(request, f'✓ Orden de traslado creada: {orden.folio}. Se agregaron {creados} ítem(s) desde el pedido {folio_pedido}.')
                            else:
                                messages.success(request, f'✓ Orden de traslado creada: {orden.folio}')
                        else:
                            messages.success(request, f'✓ Orden de traslado creada: {orden.folio}')
                    else:
                        messages.success(request, f'✓ Orden de traslado creada: {orden.folio}')
                except Exception as e:
                    logger.warning('Error al crear items desde folio pedido: %s', e)
                    messages.success(request, f'✓ Orden de traslado creada: {orden.folio}. No se pudieron cargar ítems desde el folio de pedido.')
            else:
                # Opcional: desde orden de suministro (legacy)
                orden_suministro_id = request.POST.get('orden_suministro_id', '').strip()
                if orden_suministro_id:
                    try:
                        lotes = Lote.objects.filter(
                            orden_suministro_id=orden_suministro_id,
                            almacen=orden.almacen_origen,
                            cantidad_disponible__gt=0,
                            estado=1,
                        )
                        creados = 0
                        for lote in lotes:
                            ItemTraslado.objects.create(
                                orden_traslado=orden,
                                lote=lote,
                                cantidad=lote.cantidad_disponible,
                                estado='pendiente',
                            )
                            creados += 1
                        if creados:
                            messages.success(request, f'✓ Orden de traslado creada: {orden.folio}. Se agregaron {creados} ítem(s) desde la orden de suministro.')
                        else:
                            messages.success(request, f'✓ Orden de traslado creada: {orden.folio}')
                    except Exception as e:
                        logger.warning('Error al crear items desde orden suministro: %s', e)
                        messages.success(request, f'✓ Orden de traslado creada: {orden.folio}')
                else:
                    messages.success(request, f'✓ Orden de traslado creada: {orden.folio}')
            return redirect('logistica:detalle_traslado', pk=orden.pk)
        else:
            messages.error(request, 'Error al crear la orden. Verifica los datos.')
    else:
        form = OrdenTrasladoForm()

    # Solicitudes con propuesta y al menos un ítem surtido (para selector de folio de pedido)
    from django.db.models import Exists, OuterRef
    tiene_surtido = LoteAsignado.objects.filter(
        item_propuesta__propuesta__solicitud=OuterRef('pk'),
        surtido=True,
    )
    solicitudes_con_surtido = SolicitudPedido.objects.filter(
        estado__in=['EN_PREPARACION', 'PREPARADA', 'ENTREGADA', 'VALIDADA'],
    ).annotate(
        tiene_surtido=Exists(tiene_surtido),
    ).filter(tiene_surtido=True).values_list('observaciones_solicitud', flat=True).distinct()
    folios_pedido = [f for f in solicitudes_con_surtido if (f or '').strip()][:150]

    try:
        url_datos_folio_pedido = reverse('logistica:datos_traslado_desde_folio_pedido')
    except NoReverseMatch:
        url_datos_folio_pedido = '/logistica/traslados/datos-desde-folio-pedido/'
    try:
        url_datos_orden_suministro = reverse('logistica:datos_traslado_desde_orden_suministro')
    except NoReverseMatch:
        url_datos_orden_suministro = '/logistica/traslados/datos-desde-orden-suministro/'
    return render(request, 'inventario/traslados/crear.html', {
        'form': form,
        'folios_pedido': folios_pedido,
        'ordenes_suministro': OrdenSuministro.objects.filter(activo=True).order_by('-fecha_orden')[:100],
        'url_datos_folio_pedido': url_datos_folio_pedido,
        'url_datos_orden_suministro': url_datos_orden_suministro,
    })


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
