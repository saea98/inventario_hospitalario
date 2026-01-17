"""
Módulo para convertir archivos Excel a PDF
Usa openpyxl para leer el Excel y reportlab para generar el PDF
Sin dependencias externas como LibreOffice o weasyprint
"""

from openpyxl import load_workbook
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageTemplate, Frame
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime


def convertir_excel_a_pdf(excel_buffer):
    """
    Convierte un buffer de Excel a PDF usando openpyxl y reportlab.
    
    Args:
        excel_buffer: BytesIO con contenido del archivo Excel
        
    Returns:
        BytesIO: Buffer con contenido del PDF
        
    Raises:
        Exception: Si falla la conversión
    """
    
    try:
        # Leer el Excel
        excel_buffer.seek(0)
        workbook = load_workbook(excel_buffer)
        worksheet = workbook.active
        
        # Extraer datos del Excel
        titulo = _obtener_valor_celda(worksheet['A1'])
        propuesta_folio = _obtener_valor_celda(worksheet['B3'])
        institucion = _obtener_valor_celda(worksheet['D3'])
        fecha = _obtener_valor_celda(worksheet['B4'])
        folio_pedido = _obtener_valor_celda(worksheet['D4'])
        area = _obtener_valor_celda(worksheet['B5'])
        total_items = _obtener_valor_celda(worksheet['D5'])
        
        # Extraer datos de la tabla (a partir de fila 9)
        datos_tabla = []
        for row_idx in range(9, worksheet.max_row + 1):
            fila = []
            for col_idx in range(1, 8):
                celda = worksheet.cell(row=row_idx, column=col_idx)
                valor = _obtener_valor_celda(celda)
                fila.append(valor if valor else "")
            
            # Si la fila tiene contenido, agregarla
            if any(fila):
                datos_tabla.append(fila)
        
        # Crear PDF
        pdf_buffer = BytesIO()
        
        # Crear documento con tamaño A4 landscape
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(A4),
            rightMargin=8*mm,
            leftMargin=8*mm,
            topMargin=8*mm,
            bottomMargin=8*mm
        )
        
        # Contenido del documento
        story = []
        
        # Título
        titulo_style = ParagraphStyle(
            'CustomTitle',
            fontSize=14,
            textColor=colors.HexColor('#8B1538'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(titulo, titulo_style))
        story.append(Spacer(1, 5*mm))
        
        # Información de la propuesta
        info_data = [
            ['Propuesta:', str(propuesta_folio), 'Institución Solicitante:', str(institucion)],
            ['Fecha:', str(fecha), 'Folio de Pedido:', str(folio_pedido)],
            ['Área:', str(area), 'Total Items:', str(total_items)],
        ]
        
        info_table = Table(info_data, colWidths=[25*mm, 35*mm, 40*mm, 80*mm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 5*mm))
        
        # Tabla de items
        encabezados = ['UBICACIÓN', 'CLAVE CNIS', 'PRODUCTO', 'CADUCIDAD', 'LOTE', 'CANTIDAD', 'CANTIDAD SURTIDA']
        datos_completos = [encabezados] + datos_tabla
        
        items_table = Table(
            datos_completos,
            colWidths=[15*mm, 20*mm, 100*mm, 18*mm, 18*mm, 18*mm, 25*mm]
        )
        
        items_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            
            # Datos
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),
            ('ALIGN', (6, 1), (6, -1), 'CENTER'),
            
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (5, 1), (5, -1), 'Helvetica-Bold'),
            
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            
            ('BACKGROUND', (5, 1), (5, -1), colors.HexColor('#e8f4f8')),
            
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(items_table)
        
        # Construir el PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        return pdf_buffer
        
    except Exception as e:
        raise Exception(f"Error al convertir Excel a PDF: {str(e)}")


def _obtener_valor_celda(celda):
    """Obtiene el valor de una celda."""
    
    if celda is None:
        return ""
    
    value = celda.value if hasattr(celda, 'value') else celda
    
    if value is None:
        return ""
    
    # Formatear fechas
    if hasattr(value, 'strftime'):
        return value.strftime('%d/%m/%Y %H:%M')
    
    return str(value)
