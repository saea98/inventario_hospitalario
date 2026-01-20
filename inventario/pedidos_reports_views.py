"""
Vistas para reportes de errores en carga masiva de pedidos
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F, Value, CharField
from django.db.models.functions import Concat
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from .pedidos_models import LogErrorPedido
from .pedidos_utils import obtener_resumen_errores
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


@login_required
def reporte_errores_pedidos(request):
    """
    Muestra un reporte de los errores en carga masiva de pedidos.
    Permite filtrar por fecha, tipo de error, institución, etc.
    """
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    tipo_error = request.GET.get('tipo_error')
    institucion = request.GET.get('institucion')
    clave_solicitada = request.GET.get('clave_solicitada')
    
    # Base queryset
    errores = LogErrorPedido.objects.select_related(
        'usuario', 'institucion', 'almacen'
    ).all()
    
    # Aplicar filtros
    if fecha_inicio:
        from datetime import datetime
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        errores = errores.filter(fecha_error__gte=fecha_inicio_dt)
    
    if fecha_fin:
        from datetime import datetime
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        fecha_fin_dt = fecha_fin_dt.replace(hour=23, minute=59, second=59)
        errores = errores.filter(fecha_error__lte=fecha_fin_dt)
    
    if tipo_error:
        errores = errores.filter(tipo_error=tipo_error)
    
    if institucion:
        errores = errores.filter(institucion__id=institucion)
    
    if clave_solicitada:
        errores = errores.filter(clave_solicitada__icontains=clave_solicitada)
    
    # Obtener resumen
    resumen = obtener_resumen_errores(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipo_error=tipo_error
    )
    
    # Estadísticas generales
    total_errores = errores.count()
    errores_hoy = errores.filter(
        fecha_error__date=timezone.now().date()
    ).count()
    errores_semana = errores.filter(
        fecha_error__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Errores sin alerta
    errores_sin_alerta = errores.filter(alerta_enviada=False).count()
    
    # Claves más frecuentes con error
    claves_frecuentes = errores.values('clave_solicitada').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Tipos de error más frecuentes
    tipos_frecuentes = errores.values('tipo_error').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Instituciones con más errores
    instituciones_frecuentes = errores.values(
        'institucion__nombre'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Usuarios con más errores
    usuarios_frecuentes = errores.values(
        'usuario__username'
    ).annotate(
        nombre_completo=Concat(
            F('usuario__first_name'), Value(' '), F('usuario__last_name'),
            output_field=CharField()
        ),
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'errores': errores[:100],  # Mostrar últimos 100
        'total_errores': total_errores,
        'errores_hoy': errores_hoy,
        'errores_semana': errores_semana,
        'errores_sin_alerta': errores_sin_alerta,
        'claves_frecuentes': claves_frecuentes,
        'tipos_frecuentes': tipos_frecuentes,
        'instituciones_frecuentes': instituciones_frecuentes,
        'usuarios_frecuentes': usuarios_frecuentes,
        'resumen': resumen,
        'tipo_error_choices': LogErrorPedido.TIPO_ERROR_CHOICES,
        'page_title': 'Reporte de Errores en Carga Masiva de Pedidos'
    }
    
    return render(request, 'inventario/pedidos/reporte_errores_pedidos.html', context)


@login_required
def reporte_claves_sin_existencia(request):
    """
    Muestra un reporte de claves solicitadas sin existencia.
    Útil para que el área médica genere oficios de solicitud.
    """
    # Obtener claves sin existencia
    errores_sin_existencia = LogErrorPedido.objects.filter(
        tipo_error='SIN_EXISTENCIA'
    ).select_related('usuario', 'institucion').order_by('-fecha_error')
    
    # Agrupar por clave
    from .models import Producto
    claves_sin_existencia = {}
    for error in errores_sin_existencia:
        if error.clave_solicitada not in claves_sin_existencia:
            descripcion = 'Producto no encontrado'
            try:
                producto = Producto.objects.get(clave_cnis=error.clave_solicitada)
                descripcion = producto.descripcion
            except Producto.DoesNotExist:
                pass
            
            claves_sin_existencia[error.clave_solicitada] = {
                'clave': error.clave_solicitada,
                'descripcion': descripcion,
                'total_solicitudes': 0,
                'cantidad_total': 0,
                'instituciones': set(),
                'ultimos_errores': []
            }
        
        claves_sin_existencia[error.clave_solicitada]['total_solicitudes'] += 1
        claves_sin_existencia[error.clave_solicitada]['cantidad_total'] += error.cantidad_solicitada or 0
        if error.institucion:
            claves_sin_existencia[error.clave_solicitada]['instituciones'].add(
                error.institucion.nombre
            )
        claves_sin_existencia[error.clave_solicitada]['ultimos_errores'].append(error)
    
    # Convertir instituciones a lista
    for clave_data in claves_sin_existencia.values():
        clave_data['instituciones'] = list(clave_data['instituciones'])
        clave_data['ultimos_errores'] = clave_data['ultimos_errores'][:5]
    
    context = {
        'claves_sin_existencia': sorted(
            claves_sin_existencia.values(),
            key=lambda x: x['total_solicitudes'],
            reverse=True
        ),
        'total_claves': len(claves_sin_existencia),
        'page_title': 'Reporte de Claves sin Existencia'
    }
    
    return render(request, 'inventario/pedidos/reporte_claves_sin_existencia.html', context)


@login_required
def exportar_claves_sin_existencia_excel(request):
    """
    Exporta el reporte de claves sin existencia a Excel
    """
    # Obtener claves sin existencia (mismo código que en la vista)
    errores_sin_existencia = LogErrorPedido.objects.filter(
        tipo_error='SIN_EXISTENCIA'
    ).select_related('usuario', 'institucion').order_by('-fecha_error')
    
    # Agrupar por clave
    from .models import Producto
    claves_sin_existencia = {}
    for error in errores_sin_existencia:
        if error.clave_solicitada not in claves_sin_existencia:
            descripcion = 'Producto no encontrado'
            try:
                producto = Producto.objects.get(clave_cnis=error.clave_solicitada)
                descripcion = producto.descripcion
            except Producto.DoesNotExist:
                pass
            
            claves_sin_existencia[error.clave_solicitada] = {
                'clave': error.clave_solicitada,
                'descripcion': descripcion,
                'total_solicitudes': 0,
                'cantidad_total': 0,
                'instituciones': set(),
            }
        
        claves_sin_existencia[error.clave_solicitada]['total_solicitudes'] += 1
        claves_sin_existencia[error.clave_solicitada]['cantidad_total'] += error.cantidad_solicitada or 0
        if error.institucion:
            claves_sin_existencia[error.clave_solicitada]['instituciones'].add(
                error.institucion.nombre
            )
    
    # Convertir instituciones a lista
    for clave_data in claves_sin_existencia.values():
        clave_data['instituciones'] = ', '.join(list(clave_data['instituciones']))
    
    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Claves Sin Existencia'
    
    # Estilos
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Encabezados
    headers = ['Clave', 'Descripción', 'Cantidad Total Solicitada', 'Total Solicitudes', 'Instituciones']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border
    
    # Datos
    for row, clave_data in enumerate(sorted(
        claves_sin_existencia.values(),
        key=lambda x: x['total_solicitudes'],
        reverse=True
    ), 2):
        ws.cell(row=row, column=1).value = clave_data['clave']
        ws.cell(row=row, column=2).value = clave_data['descripcion']
        ws.cell(row=row, column=3).value = clave_data['cantidad_total']
        ws.cell(row=row, column=4).value = clave_data['total_solicitudes']
        ws.cell(row=row, column=5).value = clave_data['instituciones']
        
        for col in range(1, 6):
            cell = ws.cell(row=row, column=col)
            cell.border = border
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    
    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 18
    ws.column_dimensions['E'].width = 30
    
    # Generar respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="claves_sin_existencia.xlsx"'
    wb.save(response)
    
    return response


@login_required
def reporte_claves_no_existen(request):
    """
    Muestra un reporte de claves que no existen en el catálogo.
    Útil para que el área médica genere oficios de solicitud de nuevos productos.
    """
    # Obtener claves que no existen
    errores_no_existen = LogErrorPedido.objects.filter(
        tipo_error='CLAVE_NO_EXISTE'
    ).select_related('usuario', 'institucion').order_by('-fecha_error')
    
    # Agrupar por clave
    claves_no_existen = {}
    for error in errores_no_existen:
        if error.clave_solicitada not in claves_no_existen:
            claves_no_existen[error.clave_solicitada] = {
                'clave': error.clave_solicitada,
                'total_solicitudes': 0,
                'cantidad_total': 0,
                'instituciones': set(),
                'ultimos_errores': []
            }
        
        claves_no_existen[error.clave_solicitada]['total_solicitudes'] += 1
        claves_no_existen[error.clave_solicitada]['cantidad_total'] += error.cantidad_solicitada or 0
        if error.institucion:
            claves_no_existen[error.clave_solicitada]['instituciones'].add(
                error.institucion.nombre
            )
        claves_no_existen[error.clave_solicitada]['ultimos_errores'].append(error)
    
    # Convertir instituciones a lista
    for clave_data in claves_no_existen.values():
        clave_data['instituciones'] = list(clave_data['instituciones'])
        clave_data['ultimos_errores'] = clave_data['ultimos_errores'][:5]
    
    context = {
        'claves_no_existen': sorted(
            claves_no_existen.values(),
            key=lambda x: x['total_solicitudes'],
            reverse=True
        ),
        'total_claves': len(claves_no_existen),
        'page_title': 'Reporte de Claves que no Existen en Catálogo'
    }
    
    return render(request, 'inventario/pedidos/reporte_claves_no_existen.html', context)
