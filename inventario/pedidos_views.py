"""
Vistas para el módulo de Gestión de Pedidos (Fase 2.2.1)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse
from datetime import date
from io import BytesIO

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from datetime import datetime

from .pedidos_models import SolicitudPedido, ItemSolicitud, PropuestaPedido, ItemPropuesta
from .pedidos_forms import (
    SolicitudPedidoForm,
    ItemSolicitudFormSet,
    FiltroSolicitudesForm,
    ValidarSolicitudPedidoForm
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
    Incluye indicador de porcentaje surtido y botón de impresión para propuestas 100% surtidas.
    """
    propuestas = PropuestaPedido.objects.select_related(
        'solicitud__institucion_solicitante',
        'solicitud__almacen_destino',
        'solicitud__usuario_solicitante'
    ).prefetch_related('items').all()
    
    from django.urls import reverse
    propuestas_con_porcentaje = []
    for propuesta in propuestas:
        if not propuesta.id:
            continue
            
        total_solicitado = propuesta.items.aggregate(
            total=Sum('cantidad_solicitada')
        )['total'] or 0
        
        total_surtido = propuesta.items.aggregate(
            total=Sum('cantidad_surtida')
        )['total'] or 0
        
        porcentaje_surtido = 0
        if total_solicitado > 0:
            porcentaje_surtido = round((total_surtido / total_solicitado) * 100, 2)
        
        url_detalle = reverse('logistica:detalle_propuesta', args=[str(propuesta.id)])
        url_pdf = reverse('logistica:generar_acuse_entrega_pdf', args=[str(propuesta.id)])
        
        propuestas_con_porcentaje.append({
            'propuesta': propuesta,
            'porcentaje_surtido': porcentaje_surtido,
            'total_solicitado': total_solicitado,
            'total_surtido': total_surtido,
            'puede_imprimir': porcentaje_surtido == 100.0,
            'url_detalle': url_detalle,
            'url_pdf': url_pdf
        })
    
    # Filtrar por estado
    estado = request.GET.get('estado')
    if estado:
        propuestas_con_porcentaje = [
            p for p in propuestas_con_porcentaje 
            if p['propuesta'].estado == estado
        ]
    
    context = {
        'propuestas': propuestas_con_porcentaje,
        'estados': PropuestaPedido.ESTADO_CHOICES,
        'page_title': 'Propuestas de Pedido para Surtimiento',
        'filtro_estado': estado
    }
    return render(request, 'inventario/pedidos/lista_propuestas.html', context)


@login_required
def detalle_propuesta(request, propuesta_id):
    """
    Muestra el detalle de una propuesta de pedido con los lotes asignados.
    Incluye indicador de progreso y botón de impresión si está 100% surtida.
    """
    propuesta = get_object_or_404(
        PropuestaPedido.objects.select_related(
            'solicitud__institucion_solicitante',
            'solicitud__almacen_destino',
            'solicitud__usuario_solicitante'
        ).prefetch_related('items__lotes_asignados__lote_ubicacion__lote', 'items__lotes_asignados__lote_ubicacion__ubicacion__almacen'),
        id=propuesta_id
    )
    
    # Calcular porcentaje surtido
    total_solicitado = propuesta.items.aggregate(
        total=Sum('cantidad_solicitada')
    )['total'] or 0
    
    total_surtido = propuesta.items.aggregate(
        total=Sum('cantidad_surtida')
    )['total'] or 0
    
    porcentaje_surtido = 0
    if total_solicitado > 0:
        porcentaje_surtido = round((total_surtido / total_solicitado) * 100, 2)
    
    puede_imprimir = porcentaje_surtido == 100.0
    
    context = {
        'propuesta': propuesta,
        'page_title': f"Propuesta {propuesta.solicitud.folio}",
        'porcentaje_surtido': porcentaje_surtido,
        'total_solicitado': total_solicitado,
        'total_surtido': total_surtido,
        'puede_imprimir': puede_imprimir,
    }
    return render(request, 'inventario/pedidos/detalle_propuesta.html', context)


