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
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.template.loader import get_template
from django.conf import settings
from datetime import datetime
from xhtml2pdf import pisa
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO
import os

from .pedidos_models import PropuestaPedido, ItemPropuesta, LoteAsignado
from .models import Lote, UbicacionAlmacen, Almacen
from .decorators_roles import requiere_rol
from .fase5_utils import generar_movimientos_suministro
from .excel_to_pdf_converter import convertir_excel_a_pdf


# ============================================================
# DASHBOARD DE PICKING
# ============================================================

@requiere_rol('Almacenista', 'Administrador', 'Gestor de Inventario')
def dashboard_picking(request):
    """
    Dashboard de picking - Muestra propuestas disponibles para picking
    Optimizado para tablet
    """
    
    # Obtener propuestas en estado REVISADA o EN_SURTIMIENTO
    propuestas = PropuestaPedido.objects.filter(
        estado__in=['REVISADA', 'EN_SURTIMIENTO']
    ).select_related('solicitud').order_by('-fecha_generacion')
    
    # Filtros
    almacen_filter = request.GET.get('almacen')
    if almacen_filter:
        propuestas = propuestas.filter(solicitud__almacen_destino_id=almacen_filter)
    
    estado_filter = request.GET.get('estado')
    if estado_filter:
        propuestas = propuestas.filter(estado=estado_filter)
    
    # Búsqueda
    busqueda = request.GET.get('q')
    if busqueda:
        propuestas = propuestas.filter(
            Q(solicitud__folio__icontains=busqueda) |
            Q(solicitud__institucion_solicitante__nombre__icontains=busqueda)
        )
    
    # Contar items por propuesta
    propuestas_con_items = []
    for prop in propuestas:
        total_items = prop.items.count()
        propuestas_con_items.append({
            'propuesta': prop,
            'total_items': total_items,
            'items_pendientes': prop.items.filter(estado__in=['DISPONIBLE', 'PARCIAL']).count()
        })
    
    # Obtener almacenes para filtro
    almacenes = Almacen.objects.all()
    
    context = {
        'propuestas': propuestas_con_items,
        'almacenes': almacenes,
        'almacen_filter': almacen_filter,
        'estado_filter': estado_filter,
        'busqueda': busqueda,
    }
    
    return render(request, 'inventario/picking/dashboard_picking.html', context)


