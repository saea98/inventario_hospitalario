"""
Reporte de Entradas al Inventario

Muestra todas las entradas (MovimientoInventario con tipo ENTRADA) 
con filtros por rango de fecha, clave, lote, proveedor, etc.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from .models import MovimientoInventario, Institucion, Almacen, Proveedor, UbicacionAlmacen


@login_required
def reporte_entradas(request):
    """
    Reporte de entradas al inventario.
    Muestra todos los MovimientoInventario con tipo ENTRADA.
    """
    
    # Obtener todos los movimientos de entrada
    entradas = MovimientoInventario.objects.filter(
        tipo_movimiento='ENTRADA'
    ).select_related(
        'lote',
        'lote__producto',
        'lote__institucion',
        'lote__almacen',
        'lote__ubicacion',
        'usuario'
    ).order_by('-fecha_movimiento')
    
    # Filtros
    filtro_fecha_desde = request.GET.get('fecha_desde', '')
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '')
    filtro_clave = request.GET.get('clave', '').strip()
    filtro_lote = request.GET.get('lote', '').strip()
    filtro_institucion = request.GET.get('institucion', '')
    filtro_almacen = request.GET.get('almacen', '')
    filtro_ubicacion = request.GET.get('ubicacion', '')
    filtro_proveedor = request.GET.get('proveedor', '')
    
    # Aplicar filtro de fecha desde
    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d').date()
            entradas = entradas.filter(fecha_movimiento__date__gte=fecha_desde)
        except ValueError:
            pass
    
    # Aplicar filtro de fecha hasta
    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d').date()
            # Sumar 1 día para incluir todo el día hasta
            fecha_hasta = fecha_hasta + timedelta(days=1)
            entradas = entradas.filter(fecha_movimiento__date__lt=fecha_hasta)
        except ValueError:
            pass
    
    # Aplicar filtro de clave
    if filtro_clave:
        entradas = entradas.filter(lote__producto__clave_cnis__icontains=filtro_clave)
    
    # Aplicar filtro de lote
    if filtro_lote:
        entradas = entradas.filter(lote__numero_lote__icontains=filtro_lote)
    
    # Aplicar filtro de institución
    if filtro_institucion:
        entradas = entradas.filter(lote__institucion__denominacion=filtro_institucion)
    
    # Aplicar filtro de almacén
    if filtro_almacen:
        entradas = entradas.filter(lote__almacen__nombre=filtro_almacen)
    
    # Aplicar filtro de ubicación
    if filtro_ubicacion:
        entradas = entradas.filter(lote__ubicacion_id=filtro_ubicacion)
    
    # Aplicar filtro de proveedor (buscar en documento_referencia o motivo)
    if filtro_proveedor:
        entradas = entradas.filter(
            Q(documento_referencia__icontains=filtro_proveedor) |
            Q(motivo__icontains=filtro_proveedor)
        )
    
    # Convertir a lista para procesamiento
    entradas_lista = []
    total_cantidad = 0
    total_valor = 0
    
    for entrada in entradas:
        valor_total = entrada.cantidad * entrada.lote.precio_unitario if entrada.lote.precio_unitario else 0
        total_cantidad += entrada.cantidad
        total_valor += valor_total
        
        entradas_lista.append({
            'id': entrada.id,
            'fecha': entrada.fecha_movimiento.strftime('%d/%m/%Y %H:%M'),
            'clave_cnis': entrada.lote.producto.clave_cnis if entrada.lote.producto else '-',
            'descripcion_producto': entrada.lote.producto.descripcion if entrada.lote.producto else '-',
            'lote': entrada.lote.numero_lote,
            'institucion': entrada.lote.institucion.denominacion if entrada.lote.institucion else '-',
            'almacen': entrada.lote.almacen.nombre if entrada.lote.almacen else '-',
            'cantidad': entrada.cantidad,
            'precio_unitario': entrada.lote.precio_unitario or 0,
            'valor_total': valor_total,
            'documento_referencia': entrada.documento_referencia or '-',
            'motivo': entrada.motivo or '-',
            'usuario': entrada.usuario.username if entrada.usuario else '-',
            'fecha_caducidad': entrada.lote.fecha_caducidad.strftime('%d/%m/%Y') if entrada.lote.fecha_caducidad else '-',
            'fecha_fabricacion': entrada.lote.fecha_fabricacion.strftime('%d/%m/%Y') if entrada.lote.fecha_fabricacion else '-',
        })
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(entradas_lista, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener opciones de filtro
    instituciones = Institucion.objects.all().order_by('denominacion')
    almacenes = Almacen.objects.all().order_by('nombre')
    ubicaciones = UbicacionAlmacen.objects.filter(activo=True).select_related('almacen').order_by('almacen__nombre', 'codigo')
    
    context = {
        'page_obj': page_obj,
        'total_registros': len(entradas_lista),
        'total_cantidad': total_cantidad,
        'total_valor': total_valor,
        'instituciones': instituciones,
        'almacenes': almacenes,
        'ubicaciones': ubicaciones,
        'filtro_fecha_desde': filtro_fecha_desde,
        'filtro_fecha_hasta': filtro_fecha_hasta,
        'filtro_clave': filtro_clave,
        'filtro_lote': filtro_lote,
        'filtro_institucion': filtro_institucion,
        'filtro_almacen': filtro_almacen,
        'filtro_ubicacion': filtro_ubicacion,
        'filtro_proveedor': filtro_proveedor,
    }
    
    return render(request, 'inventario/reporte_entradas.html', context)


@login_required
def exportar_entradas_excel(request):
    """
    Exporta el reporte de entradas a Excel.
    """
    
    # Obtener todos los movimientos de entrada
    entradas = MovimientoInventario.objects.filter(
        tipo_movimiento='ENTRADA'
    ).select_related(
        'lote',
        'lote__producto',
        'lote__institucion',
        'lote__almacen',
        'lote__ubicacion',
        'usuario'
    ).order_by('-fecha_movimiento')
    
    # Filtros
    filtro_fecha_desde = request.GET.get('fecha_desde', '')
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '')
    filtro_clave = request.GET.get('clave', '').strip()
    filtro_lote = request.GET.get('lote', '').strip()
    filtro_institucion = request.GET.get('institucion', '')
    filtro_almacen = request.GET.get('almacen', '')
    filtro_ubicacion = request.GET.get('ubicacion', '')
    filtro_proveedor = request.GET.get('proveedor', '')
    
    # Aplicar filtros
    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d').date()
            entradas = entradas.filter(fecha_movimiento__date__gte=fecha_desde)
        except ValueError:
            pass
    
    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d').date()
            fecha_hasta = fecha_hasta + timedelta(days=1)
            entradas = entradas.filter(fecha_movimiento__date__lt=fecha_hasta)
        except ValueError:
            pass
    
    if filtro_clave:
        entradas = entradas.filter(lote__producto__clave_cnis__icontains=filtro_clave)
    
    if filtro_lote:
        entradas = entradas.filter(lote__numero_lote__icontains=filtro_lote)
    
    if filtro_institucion:
        entradas = entradas.filter(lote__institucion__denominacion=filtro_institucion)
    
    if filtro_almacen:
        entradas = entradas.filter(lote__almacen__nombre=filtro_almacen)
    
    if filtro_ubicacion:
        entradas = entradas.filter(lote__ubicacion_id=filtro_ubicacion)
    
    if filtro_proveedor:
        entradas = entradas.filter(
            Q(documento_referencia__icontains=filtro_proveedor) |
            Q(motivo__icontains=filtro_proveedor)
        )
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Entradas"
    
    # Estilos
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    total_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    total_font = Font(bold=True, size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Encabezados
    headers = [
        'FECHA',
        'CLAVE CNIS',
        'DESCRIPCIÓN PRODUCTO',
        'LOTE',
        'INSTITUCIÓN',
        'ALMACÉN',
        'CANTIDAD',
        'PRECIO UNITARIO',
        'VALOR TOTAL',
        'DOCUMENTO REFERENCIA',
        'MOTIVO',
        'USUARIO',
        'FECHA CADUCIDAD',
        'FECHA FABRICACIÓN'
    ]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border
    
    # Datos
    total_cantidad = 0
    total_valor = 0
    
    for row, entrada in enumerate(entradas, 2):
        valor_total = entrada.cantidad * entrada.lote.precio_unitario if entrada.lote.precio_unitario else 0
        total_cantidad += entrada.cantidad
        total_valor += valor_total
        
        ws.cell(row=row, column=1).value = entrada.fecha_movimiento.strftime('%d/%m/%Y %H:%M')
        ws.cell(row=row, column=2).value = entrada.lote.producto.clave_cnis if entrada.lote.producto else '-'
        ws.cell(row=row, column=3).value = entrada.lote.producto.descripcion if entrada.lote.producto else '-'
        ws.cell(row=row, column=4).value = entrada.lote.numero_lote
        ws.cell(row=row, column=5).value = entrada.lote.institucion.denominacion if entrada.lote.institucion else '-'
        ws.cell(row=row, column=6).value = entrada.lote.almacen.nombre if entrada.lote.almacen else '-'
        ws.cell(row=row, column=7).value = entrada.cantidad
        ws.cell(row=row, column=8).value = entrada.lote.precio_unitario or 0
        ws.cell(row=row, column=9).value = valor_total
        ws.cell(row=row, column=10).value = entrada.documento_referencia or '-'
        ws.cell(row=row, column=11).value = entrada.motivo or '-'
        ws.cell(row=row, column=12).value = entrada.usuario.username if entrada.usuario else '-'
        ws.cell(row=row, column=13).value = entrada.lote.fecha_caducidad.strftime('%d/%m/%Y') if entrada.lote.fecha_caducidad else '-'
        ws.cell(row=row, column=14).value = entrada.lote.fecha_fabricacion.strftime('%d/%m/%Y') if entrada.lote.fecha_fabricacion else '-'
        
        # Aplicar bordes
        for col in range(1, 15):
            cell = ws.cell(row=row, column=col)
            cell.border = border
            if col in [7, 8, 9]:  # Columnas numéricas
                cell.alignment = Alignment(horizontal='right')
    
    # Fila de totales
    total_row = len(list(entradas)) + 2
    ws.cell(row=total_row, column=1).value = "TOTALES"
    ws.cell(row=total_row, column=1).font = total_font
    ws.cell(row=total_row, column=1).fill = total_fill
    
    ws.cell(row=total_row, column=7).value = total_cantidad
    ws.cell(row=total_row, column=7).font = total_font
    ws.cell(row=total_row, column=7).fill = total_fill
    
    ws.cell(row=total_row, column=9).value = total_valor
    ws.cell(row=total_row, column=9).font = total_font
    ws.cell(row=total_row, column=9).fill = total_fill
    
    # Aplicar bordes a la fila de totales
    for col in range(1, 15):
        ws.cell(row=total_row, column=col).border = border
    
    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 40
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 25
    ws.column_dimensions['F'].width = 20
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 15
    ws.column_dimensions['J'].width = 20
    ws.column_dimensions['K'].width = 25
    ws.column_dimensions['L'].width = 15
    ws.column_dimensions['M'].width = 18
    ws.column_dimensions['N'].width = 18
    
    # Crear respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="reporte_entradas.xlsx"'
    wb.save(response)
    
    return response
