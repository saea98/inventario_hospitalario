
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
import textwrap

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from io import BytesIO

from .pedidos_models import PropuestaPedido, ItemPropuesta, SolicitudPedido
from .models import Institucion, Almacen


def wrap_text(text, max_chars=25, max_lines=3):
    """
    Envuelve texto a un máximo de caracteres por línea y máximo de líneas
    """
    if not text:
        return ""
    
    lines = []
    for line in text.split('\n'):
        wrapped = textwrap.wrap(line, width=max_chars)
        lines.extend(wrapped)
    
    # Limitar a máximo de líneas
    return '\n'.join(lines[:max_lines])


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
    
    from django.urls import reverse
    
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
        
        # Generar URLs en la vista
        try:
            url_detalle = reverse('logistica:detalle_propuesta', args=[str(propuesta.id)])
            url_pdf = reverse('generar_acuse_entrega_pdf', args=[str(propuesta.id)])
        except:
            url_detalle = f'/logistica/propuestas/{propuesta.id}/'
            url_pdf = f'/logistica/propuestas/{propuesta.id}/acuse-pdf/'
        
        # Usar el estado SURTIDA para determinar si puede imprimir
        puede_imprimir = propuesta.estado == 'SURTIDA'
        
        propuestas_con_porcentaje.append({
            'propuesta': propuesta,
            'porcentaje_surtido': porcentaje_surtido,
            'total_solicitado': total_solicitado,
            'total_surtido': total_surtido,
            'puede_imprimir': puede_imprimir,
            'url_detalle': url_detalle,
            'url_pdf': url_pdf
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
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.8*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()

    # ============ ENCABEZADO ============
    import os
    from django.conf import settings
    logo_path = os.path.join(settings.BASE_DIR, 'templates', 'inventario', 'images', 'logo_acuse.png')
    logo = Image(logo_path, width=4.85*inch, height=1.0*inch)
    logo.hAlign = 'LEFT'

    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#8B1538'),
        alignment=2,
        spaceBefore=10
    )
    header_text = Paragraph('Sistema de Abasto, Inventarios y Control de Almacenes', header_style)

    header_table = Table([[logo, header_text]], colWidths=[3*inch, 7*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*inch))

    # Información del folio
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=2,
        leading=12
    )
    
    folio = propuesta.solicitud.folio
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    
    folio_pedido = propuesta.solicitud.observaciones_solicitud or 'N/A'
    info_text = f'''
    <b>#FOLIO: {folio}</b><br/>
    <b>TRANSFERENCIA:</b> prueba<br/>
    <b>FOLIO DE PEDIDO:</b> {folio_pedido}<br/>
    <b>FECHA: {fecha_actual}</b><br/>
    <b>TIPO: TRANSFERENCIA (SURTIMIENTO)</b>
    '''
    info = Paragraph(info_text, info_style)
    elements.append(info)
    elements.append(Spacer(1, 0.15*inch))
    
    # ============ ACUSE DE ENTREGA ============
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#8B1538'),
        spaceAfter=10,
        alignment=1
    )
    
    title = Paragraph('ACUSE DE ENTREGA', title_style)
    elements.append(title)
    
    # Tabla de datos de entrega
    solicitud = propuesta.solicitud
    usuario_solicitante = solicitud.usuario_solicitante
    
    # Envolver textos largos
    institucion_nombre = wrap_text(solicitud.institucion_solicitante.denominacion, max_chars=25, max_lines=3)
    usuario_nombre = wrap_text(usuario_solicitante.get_full_name(), max_chars=25, max_lines=2)
    
    delivery_data = [
        ['UNIDAD DE DESTINO', 'RECIBE (UNIDAD DE DESTINO)', 'AUTORIZA (ALMACEN)', 'ENTREGA (ALMACEN)'],
        [
            institucion_nombre,
            'NOMBRE: ___________________\n\nPUESTO: ___________________\n\nFIRMA: ___________________',
            f'NOMBRE:\n{usuario_nombre}\n\nPUESTO:\nMESA DE CONTROL\n\nFIRMA: ___________________',
            'NOMBRE: ___________________\n\nPUESTO: ___________________\n\nFIRMA: ___________________'
        ]
    ]
    
    delivery_table = Table(delivery_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch, 2.5*inch], rowHeights=[0.35*inch, 1.8*inch])
    delivery_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B1538')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('RIGHTPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('LEADING', (0, 1), (-1, -1), 11),
    ]))
    
    elements.append(delivery_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Observaciones
    obs_style = ParagraphStyle(
        'Observations',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.black,
    )
    
    obs_text = wrap_text(propuesta.solicitud.observaciones_solicitud or "N/A", max_chars=80, max_lines=2)
    obs = Paragraph(f'<b>Observaciones:</b> {obs_text}', obs_style)
    elements.append(obs)
    elements.append(Spacer(1, 0.15*inch))
    
    # ============ TABLA DE PRODUCTOS ============
    items = propuesta.items.select_related(
        'producto',
        'item_solicitud'
    ).prefetch_related('lotes_asignados__lote_ubicacion__lote')
    
    table_data = [[
        '#',
        'CLAVE',
        'DESCRIPCION',
        'UNIDAD DE MEDIDA',
        'RECURSO',
        'LOTE',
        'CADUCIDAD',
        'AREA',
        'UBICACION',
        'CANTIDAD SURTIDA',
        'OBSERVACIONES'
    ]]
    
    for idx, item in enumerate(items, 1):
        lote_info = ''
        caducidad = ''
        ubicacion = ''
        
        if item.lotes_asignados.exists():
            lote_asignado = item.lotes_asignados.first()
            lote = lote_asignado.lote_ubicacion.lote
            lote_info = lote.numero_lote
            caducidad = lote.fecha_caducidad.strftime("%d/%m/%Y")
            ubicacion = lote_asignado.lote_ubicacion.ubicacion.codigo
        
        # Envolver descripción
        descripcion = wrap_text(item.producto.descripcion, max_chars=20, max_lines=2)
        
        table_data.append([
            str(idx),
            item.producto.clave_cnis,
            descripcion,
            item.producto.unidad_medida,
            'ORDINARIO',
            lote_info,
            caducidad,
            'MEDICAMENTO',
            ubicacion,
            str(item.cantidad_propuesta if item.cantidad_propuesta > 0 else item.cantidad_surtida),
            ''
        ])
    
    # Usar el mismo ancho que la tabla de firmas (10 pulgadas total)
    table = Table(table_data, colWidths=[
        0.3*inch, 0.8*inch, 1.5*inch, 0.8*inch, 0.7*inch, 
        0.8*inch, 0.8*inch, 0.7*inch, 0.8*inch, 0.9*inch, 1.0*inch
    ])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B1538')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LEFTPADDING', (0, 1), (-1, -1), 3),
        ('RIGHTPADDING', (0, 1), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('LEADING', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(table)
    
    # Función para paginación
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawString(inch, 0.5 * inch, f"Pagina {doc.page}")
        canvas.restoreState()

    # Generar PDF
    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="acuse_entrega_{folio}.pdf"'
    
    return response