# ============================================================
# VISTA DE PICKING OPTIMIZADA
# ============================================================

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
        return redirect('logistica:detalle_propuesta', propuesta_id=propuesta_id)
    
    # Obtener orden de picking
    orden_picking = request.GET.get('orden', 'ubicacion')  # ubicacion, producto, cantidad
    
    # Obtener items de la propuesta con lotes asignados
    items_picking = []
    
    for item in propuesta.items.all():
        for lote_asignado in item.lotes_asignados.filter(surtido=False):
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            caducidad = lote.fecha_caducidad.strftime('%d/%m/%Y') if lote.fecha_caducidad else 'N/A'
            items_picking.append({
                'item_id': item.id,
                'lote_asignado_id': lote_asignado.id,
                'producto': lote.producto.descripcion,
                'cantidad': lote_asignado.cantidad_asignada,
                'lote_numero': lote.numero_lote,
                'almacen': lote_ubicacion.ubicacion.almacen.nombre,
                'almacen_id': lote_ubicacion.ubicacion.almacen_id,
                'ubicacion': lote_ubicacion.ubicacion.codigo,
                'ubicacion_id': lote_ubicacion.ubicacion_id,
                'clave_cnis': lote.producto.clave_cnis,
                'caducidad': caducidad,
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
# MARCAR ITEM COMO RECOGIDO (AJAX)
# ============================================================

@login_required
@csrf_exempt
@require_http_methods(['POST'])
def marcar_item_recogido(request, lote_asignado_id):
    """
    Marca un item como recogido en la vista de picking
    Verifica si todos los items están recogidos y completa la propuesta
    """
    
    try:
        lote_asignado = LoteAsignado.objects.get(id=lote_asignado_id)
        propuesta = lote_asignado.item_propuesta.propuesta
        
        lote_asignado.surtido = True
        lote_asignado.fecha_surtimiento = timezone.now()
        lote_asignado.save()
        
        # Verificar si todos los items de la propuesta están recogidos
        total_lotes = LoteAsignado.objects.filter(
            item_propuesta__propuesta=propuesta
        ).count()
        
        lotes_recogidos = LoteAsignado.objects.filter(
            item_propuesta__propuesta=propuesta,
            surtido=True
        ).count()
        
        propuesta_completada = False
        
        if total_lotes == lotes_recogidos and total_lotes > 0:
            # Todos los items han sido recogidos
            propuesta.estado = 'SURTIDA'
            propuesta.fecha_surtimiento = timezone.now()
            propuesta.usuario_surtimiento = request.user
            propuesta.save()
            
            # Generar movimientos de inventario
            resultado = generar_movimientos_suministro(propuesta.id, request.user)
            propuesta_completada = True
            
            return JsonResponse({
                'exito': resultado['exito'],
                'mensaje': f"Item marcado. {resultado['mensaje']}",
                'propuesta_completada': propuesta_completada,
                'lotes_recogidos': lotes_recogidos,
                'total_lotes': total_lotes,
                'movimientos_creados': resultado.get('movimientos_creados', 0)
            })
        
        return JsonResponse({
            'exito': True,
            'mensaje': 'Item marcado como recogido',
            'propuesta_completada': propuesta_completada,
            'lotes_recogidos': lotes_recogidos,
            'total_lotes': total_lotes
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


# ============================================================
# IMPRIMIR HOJA DE SURTIDO
# ============================================================

@login_required
def imprimir_hoja_surtido(request, propuesta_id):
    """
    Genera un PDF con la hoja de picking ordenada por ubicación.
    Genera el Excel primero y luego lo convierte a PDF usando weasyprint.
    """
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    
    # Obtener items de la propuesta con lotes asignados
    items_picking = []
    
    for item in propuesta.items.all():
        for lote_asignado in item.lotes_asignados.filter(surtido=False):
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            caducidad = lote.fecha_caducidad.strftime('%d/%m/%Y') if lote.fecha_caducidad else 'N/A'
            items_picking.append({
                'item_id': item.id,
                'lote_asignado_id': lote_asignado.id,
                'producto': lote.producto.descripcion,
                'cantidad': lote_asignado.cantidad_asignada,
                'lote_numero': lote.numero_lote,
                'almacen': lote_ubicacion.ubicacion.almacen.nombre,
                'almacen_id': lote_ubicacion.ubicacion.almacen_id,
                'ubicacion': lote_ubicacion.ubicacion.codigo,
                'ubicacion_id': lote_ubicacion.ubicacion_id,
                'clave_cnis': lote.producto.clave_cnis,
                'caducidad': caducidad,
            })
    
    # Ordenar por ubicación
    items_picking.sort(key=lambda x: (x['almacen_id'], x['ubicacion_id']))
    
    try:
        # Generar Excel
        excel_buffer = exportar_picking_excel_interno(propuesta, items_picking)
        
        # Convertir Excel a PDF usando weasyprint
        pdf_buffer = convertir_excel_a_pdf(excel_buffer)
        
        # Retornar PDF
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="picking_{propuesta.solicitud.folio}.pdf"'
        return response
        
    except Exception as e:
        return HttpResponse(f'Error al generar PDF: {str(e)}', status=500)



# ============================================================
# FUNCIÓN INTERNA PARA GENERAR EXCEL
# ============================================================

def exportar_picking_excel_interno(propuesta, items_picking):
    """
    Función interna que genera el Excel sin retornar HttpResponse.
    Usada tanto por exportar_picking_excel como por imprimir_hoja_surtido.
    
    Returns:
        BytesIO: Buffer con el contenido del Excel
    """
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Picking"
    
    # Definir estilos
    header_fill = PatternFill(start_color="1f77b4", end_color="1f77b4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    center_alignment = Alignment(horizontal="center", vertical="center")
    
    # Agregar información de la propuesta
    ws['A1'] = "HOJA DE PICKING"
    ws['A1'].font = Font(bold=True, size=14, color="8B1538")
    ws.merge_cells('A1:G1')
    
    ws['A3'] = "Propuesta:"
    ws['B3'] = str(propuesta.solicitud.folio)
    ws['C3'] = "Institución Solicitante:"
    ws['D3'] = propuesta.solicitud.institucion_solicitante.denominacion if propuesta.solicitud.institucion_solicitante else "N/A"
    
    ws['A4'] = "Fecha:"
    ws['B4'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    ws['C4'] = "Folio de Pedido:"
    ws['D4'] = propuesta.solicitud.observaciones_solicitud or "N/A"
    
    ws['A5'] = "Área:"
    ws['B5'] = propuesta.solicitud.almacen_destino.nombre if propuesta.solicitud.almacen_destino else "N/A"
    ws['C5'] = "Total Items:"
    ws['D5'] = len(items_picking)
    
    # Definir anchos de columnas
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 12 * 6
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 30
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 20
    
    # Agregar encabezados
    headers = ['UBICACIÓN', 'CLAVE CNIS', 'PRODUCTO', 'CADUCIDAD', 'LOTE', 'CANTIDAD', 'CANTIDAD SURTIDA']
    header_row = 8
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    ws.row_dimensions[header_row].height = 25
    
    # Agregar datos
    for row_num, item in enumerate(items_picking, header_row + 1):
        # Ubicación
        cell_a = ws.cell(row=row_num, column=1)
        cell_a.value = item['ubicacion']
        cell_a.alignment = center_alignment
        cell_a.font = Font(bold=True)
        cell_a.border = border
        
        # Clave CNIS
        cell_b = ws.cell(row=row_num, column=2)
        cell_b.value = item['clave_cnis']
        cell_b.alignment = center_alignment
        cell_b.border = border
        
        # Producto
        cell_c = ws.cell(row=row_num, column=3)
        cell_c.value = item['producto']
        cell_c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        cell_c.border = border
        num_lines = len(str(item['producto']).split('\n')) + (len(str(item['producto'])) // 100)
        ws.row_dimensions[row_num].height = max(25, num_lines * 15)
        
        # Caducidad
        cell_d = ws.cell(row=row_num, column=4)
        cell_d.value = item['caducidad']
        cell_d.alignment = center_alignment
        cell_d.border = border
        
        # Lote
        cell_e = ws.cell(row=row_num, column=5)
        cell_e.value = item['lote_numero']
        cell_e.alignment = center_alignment
        cell_e.border = border
        
        # Cantidad
        cell_f = ws.cell(row=row_num, column=6)
        cell_f.value = item['cantidad']
        cell_f.alignment = center_alignment
        cell_f.font = Font(bold=True)
        cell_f.fill = PatternFill(start_color="e8f4f8", end_color="e8f4f8", fill_type="solid")
        cell_f.border = border
        
        # Cantidad Surtida (vacío)
        cell_g = ws.cell(row=row_num, column=7)
        cell_g.value = ""
        cell_g.alignment = center_alignment
        cell_g.border = border
    
    # Crear respuesta
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output


# ============================================================
# EXPORTAR HOJA DE PICKING A EXCEL
# ============================================================

@login_required
def exportar_picking_excel(request, propuesta_id):
    """
    Genera un archivo Excel con la hoja de picking ordenada por ubicación.
    Versión 2.0: Sin template, con encabezados en fila 8.
    """
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    
    # Obtener items de la propuesta con lotes asignados
    items_picking = []
    
    for item in propuesta.items.all():
        for lote_asignado in item.lotes_asignados.filter(surtido=False):
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            caducidad = lote.fecha_caducidad.strftime('%d/%m/%Y') if lote.fecha_caducidad else 'N/A'
            items_picking.append({
                'item_id': item.id,
                'lote_asignado_id': lote_asignado.id,
                'producto': lote.producto.descripcion,
                'cantidad': lote_asignado.cantidad_asignada,
                'lote_numero': lote.numero_lote,
                'almacen': lote_ubicacion.ubicacion.almacen.nombre,
                'almacen_id': lote_ubicacion.ubicacion.almacen_id,
                'ubicacion': lote_ubicacion.ubicacion.codigo,
                'ubicacion_id': lote_ubicacion.ubicacion_id,
                'clave_cnis': lote.producto.clave_cnis,
                'caducidad': caducidad,
            })
    
    # Ordenar por ubicación
    items_picking.sort(key=lambda x: (x['almacen_id'], x['ubicacion_id']))
    
    # Crear workbook - Versión sin template
    wb = Workbook()
    ws = wb.active
    ws.title = "Picking"
    
    # Definir estilos
    header_fill = PatternFill(start_color="1f77b4", end_color="1f77b4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    center_alignment = Alignment(horizontal="center", vertical="center")
    left_alignment = Alignment(horizontal="left", vertical="center")
    
    # Agregar información de la propuesta
    ws['A1'] = "HOJA DE PICKING"
    ws['A1'].font = Font(bold=True, size=14, color="8B1538")
    ws.merge_cells('A1:G1')
    
    ws['A3'] = "Propuesta:"
    ws['B3'] = str(propuesta.solicitud.folio)
    ws['C3'] = "Institución Solicitante:"
    ws['D3'] = propuesta.solicitud.institucion_solicitante.denominacion if propuesta.solicitud.institucion_solicitante else "N/A"
    
    ws['A4'] = "Fecha:"
    ws['B4'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    ws['C4'] = "Folio de Pedido:"
    ws['D4'] = propuesta.solicitud.observaciones_solicitud or "N/A"
    
    ws['A5'] = "Área:"
    ws['B5'] = propuesta.solicitud.almacen_destino.nombre if propuesta.solicitud.almacen_destino else "N/A"
    ws['C5'] = "Total Items:"
    ws['D5'] = len(items_picking)
    
    # Definir anchos de columnas
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 12 * 6  # Aumentar 6 veces el ancho para PRODUCTO
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 30
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 20
    
    # Agregar encabezados
    headers = ['UBICACIÓN', 'CLAVE CNIS', 'PRODUCTO', 'CADUCIDAD', 'LOTE', 'CANTIDAD', 'CANTIDAD SURTIDA']
    header_row = 8
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # Establecer altura del encabezado
    ws.row_dimensions[header_row].height = 25
    
    # Agregar datos
    for row_num, item in enumerate(items_picking, header_row + 1):
        # Ubicación
        cell_a = ws.cell(row=row_num, column=1)
        cell_a.value = item['ubicacion']
        cell_a.alignment = center_alignment
        cell_a.font = Font(bold=True)
        cell_a.border = border
        
        # Clave CNIS
        cell_b = ws.cell(row=row_num, column=2)
        cell_b.value = item['clave_cnis']
        cell_b.alignment = center_alignment
        cell_b.border = border
        
        # Producto
        cell_c = ws.cell(row=row_num, column=3)
        cell_c.value = item['producto']
        cell_c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        cell_c.border = border
        # Calcular altura basada en el número de líneas de texto
        num_lines = len(str(item['producto']).split('\n')) + (len(str(item['producto'])) // 100)
        ws.row_dimensions[row_num].height = max(25, num_lines * 15)
        
        # Caducidad
        cell_d = ws.cell(row=row_num, column=4)
        cell_d.value = item['caducidad']
        cell_d.alignment = center_alignment
        cell_d.border = border
        
        # Lote
        cell_e = ws.cell(row=row_num, column=5)
        cell_e.value = item['lote_numero']
        cell_e.alignment = center_alignment
        cell_e.border = border
        
        # Cantidad
        cell_f = ws.cell(row=row_num, column=6)
        cell_f.value = item['cantidad']
        cell_f.alignment = center_alignment
        cell_f.font = Font(bold=True)
        cell_f.fill = PatternFill(start_color="e8f4f8", end_color="e8f4f8", fill_type="solid")
        cell_f.border = border
        
        # Cantidad Surtida (vacío)
        cell_g = ws.cell(row=row_num, column=7)
        cell_g.value = ""
        cell_g.alignment = center_alignment
        cell_g.border = border
        

    # Crear respuesta
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="picking_{propuesta.solicitud.folio}.xlsx"'
    
    return response
