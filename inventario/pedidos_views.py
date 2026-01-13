
"""
Vistas para el módulo de Gestión de Pedidos (Fase 2.2.1)
"""

import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from datetime import date

from .pedidos_models import SolicitudPedido, ItemSolicitud, PropuestaPedido, ItemPropuesta, Producto
from .pedidos_forms import (
    SolicitudPedidoForm,
    ItemSolicitudFormSet,
    FiltroSolicitudesForm,
    ValidarSolicitudPedidoForm,
    BulkUploadForm
)
from .propuesta_generator import PropuestaGenerator
from .propuesta_utils import cancelar_propuesta

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
    Permite a un usuario crear una nueva solicitud de pedido y añadirle items,
    incluyendo la opción de carga masiva por CSV.
    """
    upload_form = BulkUploadForm()
    
    if request.method == 'POST':
        # Si se sube un archivo CSV
        if 'upload_csv' in request.POST:
            upload_form = BulkUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                csv_file = request.FILES['csv_file']
                try:
                    items_data = []
                    decoded_file = csv_file.read().decode('utf-8-sig')
                    io_string = io.StringIO(decoded_file)
                    reader = csv.DictReader(io_string)
                    
                    for row in reader:
                        clave = row.get('CLAVE')
                        cantidad = row.get('CANTIDAD SOLICITADA')
                        
                        if clave and cantidad:
                            try:
                                producto = Producto.objects.get(clave_cnis=clave)
                                items_data.append({
                                    'producto': producto.id,
                                    'cantidad_solicitada': int(cantidad)
                                })
                            except (Producto.DoesNotExist, ValueError):
                                messages.warning(request, f"La clave '{clave}' no existe o la cantidad '{cantidad}' no es válida.")
                    
                    # Crear formset con datos del CSV
                    formset = ItemSolicitudFormSet(initial=items_data)
                    form = SolicitudPedidoForm()
                    messages.success(request, f"{len(items_data)} items cargados desde el CSV.")
                    
                except Exception as e:
                    messages.error(request, f"Error al procesar el archivo CSV: {e}")
                    form = SolicitudPedidoForm()
                    formset = ItemSolicitudFormSet(instance=SolicitudPedido())
            else:
                messages.error(request, "Error en el formulario de carga de archivo.")
                form = SolicitudPedidoForm()
                formset = ItemSolicitudFormSet(instance=SolicitudPedido())
        
        # Si se guarda el formulario principal
        else:
            form = SolicitudPedidoForm(request.POST)
            formset = ItemSolicitudFormSet(request.POST, instance=SolicitudPedido())
            
            if form.is_valid() and formset.is_valid():
                solicitud = form.save(commit=False)
                solicitud.usuario_solicitante = request.user
                solicitud.save()
                
                formset.instance = solicitud
                formset.save()
                messages.success(request, f"Solicitud {solicitud.folio} creada con éxito.")
                return redirect('logistica:detalle_pedido', solicitud_id=solicitud.id)
            else:
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
        'upload_form': upload_form,
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
            
            for item in solicitud.items.all():
                cantidad_aprobada = form.cleaned_data.get(f'item_{item.id}_cantidad_aprobada')
                justificacion = form.cleaned_data.get(f'item_{item.id}_justificacion')
                
                item.cantidad_aprobada = cantidad_aprobada
                item.justificacion_cambio = justificacion
                item.save()
            
            total_aprobado = sum(item.cantidad_aprobada for item in solicitud.items.all())
            if total_aprobado == 0:
                solicitud.estado = 'RECHAZADA'
                messages.warning(request, f"Solicitud {solicitud.folio} ha sido rechazada.")
                solicitud.save()
            else:
                solicitud.estado = 'VALIDADA'
                solicitud.save()
                
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


# ... (el resto de las vistas se mantiene igual)
