from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date, timedelta
import os

from .models import CargaInventario, Institucion, CategoriaProducto
from .forms import CargaInventarioForm, FiltroInventarioForm
from .utils import ExcelProcessor
from .reports import ReportGenerator


@login_required
def cargar_archivo_excel(request):
    """Vista para cargar archivos Excel de inventario"""
    if request.method == 'POST':
        form = CargaInventarioForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardar el archivo
            carga = form.save(commit=False)
            carga.usuario = request.user
            carga.nombre_archivo = request.FILES['archivo'].name
            carga.save()
            
            # Procesar el archivo
            try:
                carga.estado = 'PROCESANDO'
                carga.save()
                
                processor = ExcelProcessor()
                archivo_path = carga.archivo.path
                
                # Determinar tipo de archivo por nombre
                if 'clues' in carga.nombre_archivo.lower():
                    exito = processor.procesar_archivo_clues(archivo_path)
                else:
                    exito = processor.procesar_archivo_inventario(archivo_path, request.user)
                
                # Actualizar estado de la carga
                resumen = processor.obtener_resumen()
                carga.total_registros = resumen['total_registros']
                carga.registros_procesados = resumen['total_registros']
                carga.registros_exitosos = resumen['registros_exitosos']
                carga.registros_con_error = resumen['registros_con_error']
                carga.log_errores = '\n'.join(resumen['errores'])
                carga.fecha_procesamiento = timezone.now()
                
                if exito and resumen['registros_con_error'] == 0:
                    carga.estado = 'COMPLETADA'
                    messages.success(
                        request, 
                        f'Archivo procesado exitosamente. {resumen["registros_exitosos"]} registros cargados.'
                    )
                else:
                    carga.estado = 'ERROR'
                    messages.warning(
                        request,
                        f'Archivo procesado con errores. {resumen["registros_exitosos"]} exitosos, '
                        f'{resumen["registros_con_error"]} con errores.'
                    )
                
                carga.save()
                
            except Exception as e:
                carga.estado = 'ERROR'
                carga.log_errores = str(e)
                carga.save()
                messages.error(request, f'Error al procesar archivo: {str(e)}')
            
            return redirect('detalle_carga', pk=carga.pk)
    else:
        form = CargaInventarioForm()
    
    # Mostrar cargas recientes
    cargas_recientes = CargaInventario.objects.filter(
        usuario=request.user
    ).order_by('-fecha_carga')[:10]
    
    return render(request, 'inventario/cargas/form.html', {
        'form': form,
        'cargas_recientes': cargas_recientes
    })


@login_required
def detalle_carga(request, pk):
    """Detalle de una carga de archivo"""
    carga = CargaInventario.objects.get(pk=pk, usuario=request.user)
    
    context = {
        'carga': carga,
        'errores': carga.log_errores.split('\n') if carga.log_errores else []
    }
    
    return render(request, 'inventario/cargas/detalle.html', context)


@login_required
def lista_cargas(request):
    """Lista de cargas de archivos del usuario"""
    cargas = CargaInventario.objects.filter(
        usuario=request.user
    ).order_by('-fecha_carga')
    
    return render(request, 'inventario/cargas/lista.html', {
        'cargas': cargas
    })


