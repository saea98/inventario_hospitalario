"""
Módulo para generar Acuse de Entrega en Excel
Incluye logo y formato similar al PDF
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from datetime import datetime
import os
from django.conf import settings
from io import BytesIO


def generar_acuse_excel(propuesta):
    """
    Genera un archivo Excel con el acuse de entrega de una propuesta
    
    Args:
        propuesta: Objeto PropuestaPedido
        
    Returns:
        BytesIO: Buffer con el archivo Excel
    """
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Acuse de Entrega"
    
    # Configurar ancho de columnas
    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 25
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 14
    ws.column_dimensions['I'].width = 12
    ws.column_dimensions['J'].width = 12
    ws.column_dimensions['K'].width = 15
    
    # ============ ENCABEZADO ============
    
    # Fila 1: Logo y título
    ws.merge_cells('A1:K1')
    ws['A1'].value = 'Sistema de Abasto, Inventarios y Control de Almacenes'
    ws['A1'].font = Font(name='Calibri', size=12, bold=True, color='8B1538')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 25
    
    # Intentar agregar logo
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'templates', 'inventario', 'images', 'logo_imss.jpg')
        if os.path.exists(logo_path):
            img = XLImage(logo_path)
            img.width = 80
            img.height = 25
            ws.add_image(img, 'A1')
    except Exception as e:
        print(f"No se pudo agregar el logo: {e}")
    
    # Fila 2: Espaciador
    ws.row_dimensions[2].height = 5
    
    # Fila 3: Información de folio
    ws.merge_cells('A3:K3')
    folio = propuesta.solicitud.folio
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    folio_pedido = propuesta.solicitud.observaciones_solicitud or 'N/A'
    institucion = propuesta.solicitud.institucion_solicitante.denominacion if propuesta.solicitud.institucion_solicitante else 'N/A'
    
    info_text = f'FOLIO: {folio} | FECHA: {fecha_actual} | FOLIO DE PEDIDO: {folio_pedido} | INSTITUCIÓN: {institucion}'
    ws['A3'].value = info_text
    ws['A3'].font = Font(name='Calibri', size=9, bold=True)
    ws['A3'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    # Fila 4: Espaciador
    ws.row_dimensions[4].height = 5
    
    # Fila 5: Título "ACUSE DE ENTREGA"
    ws.merge_cells('A5:K5')
    ws['A5'].value = 'ACUSE DE ENTREGA'
    ws['A5'].font = Font(name='Calibri', size=12, bold=True, color='FFFFFF')
    ws['A5'].fill = PatternFill(start_color='8B1538', end_color='8B1538', fill_type='solid')
    ws['A5'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[5].height = 20
    
    # ============ TABLA DE FIRMAS ============
    
    # Fila 6: Espaciador
    ws.row_dimensions[6].height = 5
    
    # Fila 7: Encabezados de firmas
    firma_headers = ['UNIDAD DE DESTINO', 'RECIBE\n(UNIDAD DE DESTINO)', 'AUTORIZA\n(ALMACEN)', 'ENTREGA\n(ALMACEN)']
    ws['A7'].value = firma_headers[0]
    ws['C7'].value = firma_headers[1]
    ws['E7'].value = firma_headers[2]
    ws['G7'].value = firma_headers[3]
    
    # Aplicar estilo a encabezados de firmas
    for col in ['A', 'C', 'E', 'G']:
        ws[f'{col}7'].font = Font(name='Calibri', size=10, bold=True, color='FFFFFF')
        ws[f'{col}7'].fill = PatternFill(start_color='8B1538', end_color='8B1538', fill_type='solid')
        ws[f'{col}7'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    ws.row_dimensions[7].height = 25
    
    # Fila 8-11: Datos de firmas
    almacen_destino = propuesta.solicitud.almacen_destino.nombre if propuesta.solicitud.almacen_destino else 'N/A'
    
    ws['A8'].value = almacen_destino
    ws['C8'].value = 'NOMBRE: __________________'
    ws['E8'].value = 'NOMBRE: Gerardo Anaya'
    ws['G8'].value = 'NOMBRE: __________________'
    
    ws['C9'].value = 'PUESTO: __________________'
    ws['E9'].value = 'PUESTO: MESA DE CONTROL'
    ws['G9'].value = 'PUESTO: __________________'
    
    ws['C10'].value = 'FIRMA: __________________'
    ws['E10'].value = 'FIRMA: __________________'
    ws['G10'].value = 'FIRMA: __________________'
    
    # Aplicar estilos a datos de firmas
    for row in range(8, 11):
        for col in ['A', 'C', 'E', 'G']:
            cell = ws[f'{col}{row}']
            cell.font = Font(name='Calibri', size=9)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
    
    ws.row_dimensions[8].height = 15
    ws.row_dimensions[9].height = 15
    ws.row_dimensions[10].height = 15
    
    # Fila 12: Espaciador
    ws.row_dimensions[12].height = 10
    
    # ============ TABLA DE ITEMS ============
    
    # Fila 13: Encabezados de tabla
    headers = ['#', 'CLAVE CNIS', 'DESCRIPCIÓN', 'U.M.', 'TIPO', 'LOTE', 'CADUCIDAD', 'CLASIFICACIÓN', 'UBICACIÓN', 'CANTIDAD', 'FOLIO PEDIDO']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=13, column=col_num)
        cell.value = header
        cell.font = Font(name='Calibri', size=9, bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='8B1538', end_color='8B1538', fill_type='solid')
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    ws.row_dimensions[13].height = 25
    
    # Agregar items
    row_num = 14
    idx = 1
    
    for item in propuesta.items.all():
        lotes_asignados = item.lotes_asignados.all()
        
        for lote_asignado in lotes_asignados:
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            ubicacion = lote_ubicacion.ubicacion.codigo if lote_ubicacion.ubicacion else 'N/A'
            caducidad = lote.fecha_caducidad.strftime("%d/%m/%Y") if lote.fecha_caducidad else 'N/A'
            lote_info = lote.numero_lote if lote.numero_lote else 'N/A'
            descripcion = item.producto.descripcion[:30]  # Limitar descripción
            cantidad = item.cantidad_propuesta if item.cantidad_propuesta > 0 else item.cantidad_surtida
            
            # Agregar fila
            ws.cell(row=row_num, column=1).value = idx
            ws.cell(row=row_num, column=2).value = item.producto.clave_cnis
            ws.cell(row=row_num, column=3).value = descripcion
            ws.cell(row=row_num, column=4).value = item.producto.unidad_medida
            ws.cell(row=row_num, column=5).value = 'ORDINARIO'
            ws.cell(row=row_num, column=6).value = lote_info
            ws.cell(row=row_num, column=7).value = caducidad
            ws.cell(row=row_num, column=8).value = 'MEDICAMENTO'
            ws.cell(row=row_num, column=9).value = ubicacion
            ws.cell(row=row_num, column=10).value = cantidad
            ws.cell(row=row_num, column=11).value = ''
            
            # Aplicar estilos
            for col in range(1, 12):
                cell = ws.cell(row=row_num, column=col)
                cell.font = Font(name='Calibri', size=8)
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
            
            ws.row_dimensions[row_num].height = 20
            row_num += 1
            idx += 1
    
    # Guardar en buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer
