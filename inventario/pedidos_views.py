"""
Vistas para el módulo de Gestión de Pedidos (Fase 2.2.1)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from datetime import date

from .pedidos_models import SolicitudPedido, ItemSolicitud, PropuestaPedido, ItemPropuesta
from .pedidos_forms import (
    SolicitudPedidoForm,
    ItemSolicitudFormSet,
    FiltroSolicitudesForm,
    ValidarSolicitudPedidoForm
)
from .propuesta_generator import PropuestaGenerator

# ============================================================================
# VISTAS DE GESTIÓN DE PEDIDOS
# ============================================================================

@login_required
def lista_solicitudes(request):
    """
    Muestra una lista de todas las solicitudes de pedido, con filtros.
    """
    solicitudes = SolicitudPedido.objects.select_related(
        'institucion_solicitante', 'almacen_destino', 'usuario_solicitante'
    ).all()
    
    form = FiltroSolicitudesForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data['estado']:
            solicitudes = solicitudes.filter(estado=form.cleaned_data['estado'])
        if form.cleaned_data['fecha_inicio']:
            solicitudes = solicitudes.filter(fecha_solicitud__gte=form.cleaned_data['fecha_inicio'])
        if form.cleaned_data['fecha_fin']:
            solicitudes = solicitudes.filter(fecha_solicitud__lte=form.cleaned_data['fecha_fin'])
        if form.cleaned_data['institucion']:
            solicitudes = solicitudes.filter(institucion_solicitante__nombre__icontains=form.cleaned_data['institucion'])
            
    context = {
        'solicitudes': solicitudes,
        'form': form,
        'page_title': 'Gestión de Pedidos'
    }
    return render(request, 'inventario/pedidos/lista_solicitudes.html', context)


@login_required
@transaction.atomic
def crear_solicitud(request):
    """
    Permite a un usuario crear una nueva solicitud de pedido y añadirle items.
    """
    if request.method == 'POST':
        form = SolicitudPedidoForm(request.POST)
        formset = ItemSolicitudFormSet(request.POST, instance=SolicitudPedido())
        
        if form.is_valid() and formset.is_valid():
            # Primero guardar la solicitud
            solicitud = form.save(commit=False)
            solicitud.usuario_solicitante = request.user
            solicitud.save()
            
            # Luego procesar el formset con la solicitud ya guardada
            formset = ItemSolicitudFormSet(request.POST, instance=solicitud)
            
            if formset.is_valid():
                formset.save()
                messages.success(request, f"Solicitud {solicitud.folio} creada con éxito.")
                return redirect('logistica:detalle_pedido', solicitud_id=solicitud.id)
            else:
                # Si el formset no es válido, eliminar la solicitud y mostrar error
                solicitud.delete()
                messages.error(request, "Por favor, corrige los errores en los items.")
        else:
            # Mostrar errores del formulario
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            if formset.errors:
                messages.error(request, "Por favor, corrige los errores en los items.")

    else:
        form = SolicitudPedidoForm()
        formset = ItemSolicitudFormSet(instance=SolicitudPedido())
        
    context = {
        'form': form,
        'formset': formset,
        'page_title': 'Crear Nueva Solicitud de Pedido'
    }
    return render(request, 'inventario/pedidos/crear_solicitud.html', context)


@login_required
def detalle_solicitud(request, solicitud_id):
    """
    Muestra el detalle de una solicitud de pedido específica.
    """
    solicitud = get_object_or_404(
        SolicitudPedido.objects.select_related(
            'institucion_solicitante', 'almacen_destino', 'usuario_solicitante', 'usuario_validacion'
        ).prefetch_related('items__producto'),
        id=solicitud_id
    )
    
    # Obtener la propuesta si existe
    propuesta = PropuestaPedido.objects.filter(solicitud=solicitud).first()
    
    context = {
        'solicitud': solicitud,
        'propuesta': propuesta,
        'page_title': f"Detalle de Solicitud {solicitud.folio}"
    }
    return render(request, 'inventario/pedidos/detalle_solicitud.html', context)


@login_required
@transaction.atomic
def validar_solicitud(request, solicitud_id):
    """
    Permite a un usuario autorizado validar, modificar o rechazar los items de una solicitud.
    Genera automáticamente la propuesta de pedido si la solicitud es aprobada.
    """
    solicitud = get_object_or_404(SolicitudPedido, id=solicitud_id, estado='PENDIENTE')
    
    if request.method == 'POST':
        form = ValidarSolicitudPedidoForm(request.POST, solicitud=solicitud)
        if form.is_valid():
            solicitud.usuario_validacion = request.user
            solicitud.fecha_validacion = timezone.now()
            
            # Procesar cada item
            for item in solicitud.items.all():
                cantidad_aprobada = form.cleaned_data.get(f'item_{item.id}_cantidad_aprobada')
                justificacion = form.cleaned_data.get(f'item_{item.id}_justificacion')
                
                item.cantidad_aprobada = cantidad_aprobada
                item.justificacion_cambio = justificacion
                item.save()
            
            # Actualizar estado de la solicitud
            total_aprobado = sum(item.cantidad_aprobada for item in solicitud.items.all())
            if total_aprobado == 0:
                solicitud.estado = 'RECHAZADA'
                messages.warning(request, f"Solicitud {solicitud.folio} ha sido rechazada.")
                solicitud.save()
            else:
                solicitud.estado = 'VALIDADA'
                solicitud.save()
                
                # Generar la propuesta de pedido automáticamente
                try:
                    generator = PropuestaGenerator(solicitud.id, request.user)
                    propuesta = generator.generate()
                    messages.success(request, f"Solicitud {solicitud.folio} validada y propuesta de pedido generada.")
                except Exception as e:
                    messages.error(request, f"Error al generar la propuesta: {str(e)}")
            
            return redirect('logistica:detalle_pedido', solicitud_id=solicitud.id)
    else:
        form = ValidarSolicitudPedidoForm(solicitud=solicitud)
        
    context = {
        'solicitud': solicitud,
        'form': form,
        'page_title': f"Validar Solicitud {solicitud.folio}"
    }
    return render(request, 'inventario/pedidos/validar_solicitud.html', context)


# ============================================================================
# VISTAS DE PROPUESTA DE PEDIDO (Para personal de almacén)
# ============================================================================

@login_required
def lista_propuestas(request):
    """
    Muestra una lista de propuestas de pedido para que el almacén las revise y surta.
    """
    propuestas = PropuestaPedido.objects.select_related(
        'solicitud__institucion_solicitante',
        'solicitud__almacen_destino'
    ).all()
    
    # Filtrar por estado
    estado = request.GET.get('estado')
    if estado:
        propuestas = propuestas.filter(estado=estado)
    
    context = {
        'propuestas': propuestas,
        'estados': PropuestaPedido.ESTADO_CHOICES,
        'page_title': 'Propuestas de Pedido para Surtimiento'
    }
    return render(request, 'inventario/pedidos/lista_propuestas.html', context)


@login_required
def detalle_propuesta(request, propuesta_id):
    """
    Muestra el detalle de una propuesta de pedido con los lotes asignados.
    """
    propuesta = get_object_or_404(
        PropuestaPedido.objects.select_related(
            'solicitud__institucion_solicitante',
            'solicitud__almacen_destino'
        ).prefetch_related('items__lotes_asignados__lote_ubicacion__lote', 'items__lotes_asignados__lote_ubicacion__ubicacion__almacen'),
        id=propuesta_id
    )
    
    context = {
        'propuesta': propuesta,
        'page_title': f"Propuesta {propuesta.solicitud.folio}"
    }
    return render(request, 'inventario/pedidos/detalle_propuesta.html', context)


@login_required
@transaction.atomic
def revisar_propuesta(request, propuesta_id):
    """
    Permite al personal de almacén revisar la propuesta antes de surtir.
    """
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id, estado='GENERADA')
    
    if request.method == 'POST':
        propuesta.estado = 'REVISADA'
        propuesta.fecha_revision = timezone.now()
        propuesta.usuario_revision = request.user
        propuesta.observaciones_revision = request.POST.get('observaciones', '')
        propuesta.save()
        
        messages.success(request, "Propuesta revisada. Procede al surtimiento.")
        return redirect('logistica:detalle_propuesta', propuesta_id=propuesta.id)
    
    context = {
        'propuesta': propuesta,
        'page_title': f"Revisar Propuesta {propuesta.solicitud.folio}"
    }
    return render(request, 'inventario/pedidos/revisar_propuesta.html', context)


@login_required
@transaction.atomic
def surtir_propuesta(request, propuesta_id):
    """
    Permite al personal de almacén confirmar el surtimiento de una propuesta.
    FASE 5: Genera automáticamente movimientos de inventario.
    """
    from .fase5_utils import generar_movimientos_suministro
    
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id, estado='REVISADA')
    
    if request.method == 'POST':
        propuesta.estado = 'EN_SURTIMIENTO'
        propuesta.fecha_surtimiento = timezone.now()
        propuesta.usuario_surtimiento = request.user
        propuesta.save()
        
        # Marcar los lotes como surtidos
        for item in propuesta.items.all():
            for lote_asignado in item.lotes_asignados.all():
                lote_asignado.surtido = True
                lote_asignado.fecha_surtimiento = timezone.now()
                lote_asignado.save()
        
        propuesta.estado = 'SURTIDA'
        propuesta.save()
        
        # FASE 5: Generar movimientos de inventario automáticamente
        resultado = generar_movimientos_suministro(propuesta.id, request.user)
        if resultado['exito']:
            messages.success(
                request, 
                f"Propuesta surtida exitosamente. {resultado['mensaje']}"
            )
        else:
            messages.warning(
                request, 
                f"Propuesta surtida pero con advertencia: {resultado['mensaje']}"
            )
        
        return redirect('logistica:lista_propuestas')
    
    context = {
        'propuesta': propuesta,
        'page_title': f"Surtir Propuesta {propuesta.solicitud.folio}"
    }
    return render(request, 'inventario/pedidos/surtir_propuesta.html', context)



@login_required
@transaction.atomic
def editar_propuesta(request, propuesta_id):
    """
    Permite al personal de almacén editar los lotes y cantidades de la propuesta.
    Puede cambiar qué lotes se asignan y qué cantidades se proponen para cada item.
    """
    from .pedidos_models import LoteAsignado, LoteUbicacion
    
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id, estado='GENERADA')
    
    if request.method == 'POST':
        # Procesar cambios en cantidades y lotes
        for item in propuesta.items.all():
            # Actualizar cantidad propuesta
            nueva_cantidad = request.POST.get(f'item_{item.id}_cantidad_propuesta')
            if nueva_cantidad:
                item.cantidad_propuesta = int(nueva_cantidad)
                item.save()
            
            # Procesar cambios en lotes asignados
            lotes_actuales = item.lotes_asignados.select_related('lote_ubicacion__lote', 'lote_ubicacion__ubicacion').all()
            for lote_asignado in lotes_actuales:
                nueva_cantidad_lote = request.POST.get(f'lote_{lote_asignado.id}_cantidad')
                if nueva_cantidad_lote:
                    lote_asignado.cantidad_asignada = int(nueva_cantidad_lote)
                    lote_asignado.save()
                
                # Eliminar lote si se marca para eliminar
                if request.POST.get(f'lote_{lote_asignado.id}_eliminar'):
                    lote_asignado.delete()
            
            # Agregar nuevos lotes si se seleccionan
            nueva_ubicacion_id = request.POST.get(f'item_{item.id}_nueva_ubicacion')
            if nueva_ubicacion_id:
                lote_ubicacion = LoteUbicacion.objects.get(id=nueva_ubicacion_id)
                cantidad_nuevo = int(request.POST.get(f'item_{item.id}_cantidad_nueva_ubicacion', 0))
                
                if cantidad_nuevo > 0:
                    LoteAsignado.objects.create(
                        item_propuesta=item,
                        lote_ubicacion=lote_ubicacion,
                        cantidad_asignada=cantidad_nuevo
                    )
        
        # Actualizar totales de la propuesta
        propuesta.total_propuesto = sum(item.cantidad_propuesta for item in propuesta.items.all())
        propuesta.save()
        
        messages.success(request, "Propuesta actualizada correctamente.")
        return redirect('logistica:detalle_propuesta', propuesta_id=propuesta.id)
    
    context = {
        'propuesta': propuesta,
        'page_title': f"Editar Propuesta {propuesta.solicitud.folio}"
    }
    return render(request, 'inventario/pedidos/editar_propuesta.html', context)
