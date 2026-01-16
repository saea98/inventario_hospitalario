"""
Módulo para generar Acuse de Entrega en Excel usando template
"""

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from datetime import datetime
import os
from django.conf import settings
from io import BytesIO
import shutil


def generar_acuse_excel(propuesta):
    """
    Genera un archivo Excel con el acuse de entrega usando un template como base
    
    Args:
        propuesta: Objeto PropuestaPedido
        
    Returns:
        BytesIO: Buffer con el archivo Excel
    """
    
    # Cargar el template
    template_path = os.path.join(settings.BASE_DIR, 'inventario', 'templates', 'acuse_entrega_template.xlsx')
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template no encontrado en: {template_path}")
    
    # Cargar el workbook desde el template
    wb = load_workbook(template_path)
    ws = wb.active
    
    # Obtener datos de la propuesta
    folio = propuesta.solicitud.folio
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    folio_pedido = propuesta.solicitud.observaciones_solicitud or 'N/A'
    institucion = propuesta.solicitud.institucion_solicitante.denominacion if propuesta.solicitud.institucion_solicitante else 'N/A'
    
    # ============ ACTUALIZAR ENCABEZADO ============
    
    # Fila 1: #FOLIO
    ws['I1'].value = f'#FOLIO: {folio}'
    
    # Fila 3: FOLIO DE PEDIDO
    ws['I3'].value = f'FOLIO DE PEDIDO: {folio_pedido}'
    
    # Fila 4: FECHA
    ws['I4'].value = f'FECHA: {fecha_actual}'
    
    # ============ ACTUALIZAR TABLA DE FIRMAS ============
    
    # Fila 10: Institución
    ws['A10'].value = f'INSTITUCIÓN: {institucion}'
    
    # ============ ACTUALIZAR TABLA DE ITEMS ============
    
    # Comenzar en fila 18 (después de los encabezados en fila 17)
    row_num = 18
    idx = 1
    
    # Limpiar filas existentes primero (si las hay)
    # Buscar cuántas filas tienen datos en el template
    max_row_in_template = 18
    for row in range(18, ws.max_row + 1):
        if ws.cell(row=row, column=1).value is not None:
            max_row_in_template = row
    
    # Eliminar filas de datos del template (mantener encabezados)
    if max_row_in_template > 18:
        ws.delete_rows(18, max_row_in_template - 17)
    
    # Agregar items
    for item in propuesta.items.all():
        lotes_asignados = item.lotes_asignados.all()
        
        for lote_asignado in lotes_asignados:
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            ubicacion = lote_ubicacion.ubicacion.codigo if lote_ubicacion.ubicacion else 'N/A'
            caducidad = lote.fecha_caducidad.strftime("%d/%m/%Y") if lote.fecha_caducidad else 'N/A'
            lote_info = lote.numero_lote if lote.numero_lote else 'N/A'
            descripcion = item.producto.descripcion
            cantidad = item.cantidad_propuesta if item.cantidad_propuesta > 0 else item.cantidad_surtida
            
            # Agregar fila con datos
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
            
            # Copiar estilos de la fila anterior (fila 18 del template)
            if row_num == 18:
                # Primera fila de datos, copiar estilos de la fila 18 del template
                for col in range(1, 12):
                    source_cell = ws.cell(row=18, column=col)
                    target_cell = ws.cell(row=row_num, column=col)
                    
                    # Copiar estilos
                    if source_cell.has_style:
                        target_cell.font = source_cell.font.copy()
                        target_cell.border = source_cell.border.copy()
                        target_cell.fill = source_cell.fill.copy()
                        target_cell.number_format = source_cell.number_format
                        target_cell.protection = source_cell.protection
                        target_cell.alignment = source_cell.alignment.copy()
            else:
                # Copiar estilos de la fila anterior
                for col in range(1, 12):
                    source_cell = ws.cell(row=row_num - 1, column=col)
                    target_cell = ws.cell(row=row_num, column=col)
                    
                    if source_cell.has_style:
                        target_cell.font = source_cell.font.copy()
                        target_cell.border = source_cell.border.copy()
                        target_cell.fill = source_cell.fill.copy()
                        target_cell.number_format = source_cell.number_format
                        target_cell.protection = source_cell.protection
                        target_cell.alignment = source_cell.alignment.copy()
            
            row_num += 1
            idx += 1
    
    # Guardar en buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer
