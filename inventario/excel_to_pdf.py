"""
Módulo para convertir archivos Excel a PDF
"""

import subprocess
import os
import tempfile
from io import BytesIO


def convertir_excel_a_pdf(excel_buffer):
    """
    Convierte un buffer de Excel a PDF usando LibreOffice.
    
    Args:
        excel_buffer: BytesIO con el contenido del Excel
    
    Returns:
        BytesIO: Buffer con el contenido del PDF
    
    Raises:
        Exception: Si LibreOffice no está disponible o la conversión falla
    """
    
    try:
        # Crear archivos temporales
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as excel_file:
            excel_file.write(excel_buffer.getvalue())
            excel_path = excel_file.name
        
        # Crear directorio temporal para el PDF
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Usar LibreOffice para convertir a PDF
            # --headless: sin interfaz gráfica
            # --convert-to pdf: convertir a PDF
            # --outdir: directorio de salida
            subprocess.run(
                [
                    'libreoffice',
                    '--headless',
                    '--convert-to', 'pdf',
                    '--outdir', temp_dir,
                    excel_path
                ],
                check=True,
                capture_output=True,
                timeout=30
            )
            
            # Obtener el nombre del archivo PDF generado
            pdf_filename = os.path.splitext(os.path.basename(excel_path))[0] + '.pdf'
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            # Leer el PDF generado
            with open(pdf_path, 'rb') as pdf_file:
                pdf_buffer = BytesIO(pdf_file.read())
            
            # Limpiar archivos temporales
            os.remove(excel_path)
            os.remove(pdf_path)
            os.rmdir(temp_dir)
            
            return pdf_buffer
            
        except subprocess.TimeoutExpired:
            raise Exception("La conversión a PDF tardó demasiado tiempo")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error en LibreOffice: {e.stderr.decode()}")
        except Exception as e:
            raise Exception(f"Error durante la conversión: {str(e)}")
        finally:
            # Limpiar en caso de error
            if os.path.exists(excel_path):
                os.remove(excel_path)
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
    
    except Exception as e:
        raise Exception(f"Error al convertir Excel a PDF: {str(e)}")
