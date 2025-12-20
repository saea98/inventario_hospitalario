"""
Fase 6 - Optimización de Picking para Suministro
Vistas para ordenar y visualizar propuestas de forma optimizada
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, F
from django.views.decorators.http import require_http_methods
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime

from .pedidos_models import PropuestaPedido, ItemPropuesta, LoteAsignado
from .models import Lote, Ubicacion
from .decorators_roles import requiere_rol


# ============================================================
# VISTA DE PICKING OPTIMIZADA
# ============================================================

@login_required
@requiere_rol('Almacenista', 'Administrador', 'Gestor de Inventario')
def picking_propuesta(request, propuesta_id):
    """
    Vista optimizada de picking para tablet/pantalla
    Muestra los items ordenados por ubicación
    """
    
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    
    # Validar que la propuesta esté en estado correcto
    if propuesta.estado not in ['REVISADA', 'EN_SURTIMIENTO']:
        messages.error(request, 'La propuesta no está lista para picking.')
        return redirect('detalle_propuesta', pk=propuesta_id)
    
    # Obtener orden de picking
    orden_picking = request.GET.get('orden', 'ubicacion')  # ubicacion, producto, cantidad
    
    # Obtener items de la propuesta con lotes asignados
    items_picking = []
    
    for item in propuesta.items.all():
        for lote_asignado in item.lotes_asignados.filter(surtido=False):
            lote = lote_asignado.lote
            items_picking.append({
                'item_id': item.id,
                'lote_asignado_id': lote_asignado.id,
                'producto': lote.producto.descripcion,
                'cantidad': lote_asignado.cantidad_asignada,
                'lote_numero': lote.numero_lote,
                'almacen': lote.almacen.nombre,
                'almacen_id': lote.almacen_id,
                'ubicacion': lote.ubicacion.nombre if lote.ubicacion else 'Sin ubicación',
                'ubicacion_id': lote.ubicacion_id if lote.ubicacion else 0,
                'clave_cnis': lote.producto.clave_cnis,
            })
    
    # Ordenar según parámetro
    if orden_picking == 'producto':
        items_picking.sort(key=lambda x: x['producto'])
    elif orden_picking == 'cantidad':
        items_picking.sort(key=lambda x: x['cantidad'], reverse=True)
    else:  # ubicacion (predeterminado)
        items_picking.sort(key=lambda x: (x['almacen_id'], x['ubicacion_id']))
    
    # Agrupar por ubicación para vista
    ubicaciones_agrupadas = {}
    for item in items_picking:
        key = f"{item['almacen']} - {item['ubicacion']}"
        if key not in ubicaciones_agrupadas:
            ubicaciones_agrupadas[key] = []
        ubicaciones_agrupadas[key].append(item)
    
    context = {
        'propuesta': propuesta,
        'items_picking': items_picking,
        'ubicaciones_agrupadas': ubicaciones_agrupadas,
        'orden_picking': orden_picking,
        'total_items': len(items_picking),
    }
    
    return render(request, 'inventario/picking/picking_propuesta.html', context)


# ============================================================
# GENERAR PICKING LIST (PDF)
# ============================================================

@login_required
@requiere_rol('Almacenista', 'Administrador', 'Gestor de Inventario')
def generar_picking_pdf(request, propuesta_id):
    """
    Genera un PDF optimizado para impresora térmica
    """
    
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    
    # Obtener items de la propuesta
    items_picking = []
    
    for item in propuesta.items.all():
        for lote_asignado in item.lotes_asignados.filter(surtido=False):
            lote = lote_asignado.lote
            items_picking.append({
                'producto': lote.producto.descripcion,
                'cantidad': lote_asignado.cantidad_asignada,
                'lote_numero': lote.numero_lote,
                'almacen': lote.almacen.nombre,
                'ubicacion': lote.ubicacion.nombre if lote.ubicacion else 'Sin ubicación',
                'clave_cnis': lote.producto.clave_cnis,
                'almacen_id': lote.almacen_id,
                'ubicacion_id': lote.ubicacion_id if lote.ubicacion else 0,
            })
    
    # Ordenar por ubicación
    items_picking.sort(key=lambda x: (x['almacen_id'], x['ubicacion_id']))
    
    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=10,
        alignment=TA_CENTER,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=8,
        spaceBefore=8,
    )
    
    # Contenido del PDF
    elements = []
    
    # Título
    elements.append(Paragraph("PICKING LIST", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Información de la propuesta
    info_data = [
        ['Propuesta:', str(propuesta.solicitud.folio)],
        ['Fecha:', datetime.now().strftime('%d/%m/%Y %H:%M')],
        ['Total Items:', str(len(items_picking))],
    ]
    
    info_table = Table(info_data, colWidths=[1.5*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Tabla de items
    table_data = [['UBICACIÓN', 'PRODUCTO', 'CANT.', 'LOTE']]
    
    for item in items_picking:
        ubicacion_str = f"{item['almacen']}\n{item['ubicacion']}"
        producto_str = f"{item['producto']}\n({item['clave_cnis']})"
        
        table_data.append([
            ubicacion_str,
            producto_str,
            str(item['cantidad']),
            item['lote_numero'],
        ])
    
    table = Table(table_data, colWidths=[1.5*inch, 2.5*inch, 0.8*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    elements.append(table)
    
    # Construir PDF
    doc.build(elements)
    
    # Retornar PDF
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="picking_{propuesta.solicitud.folio}.pdf"'
    
    return response


# ============================================================
# MARCAR ITEM COMO RECOGIDO (AJAX)
# ============================================================

@login_required
@require_http_methods(['POST'])
def marcar_item_recogido(request, lote_asignado_id):
    """
    Marca un item como recogido en la vista de picking
    """
    
    try:
        lote_asignado = LoteAsignado.objects.get(id=lote_asignado_id)
        lote_asignado.surtido = True
        lote_asignado.save()
        
        return JsonResponse({
            'exito': True,
            'mensaje': 'Item marcado como recogido'
        })
    
    except LoteAsignado.DoesNotExist:
        return JsonResponse({
            'exito': False,
            'mensaje': 'Item no encontrado'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'mensaje': f'Error: {str(e)}'
        }, status=500)
