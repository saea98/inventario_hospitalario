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
        'solicitud__almacen_destino'
    ).order_by('-fecha_generacion')
    
    # Filtros
    estado_filter = request.GET.get('estado')
    if estado_filter:
        propuestas = propuestas.filter(estado=estado_filter)
    
    institucion_filter = request.GET.get('institucion')
    if institucion_filter:
        propuestas = propuestas.filter(solicitud__institucion_solicitante_id=institucion_filter)
    
    # Búsqueda
    busqueda = request.GET.get('q')
    if busqueda:
        propuestas = propuestas.filter(
            Q(solicitud__folio__icontains=busqueda) |
            Q(solicitud__institucion_solicitante__nombre__icontains=busqueda)
        )
    
    # Calcular porcentaje de surtimiento
    propuestas_con_progreso = []
    for prop in propuestas:
        total_items = prop.items.count()
        if total_items > 0:
            items_surtidos = prop.items.filter(estado='SURTIDO').count()
            porcentaje = (items_surtidos / total_items) * 100
        else:
            porcentaje = 0
        
        propuestas_con_progreso.append({
            'propuesta': prop,
            'total_items': total_items,
            'items_surtidos': items_surtidos if total_items > 0 else 0,
            'porcentaje': porcentaje,
            'puede_generar_acuse': porcentaje == 100
        })
    
    # Paginación
    paginator = Paginator(propuestas_con_progreso, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener instituciones para filtro
    instituciones = Institucion.objects.all()
    
    context = {
        'page_obj': page_obj,
        'instituciones': instituciones,
        'estado_filter': estado_filter,
        'institucion_filter': institucion_filter,
        'busqueda': busqueda,
    }
    
    return render(request, 'inventario/propuestas_surtimiento.html', context)


@login_required
def detalle_propuesta_surtimiento(request, propuesta_id):
    """
    Detalle de una propuesta de surtimiento
    """
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    
    # Calcular estadísticas
    total_items = propuesta.items.count()
    items_surtidos = propuesta.items.filter(estado='SURTIDO').count()
    items_disponibles = propuesta.items.filter(estado__in=['DISPONIBLE', 'PARCIAL']).count()
    
    if total_items > 0:
        porcentaje_surtimiento = (items_surtidos / total_items) * 100
    else:
        porcentaje_surtimiento = 0
    
    context = {
        'propuesta': propuesta,
        'total_items': total_items,
        'items_surtidos': items_surtidos,
        'items_disponibles': items_disponibles,
        'porcentaje_surtimiento': porcentaje_surtimiento,
        'puede_generar_acuse': porcentaje_surtimiento == 100
    }
    
    return render(request, 'inventario/detalle_propuesta_surtimiento.html', context)


@login_required
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
        topMargin=1.2*inch,
        bottomMargin=0.8*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()

    # ============ ENCABEZADO ============
    import os
    from django.conf import settings
    logo_path = os.path.join(settings.BASE_DIR, 'templates', 'inventario', 'images', 'logo_imss.jpg')
    logo = Image(logo_path, width=6.0*inch, height=0.8*inch)
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
        textColor=colors.white,
        alignment=1,
        spaceAfter=10
    )
    
    title = Paragraph('ACUSE DE ENTREGA', title_style)
    title_table = Table([[title]], colWidths=[10*inch])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1f77b4')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 0.1*inch))
    
    # ============ TABLA DE ITEMS ============
    table_data = [
        ['#', 'CLAVE CNIS', 'DESCRIPCIÓN', 'U.M.', 'TIPO', 'LOTE', 'CADUCIDAD', 'CLASIFICACIÓN', 'UBICACIÓN', 'CANTIDAD', 'OBSERVACIONES']
    ]
    
    idx = 1
    for item in propuesta.items.all():
        # Obtener lotes asignados
        lotes_asignados = item.lotes_asignados.all()
        
        for lote_asignado in lotes_asignados:
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            
            # Información de ubicación
            ubicacion = lote_ubicacion.ubicacion.codigo if lote_ubicacion.ubicacion else 'N/A'
            
            # Información de caducidad
            caducidad = lote.fecha_caducidad.strftime("%d/%m/%Y") if lote.fecha_caducidad else 'N/A'
            
            # Información de lote
            lote_info = lote.numero_lote if lote.numero_lote else 'N/A'
            
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
            idx += 1
    
    # Usar el mismo ancho que la tabla de firmas (10 pulgadas total)
    table = Table(table_data, colWidths=[
        0.3*inch, 0.8*inch, 1.5*inch, 0.8*inch, 0.7*inch, 
        0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.8*inch
    ])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    # Función para agregar header solo en páginas siguientes
    def header_later_pages(canvas, doc):
        canvas.saveState()
        
        # Agregar logo en páginas siguientes
        logo_path = os.path.join(settings.BASE_DIR, 'templates', 'inventario', 'images', 'logo_imss.jpg')
        canvas.drawImage(logo_path, 0.5*inch, doc.height + 0.4*inch, width=6.0*inch, height=0.8*inch)
        
        # Agregar información de folio
        canvas.setFont('Helvetica', 8)
        info_line = f"#FOLIO: {folio} | TRANSFERENCIA: prueba | FOLIO DE PEDIDO: {folio_pedido} | FECHA: {fecha_actual} | TIPO: TRANSFERENCIA (SURTIMIENTO)"
        canvas.drawString(0.5*inch, doc.height + 0.15*inch, info_line)
        
        # Agregar linea divisoria
        canvas.setLineWidth(0.5)
        canvas.line(0.5*inch, doc.height, doc.width + 0.5*inch, doc.height)
        
        # Agregar numero de pagina
        canvas.setFont('Helvetica', 8)
        canvas.drawString(doc.width + 0.2*inch, 0.5 * inch, f"Página {doc.page}")
        
        canvas.restoreState()

    # Generar PDF
    doc.build(elements, onFirstPage=lambda c, d: None, onLaterPages=header_later_pages)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="acuse_entrega_{folio}.pdf"'
    
    return response
