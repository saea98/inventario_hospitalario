from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
import json

from .models import (
    MovimientoInventario, 
    LoteUbicacion, 
    OrdenSuministro, 
    CitaProveedor,
    Institucion,
    Almacen,
    User
)


@login_required
def dashboard_movimientos(request):
    """Dashboard de movimientos diarios consolidado"""
    
    # Obtener la fecha actual en la zona horaria configurada (UTC-6)
    fecha_hoy = timezone.localtime(timezone.now()).date()
    
    # Obtener fecha del filtro o usar la actual
    fecha_str = request.GET.get('fecha', fecha_hoy.isoformat())
    try:
        fecha_filtro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except:
        fecha_filtro = fecha_hoy
    
    # Rango de fecha (desde las 00:00 hasta las 23:59)
    inicio_dia = timezone.make_aware(datetime.combine(fecha_filtro, datetime.min.time()))
    fin_dia = timezone.make_aware(datetime.combine(fecha_filtro, datetime.max.time()))
    
    # Obtener filtros
    tipo_movimiento = request.GET.get('tipo_movimiento', '')
    usuario_id = request.GET.get('usuario', '')
    institucion_id = request.GET.get('institucion', '')
    almacen_id = request.GET.get('almacen', '')
    
    # Inicializar lista de movimientos consolidados
    movimientos_consolidados = []
    
    # 1. Movimientos de Inventario
    movimientos_inv = MovimientoInventario.objects.filter(
        fecha_movimiento__gte=inicio_dia,
        fecha_movimiento__lte=fin_dia,
        anulado=False
    ).select_related('lote', 'lote__producto', 'lote__institucion', 'usuario')
    
    if usuario_id:
        movimientos_inv = movimientos_inv.filter(usuario_id=usuario_id)
    if institucion_id:
        movimientos_inv = movimientos_inv.filter(lote__institucion_id=institucion_id)
    
    for mov in movimientos_inv:
        movimientos_consolidados.append({
            'tipo': 'Movimiento de Inventario',
            'subtipo': mov.get_tipo_movimiento_display(),
            'fecha': mov.fecha_movimiento,
            'producto': mov.lote.producto.clave_cnis if mov.lote.producto else '-',
            'descripcion_producto': mov.lote.producto.descripcion[:50] if mov.lote.producto else '-',
            'lote': mov.lote.numero_lote,
            'cantidad': mov.cantidad,
            'institucion': mov.lote.institucion.denominacion if mov.lote.institucion else '-',
            'usuario': mov.usuario.get_full_name() or mov.usuario.username,
            'motivo': mov.motivo[:100],
            'folio': mov.folio or '-',
            'id': f'mov_{mov.id}'
        })
    
    # 2. Asignación de Ubicaciones
    asignaciones = LoteUbicacion.objects.filter(
        fecha_asignacion__gte=inicio_dia,
        fecha_asignacion__lte=fin_dia
    ).select_related('lote', 'lote__producto', 'lote__institucion', 'ubicacion', 'usuario_asignacion')
    
    if usuario_id:
        asignaciones = asignaciones.filter(usuario_asignacion_id=usuario_id)
    if institucion_id:
        asignaciones = asignaciones.filter(lote__institucion_id=institucion_id)
    
    for asig in asignaciones:
        movimientos_consolidados.append({
            'tipo': 'Asignación de Ubicación',
            'subtipo': 'Asignación',
            'fecha': asig.fecha_asignacion,
            'producto': asig.lote.producto.clave_cnis if asig.lote.producto else '-',
            'descripcion_producto': asig.lote.producto.descripcion[:50] if asig.lote.producto else '-',
            'lote': asig.lote.numero_lote,
            'cantidad': asig.cantidad,
            'institucion': asig.lote.institucion.denominacion if asig.lote.institucion else '-',
            'usuario': asig.usuario_asignacion.get_full_name() or asig.usuario_asignacion.username if asig.usuario_asignacion else '-',
            'motivo': f"Ubicación: {asig.ubicacion.codigo}",
            'folio': asig.lote.numero_lote,
            'id': f'asig_{asig.id}'
        })
    
    # 3. Órdenes de Suministro
    ordenes = OrdenSuministro.objects.filter(
        fecha_creacion__gte=inicio_dia,
        fecha_creacion__lte=fin_dia
    ).select_related('proveedor')
    
    for orden in ordenes:
        movimientos_consolidados.append({
            'tipo': 'Orden de Suministro',
            'subtipo': 'Creación',
            'fecha': orden.fecha_creacion,
            'producto': '-',
            'descripcion_producto': f"Proveedor: {orden.proveedor.razon_social if orden.proveedor else '-'}",
            'lote': '-',
            'cantidad': '-',
            'institucion': '-',
            'usuario': '-',
            'motivo': f"Orden: {orden.numero_orden}",
            'folio': orden.numero_orden,
            'id': f'orden_{orden.id}'
        })
    
    # 4. Citas con Proveedores
    citas = CitaProveedor.objects.filter(
        fecha_creacion__gte=inicio_dia,
        fecha_creacion__lte=fin_dia
    ).select_related('proveedor', 'almacen', 'usuario_creacion')
    
    for cita in citas:
        movimientos_consolidados.append({
            'tipo': 'Cita con Proveedor',
            'subtipo': cita.get_estado_display(),
            'fecha': cita.fecha_creacion,
            'producto': '-',
            'descripcion_producto': f"Proveedor: {cita.proveedor.razon_social if cita.proveedor else '-'}",
            'lote': '-',
            'cantidad': '-',
            'institucion': '-',
            'usuario': cita.usuario_creacion.get_full_name() or cita.usuario_creacion.username if cita.usuario_creacion else '-',
            'motivo': f"Almacén: {cita.almacen.nombre}",
            'folio': f"Cita {cita.id}",
            'id': f'cita_{cita.id}'
        })
    
    # Ordenar por fecha descendente
    movimientos_consolidados.sort(key=lambda x: x['fecha'], reverse=True)
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(movimientos_consolidados, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calcular estadísticas
    estadisticas = {
        'total_movimientos': len(movimientos_consolidados),
        'por_tipo': {},
        'por_usuario': {},
        'por_institucion': {}
    }
    
    for mov in movimientos_consolidados:
        # Por tipo
        tipo = mov['tipo']
        estadisticas['por_tipo'][tipo] = estadisticas['por_tipo'].get(tipo, 0) + 1
        
        # Por usuario
        usuario = mov['usuario']
        estadisticas['por_usuario'][usuario] = estadisticas['por_usuario'].get(usuario, 0) + 1
        
        # Por institución
        institucion = mov['institucion']
        if institucion != '-':
            estadisticas['por_institucion'][institucion] = estadisticas['por_institucion'].get(institucion, 0) + 1
    
    # Obtener opciones de filtro
    usuarios = User.objects.filter(is_active=True).order_by('first_name')
    instituciones = Institucion.objects.all().order_by('denominacion')
    almacenes = Almacen.objects.all().order_by('nombre')
    
    context = {
        'page_obj': page_obj,
        'estadisticas': estadisticas,
        'fecha_filtro': fecha_filtro,
        'usuarios': usuarios,
        'instituciones': instituciones,
        'almacenes': almacenes,
        'usuario_seleccionado': usuario_id,
        'institucion_seleccionada': institucion_id,
        'almacen_seleccionado': almacen_id,
    }
    
    return render(request, 'inventario/dashboard/movimientos.html', context)


@login_required
def api_estadisticas_movimientos(request):
    """API para obtener estadísticas en formato JSON"""
    
    fecha_str = request.GET.get('fecha', timezone.now().date().isoformat())
    try:
        fecha_filtro = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except:
        fecha_filtro = timezone.now().date()
    
    inicio_dia = timezone.make_aware(datetime.combine(fecha_filtro, datetime.min.time()))
    fin_dia = timezone.make_aware(datetime.combine(fecha_filtro, datetime.max.time()))
    
    # Estadísticas por tipo de movimiento
    movimientos = MovimientoInventario.objects.filter(
        fecha_movimiento__gte=inicio_dia,
        fecha_movimiento__lte=fin_dia,
        anulado=False
    ).values('tipo_movimiento').annotate(count=Count('id'))
    
    tipos_data = {item['tipo_movimiento']: item['count'] for item in movimientos}
    
    # Contar otros tipos
    asignaciones_count = LoteUbicacion.objects.filter(
        fecha_asignacion__gte=inicio_dia,
        fecha_asignacion__lte=fin_dia
    ).count()
    
    ordenes_count = OrdenSuministro.objects.filter(
        fecha_creacion__gte=inicio_dia,
        fecha_creacion__lte=fin_dia
    ).count()
    
    citas_count = CitaProveedor.objects.filter(
        fecha_creacion__gte=inicio_dia,
        fecha_creacion__lte=fin_dia
    ).count()
    
    if asignaciones_count > 0:
        tipos_data['Asignación de Ubicación'] = asignaciones_count
    if ordenes_count > 0:
        tipos_data['Orden de Suministro'] = ordenes_count
    if citas_count > 0:
        tipos_data['Cita con Proveedor'] = citas_count
    
    return JsonResponse({
        'tipos': tipos_data,
        'total': sum(tipos_data.values())
    })
