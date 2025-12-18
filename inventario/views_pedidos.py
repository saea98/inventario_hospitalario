"""
Vistas para Fase 2.2.1: Gestión de Pedidos y Salida de Mercancía
Basado en Procedimiento 2 del Manual de Almacén IMSS-Bienestar
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    SolicitudPedido, ItemSolicitudPedido, OrdenSurtimiento, SalidaExistencias,
    ItemSalidaExistencias, Lote, Producto, MovimientoInventario, Institucion
)
from .forms import (
    SolicitudPedidoForm, ItemSolicitudPedidoForm, ValidarSolicitudPedidoForm,
    ConfirmarSalidaForm, FiltroSolicitudesForm
)


@login_required
def lista_solicitudes(request):
    """
    Paso 1: Recepción de Pedido
    Lista todas las solicitudes de pedidos con filtros
    """
    solicitudes = SolicitudPedido.objects.select_related(
        'institucion', 'almacen_origen', 'usuario_solicita'
    ).all()
    
    # Aplicar filtros
    form = FiltroSolicitudesForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data.get('estado'):
            solicitudes = solicitudes.filter(estado=form.cleaned_data['estado'])
        
        if form.cleaned_data.get('institucion'):
            solicitudes = solicitudes.filter(institucion=form.cleaned_data['institucion'])
        
        if form.cleaned_data.get('fecha_desde'):
            solicitudes = solicitudes.filter(
                fecha_solicitud__date__gte=form.cleaned_data['fecha_desde']
            )
        
        if form.cleaned_data.get('fecha_hasta'):
            solicitudes = solicitudes.filter(
                fecha_solicitud__date__lte=form.cleaned_data['fecha_hasta']
            )
        
        if form.cleaned_data.get('buscar'):
            solicitudes = solicitudes.filter(
                folio__icontains=form.cleaned_data['buscar']
            )
    
    # Estadísticas
    total = solicitudes.count()
    pendientes = solicitudes.filter(estado='PENDIENTE').count()
    validadas = solicitudes.filter(estado='VALIDADA').count()
    preparadas = solicitudes.filter(estado='PREPARADA').count()
    entregadas = solicitudes.filter(estado='ENTREGADA').count()
    
    context = {
        'solicitudes': solicitudes,
        'form': form,
        'total': total,
        'pendientes': pendientes,
        'validadas': validadas,
        'preparadas': preparadas,
        'entregadas': entregadas,
    }
    
    return render(request, 'inventario/pedidos/lista_solicitudes.html', context)


@login_required
def crear_solicitud(request):
    """
    Paso 1: Recepción de Pedido
    Crear una nueva solicitud de pedido
    """
    if request.method == 'POST':
        form = SolicitudPedidoForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.usuario_solicita = request.user
            solicitud.save()
            
            messages.success(request, f'Solicitud {solicitud.folio} creada exitosamente')
            return redirect('logistica:agregar_items_solicitud', solicitud_id=solicitud.id)
    else:
        form = SolicitudPedidoForm()
    
    context = {'form': form}
    return render(request, 'inventario/pedidos/crear_solicitud.html', context)


@login_required
def agregar_items_solicitud(request, solicitud_id):
    """
    Agregar items a una solicitud de pedido
    """
    solicitud = get_object_or_404(SolicitudPedido, id=solicitud_id)
    
    # Solo el creador puede agregar items
    if solicitud.usuario_solicita != request.user:
        messages.error(request, 'No tienes permiso para editar esta solicitud')
        return redirect('logistica:lista_solicitudes')
    
    if request.method == 'POST':
        form = ItemSolicitudPedidoForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.solicitud = solicitud
            item.save()
            
            # Actualizar cantidad de items
            solicitud.cantidad_items = solicitud.items.count()
            solicitud.save()
            
            messages.success(request, f'Item {item.producto.clave_cnis} agregado')
            return redirect('logistica:agregar_items_solicitud', solicitud_id=solicitud_id)
    else:
        form = ItemSolicitudPedidoForm()
    
    context = {
        'solicitud': solicitud,
        'form': form,
        'items': solicitud.items.all()
    }
    return render(request, 'inventario/pedidos/agregar_items.html', context)


@login_required
def validar_solicitud(request, solicitud_id):
    """
    Paso 2: Validación y Generación de Movimiento
    Validar la solicitud y generar la propuesta de salida con algoritmo FIFO
    """
    solicitud = get_object_or_404(SolicitudPedido, id=solicitud_id)
    
    # Verificar que puede validarse
    if not solicitud.puede_validarse():
        messages.error(request, 'Esta solicitud no puede validarse')
        return redirect('logistica:detalle_solicitud', solicitud_id=solicitud_id)
    
    if request.method == 'POST':
        form = ValidarSolicitudPedidoForm(request.POST, solicitud=solicitud)
        if form.is_valid():
            with transaction.atomic():
                # Procesar cada item
                for item in solicitud.items.all():
                    field_name = f'item_{item.id}_cantidad'
                    cantidad_aprobada = form.cleaned_data.get(field_name, 0)
                    
                    if cantidad_aprobada > 0:
                        # Asignar lote usando FIFO
                        lote_field_name = f'item_{item.id}_lote'
                        lote = form.cleaned_data.get(lote_field_name)
                        
                        if not lote:
                            # Buscar automáticamente el mejor lote (FIFO)
                            lote = obtener_mejor_lote_fifo(
                                item.producto,
                                cantidad_aprobada,
                                solicitud.almacen_origen
                            )
                        
                        if lote:
                            item.cantidad_aprobada = cantidad_aprobada
                            item.lote_asignado = lote
                            item.estado = 'VALIDADO'
                            item.save()
                            
                            solicitud.cantidad_items_validados += 1
                        else:
                            item.estado = 'NO_DISPONIBLE'
                            item.razon_no_disponible = 'No hay lotes disponibles con cantidad suficiente'
                            item.save()
                
                # Actualizar estado de la solicitud
                solicitud.estado = 'VALIDADA'
                solicitud.usuario_validacion = request.user
                solicitud.fecha_validacion = timezone.now()
                solicitud.save()
                
                # Generar Orden de Surtimiento
                crear_orden_surtimiento(solicitud)
                
                messages.success(request, f'Solicitud {solicitud.folio} validada correctamente')
                return redirect('logistica:detalle_solicitud', solicitud_id=solicitud_id)
    else:
        form = ValidarSolicitudPedidoForm(solicitud=solicitud)
    
    context = {
        'solicitud': solicitud,
        'form': form,
        'items': solicitud.items.all()
    }
    return render(request, 'inventario/pedidos/validar_solicitud.html', context)


@login_required
def detalle_solicitud(request, solicitud_id):
    """Ver detalles de una solicitud"""
    solicitud = get_object_or_404(SolicitudPedido, id=solicitud_id)
    
    context = {
        'solicitud': solicitud,
        'items': solicitud.items.all(),
        'orden': getattr(solicitud, 'orden_surtimiento', None),
        'salida': getattr(solicitud, 'salida_existencias', None),
    }
    return render(request, 'inventario/pedidos/detalle_solicitud.html', context)


@login_required
def imprimir_orden_surtimiento(request, orden_id):
    """
    Paso 3: Preparación del Pedido (Picking)
    Imprimir la orden de surtimiento optimizada por ubicación
    """
    orden = get_object_or_404(OrdenSurtimiento, id=orden_id)
    
    # Marcar como impresa
    if orden.estado == 'GENERADA':
        orden.estado = 'IMPRESA'
        orden.fecha_impresion = timezone.now()
        orden.save()
    
    # Obtener items ordenados por ubicación
    items_ordenados = []
    for item in orden.solicitud.items.filter(estado='VALIDADO'):
        if item.lote_asignado:
            items_ordenados.append({
                'producto': item.producto,
                'cantidad': item.cantidad_aprobada,
                'lote': item.lote_asignado,
                'ubicacion': item.lote_asignado.ubicacion,
            })
    
    # Ordenar por ubicación
    items_ordenados.sort(key=lambda x: x['ubicacion'].codigo if x['ubicacion'] else '')
    
    context = {
        'orden': orden,
        'solicitud': orden.solicitud,
        'items': items_ordenados,
    }
    return render(request, 'inventario/pedidos/orden_surtimiento.html', context)


@login_required
def confirmar_salida(request, solicitud_id):
    """
    Paso 4 y 5: Registro de Salida y Entrega al Área Receptora
    Confirmar que el pedido fue surtido y entregado
    """
    solicitud = get_object_or_404(SolicitudPedido, id=solicitud_id)
    
    if solicitud.estado != 'PREPARADA':
        messages.error(request, 'Esta solicitud no está lista para entrega')
        return redirect('logistica:detalle_solicitud', solicitud_id=solicitud_id)
    
    if request.method == 'POST':
        form = ConfirmarSalidaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Crear Salida de Existencias
                salida = SalidaExistencias.objects.create(
                    solicitud=solicitud,
                    usuario=request.user,
                    tipo_salida='PEDIDO',
                    nombre_receptor=form.cleaned_data['nombre_receptor'],
                    firma_receptor=form.cleaned_data.get('firma_receptor'),
                    observaciones=form.cleaned_data.get('observaciones'),
                )
                
                # Crear items de salida y actualizar inventario
                for item in solicitud.items.filter(estado='VALIDADO'):
                    if item.lote_asignado:
                        # Crear item de salida
                        ItemSalidaExistencias.objects.create(
                            salida=salida,
                            producto=item.producto,
                            lote=item.lote_asignado,
                            cantidad=item.cantidad_aprobada,
                            precio_unitario=item.lote_asignado.precio_unitario,
                        )
                        
                        # Reducir cantidad disponible en lote
                        item.lote_asignado.cantidad_disponible -= item.cantidad_aprobada
                        item.lote_asignado.save()
                        
                        # Crear movimiento de inventario
                        MovimientoInventario.objects.create(
                            lote=item.lote_asignado,
                            tipo_movimiento='SALIDA',
                            cantidad=item.cantidad_aprobada,
                            usuario=request.user,
                            motivo=f'Salida de Existencias - Pedido {solicitud.folio}',
                            documento_referencia=salida.folio,
                        )
                
                # Actualizar estado de la solicitud
                solicitud.estado = 'ENTREGADA'
                solicitud.fecha_entrega = timezone.now()
                solicitud.save()
                
                messages.success(request, f'Pedido {solicitud.folio} entregado exitosamente')
                return redirect('logistica:detalle_solicitud', solicitud_id=solicitud_id)
    else:
        form = ConfirmarSalidaForm()
    
    context = {
        'solicitud': solicitud,
        'form': form,
        'items': solicitud.items.filter(estado='VALIDADO')
    }
    return render(request, 'inventario/pedidos/confirmar_salida.html', context)


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def obtener_mejor_lote_fifo(producto, cantidad_requerida, almacen):
    """
    Algoritmo FIFO Inteligente
    Selecciona el mejor lote según:
    1. Proximidad a caducidad (>2 meses de vigencia)
    2. Lotes más antiguos primero
    3. Cantidad suficiente disponible
    """
    hoy = timezone.now().date()
    fecha_minima_vigencia = hoy + timedelta(days=60)  # >2 meses
    
    # Buscar lotes que cumplen con vigencia mínima
    lotes = Lote.objects.filter(
        producto=producto,
        almacen=almacen,
        cantidad_disponible__gte=cantidad_requerida,
        fecha_caducidad__gt=fecha_minima_vigencia,
        estado='DISPONIBLE'
    ).order_by('fecha_caducidad', 'fecha_recepcion')  # FIFO
    
    if lotes.exists():
        return lotes.first()
    
    # Si no hay lotes con >2 meses, buscar los próximos a caducar
    lotes_proximos = Lote.objects.filter(
        producto=producto,
        almacen=almacen,
        cantidad_disponible__gte=cantidad_requerida,
        fecha_caducidad__lte=fecha_minima_vigencia,
        estado='DISPONIBLE'
    ).order_by('fecha_caducidad', 'fecha_recepcion')
    
    if lotes_proximos.exists():
        return lotes_proximos.first()
    
    return None


def crear_orden_surtimiento(solicitud):
    """
    Crear una orden de surtimiento a partir de una solicitud validada
    Ordena los items por ubicación para optimizar el picking
    """
    orden = OrdenSurtimiento.objects.create(
        solicitud=solicitud,
    )
    
    return orden


@login_required
def historial_pedidos(request):
    """Ver historial de todos los pedidos"""
    salidas = SalidaExistencias.objects.select_related(
        'solicitud', 'usuario'
    ).all().order_by('-fecha_salida')
    
    context = {
        'salidas': salidas,
        'total': salidas.count(),
    }
    return render(request, 'inventario/pedidos/historial_pedidos.html', context)


@login_required
def detalle_salida(request, salida_id):
    """Ver detalles de una salida de existencias"""
    salida = get_object_or_404(SalidaExistencias, id=salida_id)
    
    context = {
        'salida': salida,
        'items': salida.items.all(),
        'solicitud': salida.solicitud,
    }
    return render(request, 'inventario/pedidos/detalle_salida.html', context)
