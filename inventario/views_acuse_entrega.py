"""
Vistas para generar Acuse de Entrega en PDF
Módulo: Logística - Gestión de Propuestas de Surtimiento
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, Case, When, IntegerField
from django.utils import timezone
from datetime import datetime

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from io import BytesIO

from .pedidos_models import PropuestaPedido, ItemPropuesta, SolicitudPedido
from .models import Institucion, Almacen


@login_required
def lista_propuestas_surtimiento(request):
    """
    Lista todas las propuestas de surtimiento con indicador de porcentaje surtido
    """
    propuestas = PropuestaPedido.objects.select_related(
        'solicitud__institucion_solicitante',
        'solicitud__almacen_destino',
        'solicitud__usuario_solicitante'
    ).prefetch_related('items')
    
    # Calcular porcentaje surtido para cada propuesta
    propuestas_con_porcentaje = []
    for propuesta in propuestas:
        total_solicitado = propuesta.items.aggregate(
            total=Sum('cantidad_solicitada')
        )['total'] or 0
        
        total_surtido = propuesta.items.aggregate(
            total=Sum('cantidad_surtida')
        )['total'] or 0
        
        porcentaje_surtido = 0
        if total_solicitado > 0:
            porcentaje_surtido = round((total_surtido / total_solicitado) * 100, 2)
        
        propuestas_con_porcentaje.append({
            'propuesta': propuesta,
            'porcentaje_surtido': porcentaje_surtido,
            'total_solicitado': total_solicitado,
            'total_surtido': total_surtido,
            'puede_imprimir': porcentaje_surtido == 100.0
        })
    
    # Filtros
    filtro_estado = request.GET.get('estado', '')
    filtro_institucion = request.GET.get('institucion', '')
    filtro_almacen = request.GET.get('almacen', '')
    
    if filtro_estado:
        propuestas_con_porcentaje = [
            p for p in propuestas_con_porcentaje 
            if p['propuesta'].estado == filtro_estado
        ]
    
    if filtro_institucion:
        propuestas_con_porcentaje = [
            p for p in propuestas_con_porcentaje 
            if str(p['propuesta'].solicitud.institucion_solicitante.id) == filtro_institucion
        ]
    
    if filtro_almacen:
        propuestas_con_porcentaje = [
            p for p in propuestas_con_porcentaje 
            if str(p['propuesta'].solicitud.almacen_destino.id) == filtro_almacen
        ]
    
    # Paginación
    paginator = Paginator(propuestas_con_porcentaje, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Opciones para filtros
    instituciones = Institucion.objects.all()
    almacenes = Almacen.objects.all()
    estados = PropuestaPedido.ESTADO_CHOICES
    
    context = {
        'page_obj': page_obj,
        'instituciones': instituciones,
        'almacenes': almacenes,
        'estados': estados,
        'filtro_estado': filtro_estado,
        'filtro_institucion': filtro_institucion,
        'filtro_almacen': filtro_almacen,
    }
    
    return render(request, 'inventario/lista_propuestas_surtimiento.html', context)


@login_required
def detalle_propuesta_surtimiento(request, propuesta_id):
    """
    Detalle de una propuesta de surtimiento con botón para imprimir acuse
    """
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    
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
    
    # Obtener items con información de lotes
    items = propuesta.items.select_related(
        'producto',
        'item_solicitud'
    ).prefetch_related('lotes_asignados__lote_ubicacion__lote')
    
    context = {
        'propuesta': propuesta,
        'items': items,
        'porcentaje_surtido': porcentaje_surtido,
        'total_solicitado': total_solicitado,
        'total_surtido': total_surtido,
        'puede_imprimir': puede_imprimir,
    }
    
    return render(request, 'inventario/detalle_propuesta_surtimiento.html', context)


@login_required
@require_http_methods(["GET"])
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
        return redirect('detalle_propuesta_surtimiento', propuesta_id=propuesta_id)
    
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
