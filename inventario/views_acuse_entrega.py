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
from .acuse_excel import generar_acuse_excel
from .acuse_excel_to_pdf import convertir_acuse_excel_a_pdf


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


def crear_header_compacto(folio, fecha, folio_pedido, institucion, styles):
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
        fontSize=6,
        textColor=colors.black,
        alignment=2,
        spaceAfter=0,
        leading=8
    )
    
    info_text = f'''#FOLIO: {folio}<br/>
TRANSFERENCIA: prueba<br/>
FOLIO DE PEDIDO: {folio_pedido}<br/>
INSTITUCIÓN: {institucion}<br/>
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
    Genera el Excel primero y luego lo convierte a PDF
    """
    # Obtener propuesta con todas sus relaciones para asegurar datos actualizados
    propuesta = get_object_or_404(
        PropuestaPedido.objects.select_related(
            'solicitud__institucion_solicitante',
            'solicitud__almacen_destino'
        ).prefetch_related(
            'items__producto',
            'items__lotes_asignados__lote_ubicacion__lote',
            'items__lotes_asignados__lote_ubicacion__ubicacion'
        ),
        id=propuesta_id
    )
    
    try:
        # Generar Excel
        excel_buffer = generar_acuse_excel(propuesta)
        
        # Convertir Excel a PDF
        pdf_buffer = convertir_acuse_excel_a_pdf(excel_buffer)
        
        # Retornar PDF
        folio = propuesta.solicitud.folio
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="acuse_entrega_{folio}.pdf"'
        return response
        
    except Exception as e:
        return HttpResponse(f'Error al generar PDF: {str(e)}', status=500)


@login_required
def generar_acuse_entrega_excel(request, propuesta_id):
    """
    Genera el Excel del Acuse de Entrega para una propuesta surtida al 100%
    """
    # Obtener propuesta con todas sus relaciones para asegurar datos actualizados
    propuesta = get_object_or_404(
        PropuestaPedido.objects.select_related(
            'solicitud__institucion_solicitante',
            'solicitud__almacen_destino'
        ).prefetch_related(
            'items__producto',
            'items__lotes_asignados__lote_ubicacion__lote',
            'items__lotes_asignados__lote_ubicacion__ubicacion'
        ),
        id=propuesta_id
    )
    
    # Generar Excel
    buffer = generar_acuse_excel(propuesta)
    
    # Obtener folio para el nombre del archivo
    folio = propuesta.solicitud.folio
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="acuse_entrega_{folio}.xlsx"'
    
    return response
