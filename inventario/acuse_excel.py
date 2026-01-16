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
    con formato similar al ejemplo proporcionado
    
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
    ws.column_dimensions['F'].width = 13
    ws.column_dimensions['G'].width = 13
    ws.column_dimensions['H'].width = 14
    ws.column_dimensions['I'].width = 12
    ws.column_dimensions['J'].width = 12.85546875
    ws.column_dimensions['K'].width = 19
    
    # ============ ENCABEZADO ============
    
    # Fila 1: Título en columna D
    ws['D1'].value = 'Sistema de Abasto, Inventarios y Control de Almacenes'
    ws['D1'].font = Font(name='Calibri', size=12, bold=True, color='8B1538')
    ws['D1'].alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[1].height = 20
    
    # Intentar agregar logo en A1
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'templates', 'inventario', 'images', 'logo_imss.jpg')
        if os.path.exists(logo_path):
            img = XLImage(logo_path)
            img.width = 60
            img.height = 20
            ws.add_image(img, 'A1')
    except Exception as e:
        print(f"No se pudo agregar el logo: {e}")
    
    # Fila 2-5: Información de folio (alineada a la derecha en columnas I-K)
    folio = propuesta.solicitud.folio
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    folio_pedido = propuesta.solicitud.observaciones_solicitud or 'N/A'
    institucion = propuesta.solicitud.institucion_solicitante.denominacion if propuesta.solicitud.institucion_solicitante else 'N/A'
    
    # Fila 1: #FOLIO
    ws['I1'].value = f'#FOLIO: {folio}'
    ws['I1'].font = Font(name='Calibri', size=8, bold=True)
    ws['I1'].alignment = Alignment(horizontal='right', vertical='center')
    
    # Fila 2: TRANSFERENCIA
    ws['I2'].value = 'TRANSFERENCIA: prueba'
    ws['I2'].font = Font(name='Calibri', size=8)
    ws['I2'].alignment = Alignment(horizontal='right', vertical='center')
    
    # Fila 3: FOLIO DE PEDIDO
    ws['I3'].value = f'FOLIO DE PEDIDO: {folio_pedido}'
    ws['I3'].font = Font(name='Calibri', size=8)
    ws['I3'].alignment = Alignment(horizontal='right', vertical='center')
    
    # Fila 4: FECHA
    ws['I4'].value = f'FECHA: {fecha_actual}'
    ws['I4'].font = Font(name='Calibri', size=8)
    ws['I4'].alignment = Alignment(horizontal='right', vertical='center')
    
    # Fila 5: TIPO
    ws['I5'].value = 'TIPO: TRANSFERENCIA (SURTIMIENTO)'
    ws['I5'].font = Font(name='Calibri', size=8)
    ws['I5'].alignment = Alignment(horizontal='right', vertical='center')
    
    # Fila 6: Espaciador
    ws.row_dimensions[6].height = 5
    
    # Fila 7: Título "ACUSE DE ENTREGA"
    ws['A7'].value = 'ACUSE DE ENTREGA'
    ws['A7'].font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    ws['A7'].fill = PatternFill(start_color='8B1538', end_color='8B1538', fill_type='solid')
    ws['A7'].alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[7].height = 18
    
    # Fila 8: Espaciador
    ws.row_dimensions[8].height = 5
    
    # Fila 9: Encabezados de firmas
    firma_headers = {
        'A9': 'UNIDAD DE DESTINO',
        'D9': 'RECIBE\n(UNIDAD DE DESTINO)',
        'G9': 'AUTORIZA\n(ALMACEN)',
        'J9': 'ENTREGA\n(ALMACEN)'
    }
    
    for cell_ref, header_text in firma_headers.items():
        cell = ws[cell_ref]
        cell.value = header_text
        cell.font = Font(name='Calibri', size=9, bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='8B1538', end_color='8B1538', fill_type='solid')
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    ws.row_dimensions[9].height = 25
    
    # Fila 10: Datos de firmas - Institución y nombres
    ws['A10'].value = f'INSTITUCIÓN: {institucion}'
    ws['A10'].font = Font(name='Calibri', size=8)
    ws['A10'].alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    ws['A10'].border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    ws['D10'].value = 'NOMBRE:'
    ws['D10'].font = Font(name='Calibri', size=8)
    ws['D10'].alignment = Alignment(horizontal='center', vertical='top')
    ws['D10'].border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    ws['G10'].value = 'NOMBRE:'
    ws['G10'].font = Font(name='Calibri', size=8)
    ws['G10'].alignment = Alignment(horizontal='center', vertical='top')
    ws['G10'].border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    ws['J10'].value = 'NOMBRE:'
    ws['J10'].font = Font(name='Calibri', size=8)
    ws['J10'].alignment = Alignment(horizontal='center', vertical='top')
    ws['J10'].border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    ws.row_dimensions[10].height = 20
    
    # Fila 11: PUESTO
    for col in ['D', 'G', 'J']:
        cell = ws[f'{col}11']
        cell.value = 'PUESTO:'
        cell.font = Font(name='Calibri', size=8)
        cell.alignment = Alignment(horizontal='center', vertical='top')
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    ws.row_dimensions[11].height = 20
    
    # Fila 12: Espaciador
    ws.row_dimensions[12].height = 5
    
    # Fila 13: FIRMA
    for col in ['D', 'G', 'J']:
        cell = ws[f'{col}13']
        cell.value = 'FIRMA:'
        cell.font = Font(name='Calibri', size=8)
        cell.alignment = Alignment(horizontal='center', vertical='top')
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    ws.row_dimensions[13].height = 30
    
    # Fila 14-16: Espaciador
    ws.row_dimensions[14].height = 5
    ws.row_dimensions[15].height = 5
    ws.row_dimensions[16].height = 5
    
    # Fila 17: Encabezados de tabla de items
    headers = ['#', 'CLAVE CNIS', 'DESCRIPCIÓN', 'U.M.', 'TIPO', 'LOTE', 'CADUCIDAD', 'CLASIFICACIÓN', 'UBICACIÓN', 'CANTIDAD', 'FOLIO PEDIDO']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=17, column=col_num)
        cell.value = header
        cell.font = Font(name='Calibri', size=8, bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='8B1538', end_color='8B1538', fill_type='solid')
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    ws.row_dimensions[17].height = 25
    
    # Agregar items (comenzando en fila 18)
    row_num = 18
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
