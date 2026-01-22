"""
Vistas para reporte de lotes y pedidos asociados.
Permite buscar un lote específico y ver todos los pedidos donde está asignado.

Relaciones:
- Producto (clave_cnis) -> Lote (numero_lote) -> LoteUbicacion -> LoteAsignado -> ItemPropuesta -> PropuestaPedido -> SolicitudPedido
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q, Sum, F, DecimalField, Case, When, Value
from django.db.models.functions import Coalesce
from datetime import date
import logging

from .models import Lote, Producto, LoteUbicacion
from .pedidos_models import ItemPropuesta, LoteAsignado, PropuestaPedido, ItemSolicitud
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


@login_required
def reporte_lote_pedidos(request):
    """
    Reporte de lote y pedidos asociados.
    Permite buscar un lote específico y ver todos los pedidos donde está asignado.
    """
    
    # Obtener parámetros de búsqueda
    filtro_clave = request.GET.get('clave', '').strip()
    filtro_lote = request.GET.get('lote', '').strip()
    
    datos_lote = None
    datos_pedidos = []
    total_reservado = 0
    total_surtido = 0
    
    # Si hay filtros, buscar el lote
    if filtro_clave or filtro_lote:
        # PASO 1: Buscar el Producto por clave
        query_producto = Producto.objects.all()
        
        if filtro_clave:
            query_producto = query_producto.filter(
                Q(clave_cnis__icontains=filtro_clave) |
                Q(descripcion__icontains=filtro_clave)
            )
        
        if query_producto.exists():
            # PASO 2: Buscar el Lote por número y producto
            query_lote = Lote.objects.select_related(
                'producto',
                'institucion',
                'almacen'
            ).filter(
                producto__in=query_producto
            )
            
            if filtro_lote:
                query_lote = query_lote.filter(numero_lote__icontains=filtro_lote)
            
            # Si hay un único lote, mostrar sus pedidos
            if query_lote.count() == 1:
                lote = query_lote.first()
                
                # Preparar datos del lote
                datos_lote = {
                    'lote_id': lote.id,
                    'clave': lote.producto.clave_cnis,
                    'descripcion': lote.producto.descripcion,
                    'numero_lote': lote.numero_lote,
                    'institucion': lote.institucion.denominacion if lote.institucion else 'N/A',
                    'cantidad_disponible': lote.cantidad_disponible,
                    'cantidad_reservada': lote.cantidad_reservada,
                    'cantidad_neta': max(0, lote.cantidad_disponible - lote.cantidad_reservada),
                    'fecha_caducidad': lote.fecha_caducidad,
                    'precio_unitario': lote.precio_unitario,
                    'valor_total': lote.valor_total,
                }
                
                # PASO 3: Buscar LoteUbicacion para este lote
                lotes_ubicacion = LoteUbicacion.objects.filter(lote_id=lote.id)
                
                if lotes_ubicacion.exists():
                    # PASO 4: Buscar LoteAsignado que usan esos LoteUbicacion
                    lotes_asignados = LoteAsignado.objects.filter(
                        lote_ubicacion_id__in=lotes_ubicacion.values_list('id', flat=True)
                    ).select_related(
                        'item_propuesta__propuesta__solicitud',
                        'item_propuesta__producto',
                        'lote_ubicacion__lote'
                    )
                    
                    if lotes_asignados.exists():
                        # PASO 5: Procesar LoteAsignado y agrupar por PropuestaPedido
                        pedidos_dict = {}
                        
                        for lote_asignado in lotes_asignados:
                            try:
                                item_prop = lote_asignado.item_propuesta
                                propuesta = item_prop.propuesta
                                solicitud = propuesta.solicitud
                                
                                # Clave única del pedido
                                pedido_key = propuesta.id
                                
                                if pedido_key not in pedidos_dict:
                                    pedidos_dict[pedido_key] = {
                                        'propuesta_id': propuesta.id,
                                        'solicitud_folio': solicitud.observaciones_solicitud if solicitud.observaciones_solicitud else solicitud.folio,
                                        'institucion_solicitante': solicitud.institucion_solicitante.denominacion,
                                        'estado_propuesta': propuesta.get_estado_display(),
                                        'fecha_generacion': propuesta.fecha_generacion,
                                        'items': {}
                                    }
                                
                                # Usar diccionario para items para evitar duplicados
                                item_key = item_prop.id
                                
                                if item_key not in pedidos_dict[pedido_key]['items']:
                                    item_info = {
                                        'item_propuesta_id': item_prop.id,
                                        'producto_clave': item_prop.producto.clave_cnis,
                                        'producto_descripcion': item_prop.producto.descripcion,
                                        'cantidad_solicitada': item_prop.cantidad_solicitada,
                                        'cantidad_disponible': item_prop.cantidad_disponible,
                                        'cantidad_propuesta': item_prop.cantidad_propuesta,
                                        'cantidad_surtida': item_prop.cantidad_surtida,
                                        'estado_item': item_prop.estado,
                                        'lotes_asignados': []
                                    }
                                    pedidos_dict[pedido_key]['items'][item_key] = item_info
                                
                                # Agregar información del lote asignado
                                lote_info = {
                                    'cantidad_asignada': lote_asignado.cantidad_asignada,
                                    'fecha_asignacion': lote_asignado.fecha_asignacion,
                                    'fecha_surtimiento': lote_asignado.fecha_surtimiento,
                                    'surtido': lote_asignado.surtido,
                                    'numero_lote': lote_asignado.lote_ubicacion.lote.numero_lote,
                                }
                                
                                pedidos_dict[pedido_key]['items'][item_key]['lotes_asignados'].append(lote_info)
                                
                                # Acumular totales
                                total_reservado += item_prop.cantidad_propuesta
                                total_surtido += item_prop.cantidad_surtida
                                
                            except Exception as e:
                                logger.error(f"Error procesando lote asignado: {str(e)}")
                        
                        # Convertir dict a lista
                        for pedido_key in pedidos_dict:
                            # Convertir items dict a lista
                            pedidos_dict[pedido_key]['items'] = list(pedidos_dict[pedido_key]['items'].values())
                        
                        datos_pedidos = list(pedidos_dict.values())
    
    # Contexto
    context = {
        'page_title': 'Reporte de Lote y Pedidos',
        'filtro_clave': filtro_clave,
        'filtro_lote': filtro_lote,
        'datos_lote': datos_lote,
        'datos_pedidos': datos_pedidos,
        'total_reservado': total_reservado,
        'total_surtido': total_surtido,
        'total_pendiente': max(0, datos_lote['cantidad_neta'] - total_surtido) if datos_lote else 0,
    }
    
    return render(request, 'inventario/reportes/reporte_lote_pedidos.html', context)


@login_required
def exportar_lote_pedidos_excel(request):
    """
    Exporta el reporte de lote y pedidos asociados a Excel.
    """
    
    # Obtener parámetros de búsqueda (GET o POST)
    filtro_clave = request.POST.get('clave', request.GET.get('clave', '')).strip()
    filtro_lote = request.POST.get('lote', request.GET.get('lote', '')).strip()
    
    datos_lote = None
    datos_pedidos = []
    total_reservado = 0
    total_surtido = 0
    
    # Reutilizar la misma lógica de búsqueda que reporte_lote_pedidos
    if filtro_clave or filtro_lote:
        # PASO 1: Buscar el Producto por clave
        query_producto = Producto.objects.all()
        
        if filtro_clave:
            query_producto = query_producto.filter(
                Q(clave_cnis__icontains=filtro_clave) |
                Q(descripcion__icontains=filtro_clave)
            )
        
        if query_producto.exists():
            # PASO 2: Buscar el Lote por número y producto
            query_lote = Lote.objects.select_related(
                'producto',
                'institucion',
                'almacen'
            ).filter(
                producto__in=query_producto
            )
            
            if filtro_lote:
                query_lote = query_lote.filter(numero_lote__icontains=filtro_lote)
            
            # Si hay un único lote, mostrar sus pedidos
            if query_lote.count() == 1:
                lote = query_lote.first()
                
                # Preparar datos del lote
                datos_lote = {
                    'lote_id': lote.id,
                    'clave': lote.producto.clave_cnis,
                    'descripcion': lote.producto.descripcion,
                    'numero_lote': lote.numero_lote,
                    'institucion': lote.institucion.denominacion if lote.institucion else 'N/A',
                    'cantidad_disponible': lote.cantidad_disponible,
                    'cantidad_reservada': lote.cantidad_reservada,
                    'cantidad_neta': max(0, lote.cantidad_disponible - lote.cantidad_reservada),
                    'fecha_caducidad': lote.fecha_caducidad,
                    'precio_unitario': lote.precio_unitario,
                    'valor_total': lote.valor_total,
                }
                
                # PASO 3: Buscar LoteUbicacion para este lote
                lotes_ubicacion = LoteUbicacion.objects.filter(lote_id=lote.id)
                
                if lotes_ubicacion.exists():
                    # PASO 4: Buscar LoteAsignado que usan esos LoteUbicacion
                    lotes_asignados = LoteAsignado.objects.filter(
                        lote_ubicacion_id__in=lotes_ubicacion.values_list('id', flat=True)
                    ).select_related(
                        'item_propuesta__propuesta__solicitud',
                        'item_propuesta__producto',
                        'lote_ubicacion__lote'
                    )
                    
                    if lotes_asignados.exists():
                        # PASO 5: Procesar LoteAsignado y agrupar por PropuestaPedido
                        pedidos_dict = {}
                        
                        for lote_asignado in lotes_asignados:
                            try:
                                item_prop = lote_asignado.item_propuesta
                                propuesta = item_prop.propuesta
                                solicitud = propuesta.solicitud
                                
                                # Clave única del pedido
                                pedido_key = propuesta.id
                                
                                if pedido_key not in pedidos_dict:
                                    pedidos_dict[pedido_key] = {
                                        'propuesta_id': propuesta.id,
                                        'solicitud_folio': solicitud.observaciones_solicitud if solicitud.observaciones_solicitud else solicitud.folio,
                                        'institucion_solicitante': solicitud.institucion_solicitante.denominacion,
                                        'estado_propuesta': propuesta.get_estado_display(),
                                        'fecha_generacion': propuesta.fecha_generacion,
                                        'items': {}
                                    }
                                
                                # Usar diccionario para items para evitar duplicados
                                item_key = item_prop.id
                                
                                if item_key not in pedidos_dict[pedido_key]['items']:
                                    item_info = {
                                        'item_propuesta_id': item_prop.id,
                                        'producto_clave': item_prop.producto.clave_cnis,
                                        'producto_descripcion': item_prop.producto.descripcion,
                                        'cantidad_solicitada': item_prop.cantidad_solicitada,
                                        'cantidad_disponible': item_prop.cantidad_disponible,
                                        'cantidad_propuesta': item_prop.cantidad_propuesta,
                                        'cantidad_surtida': item_prop.cantidad_surtida,
                                        'estado_item': item_prop.estado,
                                        'lotes_asignados': []
                                    }
                                    pedidos_dict[pedido_key]['items'][item_key] = item_info
                                
                                # Agregar información del lote asignado
                                lote_info = {
                                    'cantidad_asignada': lote_asignado.cantidad_asignada,
                                    'fecha_asignacion': lote_asignado.fecha_asignacion,
                                    'fecha_surtimiento': lote_asignado.fecha_surtimiento,
                                    'surtido': lote_asignado.surtido,
                                    'numero_lote': lote_asignado.lote_ubicacion.lote.numero_lote,
                                }
                                
                                pedidos_dict[pedido_key]['items'][item_key]['lotes_asignados'].append(lote_info)
                                
                                # Acumular totales
                                total_reservado += item_prop.cantidad_propuesta
                                total_surtido += item_prop.cantidad_surtida
                                
                            except Exception as e:
                                logger.error(f"Error procesando lote asignado: {str(e)}")
                        
                        # Convertir dict a lista
                        for pedido_key in pedidos_dict:
                            # Convertir items dict a lista
                            pedidos_dict[pedido_key]['items'] = list(pedidos_dict[pedido_key]['items'].values())
                        
                        datos_pedidos = list(pedidos_dict.values())
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Lote y Pedidos"
    
    # Definir estilos
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    info_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    info_font = Font(bold=True, size=11)
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    row_num = 1
    
    # Título del reporte
    ws.merge_cells(f'A{row_num}:H{row_num}')
    ws[f'A{row_num}'] = 'REPORTE DE LOTE Y PEDIDOS ASOCIADOS'
    ws[f'A{row_num}'].font = Font(bold=True, size=14)
    ws[f'A{row_num}'].alignment = Alignment(horizontal="center", vertical="center")
    row_num += 2
    
    # Información del Lote
    if datos_lote:
        ws.merge_cells(f'A{row_num}:H{row_num}')
        ws[f'A{row_num}'] = 'INFORMACIÓN DEL LOTE'
        ws[f'A{row_num}'].font = info_font
        ws[f'A{row_num}'].fill = info_fill
        ws[f'A{row_num}'].alignment = Alignment(horizontal="center", vertical="center")
        row_num += 1
        
        # Datos del lote
        lote_data = [
            ['Clave CNIS', datos_lote['clave']],
            ['Descripción', datos_lote['descripcion']],
            ['Número de Lote', datos_lote['numero_lote']],
            ['Institución', datos_lote['institucion']],
            ['Cantidad Disponible', datos_lote['cantidad_disponible']],
            ['Cantidad Reservada', datos_lote['cantidad_reservada']],
            ['Cantidad Neta', datos_lote['cantidad_neta']],
            ['Fecha Caducidad', datos_lote['fecha_caducidad'].strftime('%d/%m/%Y') if datos_lote['fecha_caducidad'] else 'N/A'],
            ['Precio Unitario', f"${datos_lote['precio_unitario']:.2f}"],
            ['Valor Total', f"${datos_lote['valor_total']:.2f}"],
        ]
        
        for label, value in lote_data:
            ws[f'A{row_num}'] = label
            ws[f'A{row_num}'].font = Font(bold=True)
            ws[f'B{row_num}'] = value
            row_num += 1
        
        row_num += 1
    
    # Resumen de Totales
    if datos_lote:
        ws.merge_cells(f'A{row_num}:H{row_num}')
        ws[f'A{row_num}'] = 'RESUMEN DE TOTALES'
        ws[f'A{row_num}'].font = info_font
        ws[f'A{row_num}'].fill = info_fill
        ws[f'A{row_num}'].alignment = Alignment(horizontal="center", vertical="center")
        row_num += 1
        
        total_pendiente = max(0, datos_lote['cantidad_neta'] - total_surtido)
        resumen_data = [
            ['Total Reservado', total_reservado],
            ['Total Surtido', total_surtido],
            ['Pendiente de Surtir', total_pendiente],
            ['Total Pedidos', len(datos_pedidos)],
        ]
        
        for label, value in resumen_data:
            ws[f'A{row_num}'] = label
            ws[f'A{row_num}'].font = Font(bold=True)
            ws[f'B{row_num}'] = value
            row_num += 1
        
        row_num += 1
    
    # Tabla de Pedidos
    if datos_pedidos:
        ws.merge_cells(f'A{row_num}:J{row_num}')
        ws[f'A{row_num}'] = f'PEDIDOS ASOCIADOS ({len(datos_pedidos)} encontrados)'
        ws[f'A{row_num}'].font = info_font
        ws[f'A{row_num}'].fill = info_fill
        ws[f'A{row_num}'].alignment = Alignment(horizontal="center", vertical="center")
        row_num += 1
        
        # Encabezados de pedidos
        headers_pedidos = [
            'Folio Solicitud',
            'Institución',
            'Estado Propuesta',
            'Fecha Generación',
            'Cantidad Solicitada',
            'Cantidad Propuesta',
            'Cantidad Surtida',
            'Pendiente',
        ]
        
        ws.append(headers_pedidos)
        
        # Aplicar estilos a encabezados
        for col in range(1, len(headers_pedidos) + 1):
            cell = ws.cell(row=row_num, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border
        
        row_num += 1
        
        # Datos de pedidos
        for pedido in datos_pedidos:
            # Calcular totales por pedido
            total_solicitado = sum(item['cantidad_solicitada'] for item in pedido['items'])
            total_propuesto = sum(item['cantidad_propuesta'] for item in pedido['items'])
            total_surtido_pedido = sum(item['cantidad_surtida'] for item in pedido['items'])
            total_pendiente_pedido = total_propuesto - total_surtido_pedido
            
            row = [
                pedido['solicitud_folio'],
                pedido['institucion_solicitante'],
                pedido['estado_propuesta'],
                pedido['fecha_generacion'].strftime('%d/%m/%Y %H:%M') if pedido['fecha_generacion'] else 'N/A',
                total_solicitado,
                total_propuesto,
                total_surtido_pedido,
                max(0, total_pendiente_pedido),
            ]
            
            ws.append(row)
            
            # Aplicar bordes
            for col in range(1, len(row) + 1):
                cell = ws.cell(row=row_num, column=col)
                cell.border = border
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            row_num += 1
            
            # Agregar detalles de items del pedido
            if pedido['items']:
                # Encabezados de items
                ws.merge_cells(f'A{row_num}:J{row_num}')
                ws[f'A{row_num}'] = f'  Detalles de Items - Pedido {pedido["solicitud_folio"]}'
                ws[f'A{row_num}'].font = Font(bold=True, italic=True, size=10)
                ws[f'A{row_num}'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
                row_num += 1
                
                headers_items = [
                    'Producto Clave',
                    'Producto Descripción',
                    'Cantidad Solicitada',
                    'Cantidad Disponible',
                    'Cantidad Propuesta',
                    'Cantidad Surtida',
                    'Estado Item',
                    'Lotes Asignados',
                ]
                
                ws.append(headers_items)
                
                # Aplicar estilos a encabezados de items
                for col in range(1, len(headers_items) + 1):
                    cell = ws.cell(row=row_num, column=col)
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                    cell.font = Font(bold=True, size=10)
                    cell.alignment = header_alignment
                    cell.border = border
                
                row_num += 1
                
                # Datos de items
                for item in pedido['items']:
                    lotes_info = ', '.join([f"Lote: {l['numero_lote']} (Cant: {l['cantidad_asignada']})" 
                                          for l in item['lotes_asignados']])
                    
                    row = [
                        item['producto_clave'],
                        item['producto_descripcion'][:50],  # Limitar longitud
                        item['cantidad_solicitada'],
                        item['cantidad_disponible'],
                        item['cantidad_propuesta'],
                        item['cantidad_surtida'],
                        item['estado_item'],
                        lotes_info[:100],  # Limitar longitud
                    ]
                    
                    ws.append(row)
                    
                    # Aplicar bordes
                    for col in range(1, len(row) + 1):
                        cell = ws.cell(row=row_num, column=col)
                        cell.border = border
                        cell.alignment = Alignment(horizontal="left", vertical="center")
                    
                    row_num += 1
                
                row_num += 1  # Espacio entre pedidos
    
    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 18
    ws.column_dimensions['E'].width = 18
    ws.column_dimensions['F'].width = 18
    ws.column_dimensions['G'].width = 18
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 15
    ws.column_dimensions['J'].width = 50
    
    # Crear respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Nombre del archivo con información del lote si existe
    if datos_lote:
        filename = f"reporte_lote_pedidos_{datos_lote['numero_lote']}_{datos_lote['clave']}.xlsx"
    else:
        filename = "reporte_lote_pedidos.xlsx"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response