@login_required
def generar_acuse_entrega_pdf(request, propuesta_id):
    """
    Genera el PDF del Acuse de Entrega para una propuesta surtida al 100%
    """
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    
    # Verificar que esté 100% surtida
    total_solicitado = propuesta.items.aggregate(
        total=Sum('cantidad_solicitada')
    )['total'] or 0
    
    total_surtido = propuesta.items.aggregate(
        total=Sum('cantidad_surtida')
    )['total'] or 0
    
    if total_solicitado == 0 or total_surtido != total_solicitado:
        return redirect('detalle_propuesta', propuesta_id=propuesta_id)
    
    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ============ ENCABEZADO ============
    
    # Logo y título
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#8B1538'),
        spaceAfter=6,
        alignment=1
    )
    
    header = Paragraph('SAICA<br/>Sistema de Abasto, Inventarios y Control de Almacenes', header_style)
    elements.append(header)
    
    # Información del folio
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        spaceAfter=12
    )
    
    folio = propuesta.solicitud.folio
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    
    info_text = f'''
    <b>#FOLIO: {folio}</b><br/>
    <b>TRANSFERENCIA:</b> prueba<br/>
    <b>FECHA: {fecha_actual}</b><br/>
    <b>TIPO: TRANSFERENCIA (SURTIMIENTO)</b>
    '''
    info = Paragraph(info_text, info_style)
    elements.append(info)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # ============ ACUSE DE ENTREGA ============
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#8B1538'),
        spaceAfter=12,
        alignment=1
    )
    
    title = Paragraph('ACUSE DE ENTREGA', title_style)
    elements.append(title)
    
    # Tabla de datos de entrega
    solicitud = propuesta.solicitud
    usuario_solicitante = solicitud.usuario_solicitante
    
    delivery_data = [
        ['UNIDAD DE DESTINO', 'RECIBE (UNIDAD DE DESTINO)', 'AUTORIZA (ALMACÉN)', 'ENTREGA (ALMACÉN)'],
        [
            solicitud.institucion_solicitante.denominacion,
            'NOMBRE: _______________________________\n\nPUESTO: _______________________________\n\nFIRMA: _______________________________',
            f'NOMBRE:\n{usuario_solicitante.get_full_name()}\n\nPUESTO:\nMESA DE CONTROL\n\nFIRMA: _______________________________',
            'NOMBRE: _______________________________\n\nPUESTO: _______________________________\n\nFIRMA: _______________________________'
        ]
    ]
    
    delivery_table = Table(delivery_data, colWidths=[1.5*inch, 2*inch, 2*inch, 2*inch])
    delivery_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B1538')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWHEIGHTS', (0, 0), (-1, -1), 1.2*inch),
    ]))
    
    elements.append(delivery_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Observaciones
    obs_style = ParagraphStyle(
        'Observations',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
    )
    
    obs = Paragraph(f'<b>Observaciones:</b> {propuesta.solicitud.observaciones_solicitud or "N/A"}', obs_style)
    elements.append(obs)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # ============ TABLA DE PRODUCTOS ============
    
    # Obtener items
    items = propuesta.items.select_related(
        'producto',
        'item_solicitud'
    ).prefetch_related('lotes_asignados__lote_ubicacion__lote')
    
    # Preparar datos de tabla
    table_data = [[
        '#',
        'CLAVE',
        'DESCRIPCIÓN',
        'UNIDAD DE MEDIDA',
        'RECURSO',
        'LOTE',
        'CADUCIDAD',
        'ÁREA',
        'UBICACIÓN',
        'CANTIDAD SURTIDA',
        'OBSERVACIONES'
    ]]
    
    for idx, item in enumerate(items, 1):
        # Obtener información del lote
        lote_info = ''
        caducidad = ''
        ubicacion = ''
        
        if item.lotes_asignados.exists():
            lote_asignado = item.lotes_asignados.first()
            lote = lote_asignado.lote_ubicacion.lote
            lote_info = lote.numero_lote
            caducidad = lote.fecha_caducidad.strftime("%d/%m/%Y")
            ubicacion = lote_asignado.lote_ubicacion.ubicacion.codigo
        
        table_data.append([
            str(idx),
            item.producto.clave_cnis,
            item.producto.descripcion[:50],  # Limitar descripción
            item.producto.unidad_medida,
            'ORDINARIO',  # Placeholder
            lote_info,
            caducidad,
            'MEDICAMENTO',  # Placeholder
            ubicacion,
            str(item.cantidad_surtida),
            ''
        ])
    
    # Crear tabla
    table = Table(table_data, colWidths=[
        0.3*inch,  # #
        0.8*inch,  # CLAVE
        1.5*inch,  # DESCRIPCIÓN
        0.8*inch,  # UNIDAD
        0.7*inch,  # RECURSO
        0.8*inch,  # LOTE
        0.8*inch,  # CADUCIDAD
        0.7*inch,  # ÁREA
        0.8*inch,  # UBICACIÓN
        0.9*inch,  # CANTIDAD
        1.0*inch,  # OBSERVACIONES
    ])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B1538')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWHEIGHTS', (0, 0), (-1, -1), 0.25*inch),
    ]))
    
    elements.append(table)
    
    # Generar PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="acuse_entrega_{folio}.pdf"'
    
    return response


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