@login_required
@require_http_methods(["GET"])
def descargar_reporte_inventario(request):
    """Descarga reporte de inventario en Excel"""
    
    # Obtener filtros de la URL
    filtros = {}
    if request.GET.get('institucion'):
        try:
            filtros['institucion'] = Institucion.objects.get(pk=request.GET.get('institucion'))
        except Institucion.DoesNotExist:
            pass
    
    if request.GET.get('categoria'):
        try:
            filtros['categoria'] = CategoriaProducto.objects.get(pk=request.GET.get('categoria'))
        except CategoriaProducto.DoesNotExist:
            pass
    
    if request.GET.get('fecha_desde'):
        try:
            filtros['fecha_desde'] = date.fromisoformat(request.GET.get('fecha_desde'))
        except ValueError:
            pass
    
    if request.GET.get('fecha_hasta'):
        try:
            filtros['fecha_hasta'] = date.fromisoformat(request.GET.get('fecha_hasta'))
        except ValueError:
            pass
    
    # Generar reporte
    generator = ReportGenerator()
    excel_file = generator.generar_reporte_inventario_excel(filtros)
    
    # Preparar respuesta
    response = HttpResponse(
        excel_file.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    filename = f'reporte_inventario_{date.today().strftime("%Y%m%d")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_http_methods(["GET"])
def descargar_reporte_movimientos(request):
    """Descarga reporte de movimientos en Excel"""
    
    # Obtener filtros de fecha
    fecha_desde = None
    fecha_hasta = None
    
    if request.GET.get('fecha_desde'):
        try:
            fecha_desde = date.fromisoformat(request.GET.get('fecha_desde'))
        except ValueError:
            pass
    
    if request.GET.get('fecha_hasta'):
        try:
            fecha_hasta = date.fromisoformat(request.GET.get('fecha_hasta'))
        except ValueError:
            pass
    
    # Si no se especifican fechas, usar último mes
    if not fecha_desde and not fecha_hasta:
        fecha_hasta = date.today()
        fecha_desde = fecha_hasta - timedelta(days=30)
    
    # Generar reporte
    generator = ReportGenerator()
    excel_file = generator.generar_reporte_movimientos_excel(fecha_desde, fecha_hasta)
    
    # Preparar respuesta
    response = HttpResponse(
        excel_file.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    filename = f'reporte_movimientos_{date.today().strftime("%Y%m%d")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_http_methods(["GET"])
def descargar_reporte_caducidades(request):
    """Descarga reporte de caducidades en Excel"""
    
    # Generar reporte
    generator = ReportGenerator()
    excel_file = generator.generar_reporte_caducidades_excel()
    
    # Preparar respuesta
    response = HttpResponse(
        excel_file.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    filename = f'reporte_caducidades_{date.today().strftime("%Y%m%d")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
def reportes_dashboard(request):
    """Dashboard de reportes"""
    
    # Generar estadísticas
    generator = ReportGenerator()
    estadisticas = generator.generar_estadisticas_dashboard()
    
    # Formulario de filtros para reportes
    form_filtros = FiltroInventarioForm()
    
    context = {
        'estadisticas': estadisticas,
        'form_filtros': form_filtros,
    }
    
    return render(request, 'inventario/reportes/dashboard.html', context)


@login_required
def configuracion_sistema(request):
    """Vista de configuración del sistema"""
    
    # Estadísticas del sistema
    stats = {
        'total_usuarios': request.user.__class__.objects.count(),
        'total_cargas': CargaInventario.objects.count(),
        'cargas_exitosas': CargaInventario.objects.filter(estado='COMPLETADA').count(),
        'cargas_con_error': CargaInventario.objects.filter(estado='ERROR').count(),
        'espacio_archivos': _calcular_espacio_archivos(),
    }
    
    # Cargas recientes del sistema
    cargas_recientes = CargaInventario.objects.select_related(
        'usuario'
    ).order_by('-fecha_carga')[:20]
    
    context = {
        'stats': stats,
        'cargas_recientes': cargas_recientes,
    }
    
    return render(request, 'inventario/configuracion/sistema.html', context)


def _calcular_espacio_archivos():
    """Calcula el espacio usado por archivos cargados"""
    try:
        total_size = 0
        for carga in CargaInventario.objects.all():
            if carga.archivo and os.path.exists(carga.archivo.path):
                total_size += os.path.getsize(carga.archivo.path)
        
        # Convertir a MB
        return round(total_size / (1024 * 1024), 2)
    except:
        return 0


@login_required
def ayuda_sistema(request):
    """Vista de ayuda del sistema"""
    return render(request, 'inventario/ayuda/index.html')


@login_required
def manual_usuario(request):
    """Manual de usuario del sistema"""
    return render(request, 'inventario/ayuda/manual.html')
