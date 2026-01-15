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
import os

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


def crear_header_compacto(folio, fecha, folio_pedido, styles):
    """
    Crea un header compacto para el PDF que se puede reutilizar en cada página
    """
    from django.conf import settings
    
    logo_path = os.path.join(settings.BASE_DIR, 'templates', 'inventario', 'images', 'logo_imss.jpg')
    logo = Image(logo_path, width=1.5*inch, height=0.4*inch)
    
    # Título del sistema
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#8B1538'),
        alignment=1,
        spaceAfter=2
    )
    title = Paragraph('Sistema de Abasto, Inventarios y Control de Almacenes', title_style)
    
    # Información de folio
    info_style = ParagraphStyle(
        'HeaderInfo',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.black,
        alignment=2,
        spaceAfter=0,
        leading=8
    )
    
    info_text = f'''#FOLIO: {folio}<br/>
TRANSFERENCIA: prueba<br/>
FOLIO DE PEDIDO: {folio_pedido}<br/>
FECHA: {fecha}<br/>
TIPO: TRANSFERENCIA (SURTIMIENTO)'''
    
    info = Paragraph(info_text, info_style)
    
    # Crear tabla con logo y título
    header_table = Table([[logo, title, info]], colWidths=[1.8*inch, 5.2*inch, 3.0*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    
    return header_table


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
    
    # Datos para el header
    folio = propuesta.solicitud.folio
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    folio_pedido = propuesta.solicitud.observaciones_solicitud or 'N/A'
    
    # ============ ENCABEZADO PRIMERA PÁGINA ============
    header_table = crear_header_compacto(folio, fecha_actual, folio_pedido, styles)
    elements.append(header_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # ============ TABLA DE FIRMAS (SOLO PRIMERA PÁGINA) ============
    firma_title_style = ParagraphStyle(
        'FirmaTitle',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#8B1538'),
        alignment=1,
        spaceAfter=8
    )
    
    firma_title = Paragraph('ACUSE DE ENTREGA', firma_title_style)
    firma_title_table = Table([[firma_title]], colWidths=[10*inch])
    firma_title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(firma_title_table)
    
    # Tabla de firmas
    firma_data = [
        ['UNIDAD DE DESTINO', 'RECIBE (UNIDAD DE DESTINO)', 'AUTORIZA (ALMACEN)', 'ENTREGA (ALMACEN)'],
        [
            propuesta.solicitud.almacen_destino.nombre if propuesta.solicitud.almacen_destino else 'N/A',
            'NOMBRE: __________________\n\nPUESTO: __________________\n\nFIRMA: __________________',
            'NOMBRE: Gerardo Anaya\n\nPUESTO: MESA DE CONTROL\n\nFIRMA: __________________',
            'NOMBRE: __________________\n\nPUESTO: __________________\n\nFIRMA: __________________'
        ]
    ]
    
    firma_table = Table(firma_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch, 2.5*inch])
    firma_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B1538')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 40),
    ]))
    
    elements.append(firma_table)
    elements.append(Spacer(1, 0.1*inch))
    
    # ============ TABLA DE ITEMS (PRIMERA PÁGINA) ============
    table_data_page1 = [
        ['#', 'CLAVE CNIS', 'DESCRIPCIÓN', 'U.M.', 'TIPO', 'LOTE', 'CADUCIDAD', 'CLASIFICACIÓN', 'UBICACIÓN', 'CANTIDAD', 'FOLIO PEDIDO']
    ]
    
    idx = 1
    for item in propuesta.items.all():
        lotes_asignados = item.lotes_asignados.all()
        for lote_asignado in lotes_asignados:
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            ubicacion = lote_ubicacion.ubicacion.codigo if lote_ubicacion.ubicacion else 'N/A'
            caducidad = lote.fecha_caducidad.strftime("%d/%m/%Y") if lote.fecha_caducidad else 'N/A'
            lote_info = lote.numero_lote if lote.numero_lote else 'N/A'
            descripcion = wrap_text(item.producto.descripcion, max_chars=20, max_lines=2)
            table_data_page1.append([
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
    
    table_page1 = Table(table_data_page1, colWidths=[
        0.3*inch, 0.8*inch, 1.5*inch, 0.8*inch, 0.7*inch, 
        0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.8*inch
    ])
    
    table_page1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B1538')),
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
    
    elements.append(table_page1)
    elements.append(PageBreak())
    
    # ============ ACUSE DE ENTREGA (SEGUNDA PÁGINA EN ADELANTE) ============
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
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#8B1538')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 0.1*inch))
    
    # ============ TABLA DE ITEMS (PÁGINAS POSTERIORES) ============
    table_data = [
        ['#', 'CLAVE CNIS', 'DESCRIPCIÓN', 'U.M.', 'TIPO', 'LOTE', 'CADUCIDAD', 'CLASIFICACIÓN', 'UBICACIÓN', 'CANTIDAD', 'FOLIO PEDIDO']
    ]
    
    idx = 1
    for item in propuesta.items.all():
        lotes_asignados = item.lotes_asignados.all()
        for lote_asignado in lotes_asignados:
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            ubicacion = lote_ubicacion.ubicacion.codigo if lote_ubicacion.ubicacion else 'N/A'
            caducidad = lote.fecha_caducidad.strftime("%d/%m/%Y") if lote.fecha_caducidad else 'N/A'
            lote_info = lote.numero_lote if lote.numero_lote else 'N/A'
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
    
    table = Table(table_data, colWidths=[
        0.3*inch, 0.8*inch, 1.5*inch, 0.8*inch, 0.7*inch, 
        0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.8*inch
    ])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B1538')),
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
    
    # Función para agregar header en páginas siguientes
    def header_pages(canvas, doc):
        canvas.saveState()
        
        if doc.page > 1:
            from django.conf import settings
            logo_path = os.path.join(settings.BASE_DIR, 'templates', 'inventario', 'images', 'logo_imss.jpg')
            
            # Dibujar logo
            canvas.drawImage(logo_path, 0.5*inch, doc.height + 0.75*inch, width=1.5*inch, height=0.4*inch)
            
            # Dibujar título
            canvas.setFont('Helvetica-Bold', 10)
            canvas.setFillColor(colors.HexColor('#8B1538'))
            title_text = 'Sistema de Abasto, Inventarios y Control de Almacenes'
            canvas.drawCentredString(5.5*inch, doc.height + 0.75*inch, title_text)
            
            # Dibujar información de folio
            canvas.setFont('Helvetica', 7)
            canvas.setFillColor(colors.black)
            info_lines = [
                f'#FOLIO: {folio}',
                f'TRANSFERENCIA: prueba',
                f'FOLIO DE PEDIDO: {folio_pedido}',
                f'FECHA: {fecha_actual}',
                f'TIPO: TRANSFERENCIA (SURTIMIENTO)'
            ]
            
            y_pos = doc.height + 0.75*inch
            for line in info_lines:
                canvas.drawRightString(doc.width + 0.5*inch, y_pos, line)
                y_pos -= 0.08*inch
            
            # Línea divisoria
            canvas.setLineWidth(0.5)
            canvas.line(0.5*inch, doc.height + 0.55*inch, doc.width + 0.5*inch, doc.height + 0.55*inch)
        
        # Número de página
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.black)
        canvas.drawString(doc.width + 0.2*inch, 0.5 * inch, f'Página {doc.page}')
        
        canvas.restoreState()

    # Generar PDF
    doc.build(elements, onFirstPage=lambda c, d: None, onLaterPages=header_pages)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="acuse_entrega_{folio}.pdf"'
    
    return response
