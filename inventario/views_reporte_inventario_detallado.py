"""
Vista para reporte detallado de inventario con las columnas:
ENTIDAD, CLUES, ORDEN DE SUMINISTRO, RFC, CLAVE, ESTADO DEL INSUMO,
INVENTARIO DISPONIBLE, LOTE, F_CAD, F_FAB, F_REC
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import date, datetime

from .models import Lote, Producto, Institucion, OrdenSuministro, Proveedor
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


@login_required
def reporte_inventario_detallado(request):
    """
    Reporte detallado de inventario con información de lotes, instituciones y órdenes de suministro.
    """
    
    # Obtener parámetros de filtro
    filtro_entidad = request.GET.get('entidad', '').strip()
    filtro_clues = request.GET.get('clues', '').strip()
    filtro_orden = request.GET.get('orden', '').strip()
    filtro_rfc = request.GET.get('rfc', '').strip()
    filtro_clave = request.GET.get('clave', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()
    filtro_lote = request.GET.get('lote', '').strip()
    
    # Query base con todas las relaciones necesarias
    lotes = Lote.objects.select_related(
        'producto',
        'institucion',
        'orden_suministro__proveedor'
    ).all()
    
    # Aplicar filtros
    if filtro_entidad:
        lotes = lotes.filter(institucion__denominacion__icontains=filtro_entidad)
    
    if filtro_clues:
        lotes = lotes.filter(institucion__clue__icontains=filtro_clues)
    
    if filtro_orden:
        lotes = lotes.filter(orden_suministro__numero_orden__icontains=filtro_orden)
    
    if filtro_rfc:
        lotes = lotes.filter(orden_suministro__proveedor__rfc__icontains=filtro_rfc)
    
    if filtro_clave:
        lotes = lotes.filter(producto__clave_cnis__icontains=filtro_clave)
    
    if filtro_estado:
        lotes = lotes.filter(estado=filtro_estado)
    
    if filtro_lote:
        lotes = lotes.filter(numero_lote__icontains=filtro_lote)
    
    # Ordenar por institución y fecha de recepción
    lotes = lotes.order_by('institucion__denominacion', '-fecha_recepcion', 'producto__clave_cnis')
    
    # Paginación
    paginator = Paginator(lotes, 50)  # 50 items por página
    page = request.GET.get('page', 1)
    
    try:
        lotes_paginados = paginator.page(page)
    except PageNotAnInteger:
        lotes_paginados = paginator.page(1)
    except EmptyPage:
        lotes_paginados = paginator.page(paginator.num_pages)
    
    # Preparar datos para el template
    datos_reporte = []
    for lote in lotes_paginados:
        # Obtener estado del insumo como texto
        estado_texto = lote.get_estado_display() if hasattr(lote, 'get_estado_display') else ''
        if lote.estado == 1:
            estado_texto = 'Disponible'
        elif lote.estado == 4:
            estado_texto = 'Suspendido'
        elif lote.estado == 5:
            estado_texto = 'Deteriorado'
        elif lote.estado == 6:
            estado_texto = 'Caducado'
        
        datos_reporte.append({
            'entidad': lote.institucion.denominacion if lote.institucion else '',
            'clues': lote.institucion.clue if lote.institucion else '',
            'orden_suministro': lote.orden_suministro.numero_orden if lote.orden_suministro else '',
            'rfc': lote.orden_suministro.proveedor.rfc if lote.orden_suministro and lote.orden_suministro.proveedor else '',
            'clave': lote.producto.clave_cnis if lote.producto else '',
            'estado_insumo': estado_texto,
            'inventario_disponible': lote.cantidad_disponible,
            'lote': lote.numero_lote,
            'f_cad': lote.fecha_caducidad.strftime('%d/%m/%Y') if lote.fecha_caducidad else '',
            'f_fab': lote.fecha_fabricacion.strftime('%d/%m/%Y') if lote.fecha_fabricacion else '',
            'f_rec': lote.fecha_recepcion.strftime('%d/%m/%Y') if lote.fecha_recepcion else '',
        })
    
    # Obtener listas para filtros
    instituciones = Institucion.objects.filter(activo=True).order_by('denominacion')[:100]
    
    context = {
        'datos_reporte': datos_reporte,
        'lotes_paginados': lotes_paginados,
        'filtro_entidad': filtro_entidad,
        'filtro_clues': filtro_clues,
        'filtro_orden': filtro_orden,
        'filtro_rfc': filtro_rfc,
        'filtro_clave': filtro_clave,
        'filtro_estado': filtro_estado,
        'filtro_lote': filtro_lote,
        'estados_lote': [
            (1, 'Disponible'),
            (4, 'Suspendido'),
            (5, 'Deteriorado'),
            (6, 'Caducado'),
        ],
    }
    
    return render(request, 'inventario/reportes/reporte_inventario_detallado.html', context)


@login_required
def exportar_inventario_detallado_excel(request):
    """
    Exporta el reporte de inventario detallado a Excel.
    """
    
    # Obtener los mismos filtros que en la vista
    filtro_entidad = request.GET.get('entidad', '').strip()
    filtro_clues = request.GET.get('clues', '').strip()
    filtro_orden = request.GET.get('orden', '').strip()
    filtro_rfc = request.GET.get('rfc', '').strip()
    filtro_clave = request.GET.get('clave', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()
    filtro_lote = request.GET.get('lote', '').strip()
    
    # Query base con todas las relaciones necesarias
    lotes = Lote.objects.select_related(
        'producto',
        'institucion',
        'orden_suministro__proveedor'
    ).all()
    
    # Aplicar filtros (mismos que en la vista)
    if filtro_entidad:
        lotes = lotes.filter(institucion__denominacion__icontains=filtro_entidad)
    
    if filtro_clues:
        lotes = lotes.filter(institucion__clue__icontains=filtro_clues)
    
    if filtro_orden:
        lotes = lotes.filter(orden_suministro__numero_orden__icontains=filtro_orden)
    
    if filtro_rfc:
        lotes = lotes.filter(orden_suministro__proveedor__rfc__icontains=filtro_rfc)
    
    if filtro_clave:
        lotes = lotes.filter(producto__clave_cnis__icontains=filtro_clave)
    
    if filtro_estado:
        lotes = lotes.filter(estado=filtro_estado)
    
    if filtro_lote:
        lotes = lotes.filter(numero_lote__icontains=filtro_lote)
    
    # Ordenar por institución y fecha de recepción
    lotes = lotes.order_by('institucion__denominacion', '-fecha_recepcion', 'producto__clave_cnis')
    
    # Crear workbook Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario Detallado"
    
    # Estilos
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Encabezados
    headers = [
        'ENTIDAD',
        'CLUES',
        'ORDEN DE SUMINISTRO',
        'RFC',
        'CLAVE',
        'ESTADO DEL INSUMO',
        'INVENTARIO DISPONIBLE',
        'LOTE',
        'F_CAD',
        'F_FAB',
        'F_REC'
    ]
    
    # Escribir encabezados
    for col_num, header in enumerate(headers, 1):
        col_letter = get_column_letter(col_num)
        cell = ws[f"{col_letter}1"]
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # Escribir datos
    for row_num, lote in enumerate(lotes, 2):
        # Obtener estado del insumo como texto
        estado_texto = ''
        if lote.estado == 1:
            estado_texto = 'Disponible'
        elif lote.estado == 4:
            estado_texto = 'Suspendido'
        elif lote.estado == 5:
            estado_texto = 'Deteriorado'
        elif lote.estado == 6:
            estado_texto = 'Caducado'
        
        row_data = [
            lote.institucion.denominacion if lote.institucion else '',
            lote.institucion.clue if lote.institucion else '',
            lote.orden_suministro.numero_orden if lote.orden_suministro else '',
            lote.orden_suministro.proveedor.rfc if lote.orden_suministro and lote.orden_suministro.proveedor else '',
            lote.producto.clave_cnis if lote.producto else '',
            estado_texto,
            lote.cantidad_disponible,
            lote.numero_lote,
            lote.fecha_caducidad.strftime('%d/%m/%Y') if lote.fecha_caducidad else '',
            lote.fecha_fabricacion.strftime('%d/%m/%Y') if lote.fecha_fabricacion else '',
            lote.fecha_recepcion.strftime('%d/%m/%Y') if lote.fecha_recepcion else '',
        ]
        
        for col_num, value in enumerate(row_data, 1):
            col_letter = get_column_letter(col_num)
            cell = ws[f"{col_letter}{row_num}"]
            cell.value = value
            cell.border = border
            if col_num == 7:  # INVENTARIO DISPONIBLE - alinear a la derecha
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
    
    # Ajustar ancho de columnas
    column_widths = {
        'A': 40,  # ENTIDAD
        'B': 15,  # CLUES
        'C': 25,  # ORDEN DE SUMINISTRO
        'D': 15,  # RFC
        'E': 20,  # CLAVE
        'F': 20,  # ESTADO DEL INSUMO
        'G': 20,  # INVENTARIO DISPONIBLE
        'H': 20,  # LOTE
        'I': 12,  # F_CAD
        'J': 12,  # F_FAB
        'K': 12,  # F_REC
    }
    
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width
    
    # Crear respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="reporte_inventario_detallado_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    wb.save(response)
    return response
