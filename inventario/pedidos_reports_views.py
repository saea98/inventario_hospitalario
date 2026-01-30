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
from .pedidos_models import LogErrorPedido, SolicitudPedido, ItemSolicitud, PropuestaPedido, ItemPropuesta, LoteAsignado
from .pedidos_utils import obtener_resumen_errores
from .models import Producto, Institucion
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
    filtro_pedido = request.GET.get('pedido', '').strip()
    
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

    # Obtener folio del pedido (observaciones_solicitud) para cada error
    # Si hay filtro por pedido, procesar más registros para poder filtrar
    limite = 500 if filtro_pedido else 100
    errores_lista = list(errores[:limite])
    errores_con_folio = []
    for error in errores_lista:
        folio_pedido = _obtener_folio_pedido_para_error(error)
        folio_str = folio_pedido or '-'
        errores_con_folio.append({'error': error, 'folio_pedido': folio_str})
    # Aplicar filtro por pedido (folio) si está activo
    if filtro_pedido:
        termino = filtro_pedido.lower()
        errores_con_folio = [x for x in errores_con_folio if termino in (x['folio_pedido'] or '').lower()]
    errores_con_folio = errores_con_folio[:100]
    
    # Instituciones para filtro
    instituciones = Institucion.objects.filter(activo=True).order_by('denominacion')

    context = {
        'errores': [x['error'] for x in errores_con_folio],
        'errores_con_folio': errores_con_folio,
        'total_errores': total_errores,
        'errores_hoy': errores_hoy,
        'errores_semana': errores_semana,
        'errores_sin_alerta': errores_sin_alerta,
        'claves_frecuentes': claves_frecuentes,
        'tipos_frecuentes': tipos_frecuentes,
        'instituciones_frecuentes': instituciones_frecuentes,
        'usuarios_frecuentes': usuarios_frecuentes,
        'resumen': resumen,
        'errores_por_tipo': resumen.get('errores_por_tipo', {}),
        'alertas_enviadas': errores.filter(alerta_enviada=True).count(),
        'tipo_error_choices': LogErrorPedido.TIPO_ERROR_CHOICES,
        'instituciones': instituciones,
        'filtro_pedido': filtro_pedido,
        'filtro_institucion': institucion,
        'page_title': 'Reporte de Errores en Carga Masiva de Pedidos'
    }
    
    return render(request, 'inventario/pedidos/reporte_errores_pedidos.html', context)


def _obtener_folio_pedido_para_error(error):
    """
    Busca la solicitud relacionada con el error y retorna el folio del pedido
    (observaciones_solicitud). Se busca por clave+usuario+fecha.
    """
    try:
        producto = Producto.objects.get(clave_cnis=error.clave_solicitada)
        fecha_inicio = error.fecha_error - timedelta(hours=24)
        fecha_fin = error.fecha_error + timedelta(hours=1)
        items = ItemSolicitud.objects.filter(
            producto=producto,
            solicitud__fecha_solicitud__gte=fecha_inicio,
            solicitud__fecha_solicitud__lte=fecha_fin
        ).select_related('solicitud').order_by('-solicitud__fecha_solicitud')
        if error.usuario:
            items = items.filter(solicitud__usuario_solicitante=error.usuario)
        item = items.first()
        if item and item.solicitud:
            return (item.solicitud.observaciones_solicitud or '').strip() or (item.solicitud.folio or '')
    except Producto.DoesNotExist:
        if error.usuario:
            solicitud = SolicitudPedido.objects.filter(
                usuario_solicitante=error.usuario,
                fecha_solicitud__gte=error.fecha_error - timedelta(hours=24),
                fecha_solicitud__lte=error.fecha_error + timedelta(hours=1)
            ).order_by('-fecha_solicitud').first()
            if solicitud:
                return (solicitud.observaciones_solicitud or '').strip() or (solicitud.folio or '')
    return None


@login_required
def reporte_items_no_surtidos(request):
    """
    Reporte de items que no se surtieron (o se surtieron parcialmente) en las propuestas de suministro.
    Muestra ItemPropuesta donde cantidad_surtida < cantidad_propuesta.
    """
    from django.db.models import Sum

    # Filtros
    estado_propuesta = request.GET.get('estado', '')
    institucion_id = request.GET.get('institucion', '')
    folio = request.GET.get('folio', '').strip()
    clave_cnis = request.GET.get('clave_cnis', '').strip()

    # Base: propuestas con items
    propuestas = PropuestaPedido.objects.filter(
        solicitud__isnull=False
    ).select_related(
        'solicitud__institucion_solicitante',
        'solicitud__almacen_destino'
    ).prefetch_related(
        'items__producto',
        'items__lotes_asignados'
    ).order_by('-fecha_generacion')

    if estado_propuesta:
        propuestas = propuestas.filter(estado=estado_propuesta)
    if institucion_id:
        propuestas = propuestas.filter(solicitud__institucion_solicitante_id=institucion_id)
    if folio:
        propuestas = propuestas.filter(
            Q(solicitud__folio__icontains=folio) |
            Q(solicitud__observaciones_solicitud__icontains=folio)
        )
    if clave_cnis:
        propuestas = propuestas.filter(items__producto__clave_cnis__icontains=clave_cnis).distinct()

    # Recolectar items no surtidos (cantidad_propuesta > cantidad realmente surtida)
    items_no_surtidos = []
    for propuesta in propuestas:
        solicitud = propuesta.solicitud
        folio_pedido = (solicitud.observaciones_solicitud or '').strip() or (solicitud.folio or '')
        institucion_nombre = solicitud.institucion_solicitante.denominacion if solicitud.institucion_solicitante else '-'
        almacen_nombre = solicitud.almacen_destino.nombre if solicitud.almacen_destino else '-'

        for item in propuesta.items.all():
            if item.cantidad_propuesta <= 0:
                continue
            cantidad_surtida_real = item.lotes_asignados.filter(surtido=True).aggregate(
                total=Sum('cantidad_asignada')
            )['total'] or 0
            if cantidad_surtida_real < item.cantidad_propuesta:
                cantidad_faltante = item.cantidad_propuesta - cantidad_surtida_real
                if clave_cnis and clave_cnis.lower() not in (item.producto.clave_cnis or '').lower():
                    continue
                items_no_surtidos.append({
                    'propuesta': propuesta,
                    'item': item,
                    'producto': item.producto,
                    'folio_pedido': folio_pedido,
                    'institucion': institucion_nombre,
                    'almacen': almacen_nombre,
                    'cantidad_propuesta': item.cantidad_propuesta,
                    'cantidad_surtida': cantidad_surtida_real,
                    'cantidad_faltante': cantidad_faltante,
                    'estado_propuesta': propuesta.get_estado_display(),
                })

    # Instituciones para filtro
    instituciones = Institucion.objects.filter(activo=True).order_by('denominacion')

    context = {
        'items_no_surtidos': items_no_surtidos,
        'total_items': len(items_no_surtidos),
        'instituciones': instituciones,
        'filtro_estado': estado_propuesta,
        'filtro_institucion': institucion_id,
        'filtro_folio': folio,
        'filtro_clave': clave_cnis,
        'estado_choices': PropuestaPedido.ESTADO_CHOICES,
        'page_title': 'Reporte de Items No Surtidos en Propuestas',
    }
    return render(request, 'inventario/pedidos/reporte_items_no_surtidos.html', context)


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
def reporte_pedidos_sin_existencia(request):
    """
    Muestra un reporte de pedidos con claves sin existencia agrupado por destino (institución y almacén).
    Útil para ver qué destinos tienen más problemas de disponibilidad.
    """
    # Obtener errores sin existencia
    errores_sin_existencia = LogErrorPedido.objects.filter(
        tipo_error='SIN_EXISTENCIA'
    ).select_related('usuario', 'institucion', 'almacen', 'usuario__almacen', 'usuario__almacen__institucion').order_by('-fecha_error')
    
    # Aplicar filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    institucion_id = request.GET.get('institucion')
    almacen_id = request.GET.get('almacen')
    
    if fecha_inicio:
        try:
            from datetime import datetime
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            errores_sin_existencia = errores_sin_existencia.filter(fecha_error__gte=fecha_inicio_obj)
        except ValueError:
            pass
    
    if fecha_fin:
        try:
            from datetime import datetime, time as dt_time
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d')
            fecha_fin_obj = datetime.combine(fecha_fin_obj.date(), dt_time.max)
            errores_sin_existencia = errores_sin_existencia.filter(fecha_error__lte=fecha_fin_obj)
        except ValueError:
            pass
    
    # Filtros institución/almacén se aplican después por destino del pedido
    
    # Agrupar por destino (institución + almacén del pedido)
    from .models import Producto, Institucion, Almacen
    from .pedidos_models import ItemSolicitud
    pedidos_sin_existencia = {}
    
    for error in errores_sin_existencia:
        # Buscar la solicitud relacionada para obtener institución y almacén del pedido
        institucion = None
        almacen = None
        folio_pedido = None
        solicitud_relacionada = None
        
        # Buscar solicitud que contenga un item con la clave del error
        # Esto es más preciso que buscar solo por usuario y fecha
        try:
            # Buscar el producto por clave CNIS
            producto = Producto.objects.get(clave_cnis=error.clave_solicitada)
            
            # Buscar solicitudes que tengan items con este producto
            # Buscar en un rango de tiempo más amplio para asegurar encontrar la solicitud
            fecha_inicio_busqueda = error.fecha_error - timedelta(hours=24)  # 24 horas antes
            fecha_fin_busqueda = error.fecha_error + timedelta(hours=1)  # 1 hora después
            
            # Buscar items que coincidan con el producto y la fecha
            items_relacionados = ItemSolicitud.objects.filter(
                producto=producto,
                solicitud__fecha_solicitud__gte=fecha_inicio_busqueda,
                solicitud__fecha_solicitud__lte=fecha_fin_busqueda
            ).select_related('solicitud', 'solicitud__institucion_solicitante', 'solicitud__almacen_destino').order_by('-solicitud__fecha_solicitud')
            
            # Si hay usuario, filtrar por usuario también
            if error.usuario:
                items_relacionados = items_relacionados.filter(solicitud__usuario_solicitante=error.usuario)
            
            # Tomar la primera solicitud encontrada
            item_relacionado = items_relacionados.first()
            
            if item_relacionado and item_relacionado.solicitud:
                solicitud_relacionada = item_relacionado.solicitud
                # SIEMPRE usar institución y almacén del pedido cuando se encuentra la solicitud
                # Usar los campos correctos: institucion_solicitante y almacen_destino
                institucion = solicitud_relacionada.institucion_solicitante
                almacen = solicitud_relacionada.almacen_destino
                # Usar observaciones_solicitud (folio del pedido) - este es el campo correcto
                folio_pedido = solicitud_relacionada.observaciones_solicitud.strip() if solicitud_relacionada.observaciones_solicitud else (solicitud_relacionada.folio or '')
        except Producto.DoesNotExist:
            # Si el producto no existe, intentar buscar por usuario y fecha como respaldo
            if error.usuario:
                fecha_inicio_busqueda = error.fecha_error - timedelta(hours=24)
                fecha_fin_busqueda = error.fecha_error + timedelta(hours=1)
                
                solicitud_relacionada = SolicitudPedido.objects.filter(
                    usuario_solicitante=error.usuario,
                    fecha_solicitud__gte=fecha_inicio_busqueda,
                    fecha_solicitud__lte=fecha_fin_busqueda
                ).select_related('institucion_solicitante', 'almacen_destino').order_by('-fecha_solicitud').first()
                
                if solicitud_relacionada:
                    institucion = solicitud_relacionada.institucion_solicitante
                    almacen = solicitud_relacionada.almacen_destino
                    folio_pedido = solicitud_relacionada.observaciones_solicitud.strip() if solicitud_relacionada.observaciones_solicitud else (solicitud_relacionada.folio or '')
        
        # Solo incluir en el reporte errores que están en un pedido (tienen solicitud asociada)
        if not solicitud_relacionada:
            continue
        
        # Crear clave única por destino (siempre del pedido)
        institucion_nombre = institucion.denominacion if institucion else 'Sin institución'
        almacen_nombre = almacen.nombre if almacen else 'Sin almacén'
        destino_key = f"{institucion_nombre}|{almacen_nombre}"
        
        if destino_key not in pedidos_sin_existencia:
            pedidos_sin_existencia[destino_key] = {
                'institucion': institucion_nombre,
                'almacen': almacen_nombre,
                'institucion_obj': institucion,
                'almacen_obj': almacen,
                'total_claves': 0,
                'total_solicitudes': 0,
                'cantidad_total': 0,
                'claves': set(),
                'errores': []
            }
        
        # Agregar información
        pedidos_sin_existencia[destino_key]['total_solicitudes'] += 1
        pedidos_sin_existencia[destino_key]['cantidad_total'] += error.cantidad_solicitada or 0
        pedidos_sin_existencia[destino_key]['claves'].add(error.clave_solicitada)
        
        # Agregar error con folio del pedido
        error_data = {
            'error': error,
            'folio_pedido': folio_pedido
        }
        pedidos_sin_existencia[destino_key]['errores'].append(error_data)
        
        # Agregar folio a un set para mostrar en el resumen
        if folio_pedido:
            if 'folios_pedidos' not in pedidos_sin_existencia[destino_key]:
                pedidos_sin_existencia[destino_key]['folios_pedidos'] = set()
            pedidos_sin_existencia[destino_key]['folios_pedidos'].add(folio_pedido)
    
    # Procesar datos y obtener descripciones de productos
    for destino_data in pedidos_sin_existencia.values():
        destino_data['total_claves'] = len(destino_data['claves'])
        destino_data['claves'] = sorted(list(destino_data['claves']))
        
        # Obtener descripciones de productos
        claves_con_descripcion = []
        for clave in destino_data['claves']:
            descripcion = 'Producto no encontrado'
            try:
                producto = Producto.objects.get(clave_cnis=clave)
                descripcion = producto.descripcion
            except Producto.DoesNotExist:
                pass
            claves_con_descripcion.append({
                'clave': clave,
                'descripcion': descripcion
            })
        destino_data['claves_detalle'] = claves_con_descripcion
        destino_data['errores'] = destino_data['errores'][:10]  # Limitar a 10 errores recientes
        
        # Procesar folios de pedidos
        if 'folios_pedidos' in destino_data:
            destino_data['folios_pedidos'] = sorted(list(destino_data['folios_pedidos']))
            destino_data['total_folios'] = len(destino_data['folios_pedidos'])
        else:
            destino_data['folios_pedidos'] = []
            destino_data['total_folios'] = 0
    
    # Obtener instituciones y almacenes para filtros
    instituciones = Institucion.objects.filter(activo=True).order_by('denominacion')
    almacenes = Almacen.objects.filter(activo=True).order_by('nombre')
    
    context = {
        'pedidos_sin_existencia': sorted(
            pedidos_sin_existencia.values(),
            key=lambda x: x['total_solicitudes'],
            reverse=True
        ),
        'total_destinos': len(pedidos_sin_existencia),
        'instituciones': instituciones,
        'almacenes': almacenes,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'institucion_id': institucion_id,
        'almacen_id': almacen_id,
        'page_title': 'Reporte de Pedidos Sin Existencia por Destino'
    }
    
    return render(request, 'inventario/pedidos/reporte_pedidos_sin_existencia.html', context)


@login_required
def exportar_pedidos_sin_existencia_excel(request):
    """
    Exporta el reporte de pedidos sin existencia por destino a Excel
    """
    # Obtener errores sin existencia (mismo código que en la vista)
    errores_sin_existencia = LogErrorPedido.objects.filter(
        tipo_error='SIN_EXISTENCIA'
    ).select_related('usuario', 'institucion', 'almacen', 'usuario__almacen', 'usuario__almacen__institucion').order_by('-fecha_error')
    
    # Aplicar filtros (mismo que en la vista)
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    institucion_id = request.GET.get('institucion')
    almacen_id = request.GET.get('almacen')
    
    if fecha_inicio:
        try:
            from datetime import datetime
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            errores_sin_existencia = errores_sin_existencia.filter(fecha_error__gte=fecha_inicio_obj)
        except ValueError:
            pass
    
    if fecha_fin:
        try:
            from datetime import datetime, time as dt_time
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d')
            fecha_fin_obj = datetime.combine(fecha_fin_obj.date(), dt_time.max)
            errores_sin_existencia = errores_sin_existencia.filter(fecha_error__lte=fecha_fin_obj)
        except ValueError:
            pass
    
    # Filtros institución/almacén se aplican después por destino del pedido
    
    # Agrupar por destino (mismo código que en la vista)
    from .models import Producto
    from .pedidos_models import ItemSolicitud
    pedidos_sin_existencia = {}
    
    for error in errores_sin_existencia:
        # Buscar la solicitud relacionada para obtener institución y almacén del pedido
        institucion = None
        almacen = None
        folio_pedido = None
        solicitud_relacionada = None
        
        # Buscar solicitud que contenga un item con la clave del error
        # Esto es más preciso que buscar solo por usuario y fecha
        try:
            # Buscar el producto por clave CNIS
            producto = Producto.objects.get(clave_cnis=error.clave_solicitada)
            
            # Buscar solicitudes que tengan items con este producto
            # Buscar en un rango de tiempo más amplio para asegurar encontrar la solicitud
            fecha_inicio_busqueda = error.fecha_error - timedelta(hours=24)  # 24 horas antes
            fecha_fin_busqueda = error.fecha_error + timedelta(hours=1)  # 1 hora después
            
            # Buscar items que coincidan con el producto y la fecha
            items_relacionados = ItemSolicitud.objects.filter(
                producto=producto,
                solicitud__fecha_solicitud__gte=fecha_inicio_busqueda,
                solicitud__fecha_solicitud__lte=fecha_fin_busqueda
            ).select_related('solicitud', 'solicitud__institucion_solicitante', 'solicitud__almacen_destino').order_by('-solicitud__fecha_solicitud')
            
            # Si hay usuario, filtrar por usuario también
            if error.usuario:
                items_relacionados = items_relacionados.filter(solicitud__usuario_solicitante=error.usuario)
            
            # Tomar la primera solicitud encontrada
            item_relacionado = items_relacionados.first()
            
            if item_relacionado and item_relacionado.solicitud:
                solicitud_relacionada = item_relacionado.solicitud
                # SIEMPRE usar institución y almacén del pedido cuando se encuentra la solicitud
                # Usar los campos correctos: institucion_solicitante y almacen_destino
                institucion = solicitud_relacionada.institucion_solicitante
                almacen = solicitud_relacionada.almacen_destino
                # Usar observaciones_solicitud (folio del pedido) - este es el campo correcto
                folio_pedido = solicitud_relacionada.observaciones_solicitud.strip() if solicitud_relacionada.observaciones_solicitud else (solicitud_relacionada.folio or '')
        except Producto.DoesNotExist:
            # Si el producto no existe, intentar buscar por usuario y fecha como respaldo
            if error.usuario:
                fecha_inicio_busqueda = error.fecha_error - timedelta(hours=24)
                fecha_fin_busqueda = error.fecha_error + timedelta(hours=1)
                
                solicitud_relacionada = SolicitudPedido.objects.filter(
                    usuario_solicitante=error.usuario,
                    fecha_solicitud__gte=fecha_inicio_busqueda,
                    fecha_solicitud__lte=fecha_fin_busqueda
                ).select_related('institucion_solicitante', 'almacen_destino').order_by('-fecha_solicitud').first()
                
                if solicitud_relacionada:
                    institucion = solicitud_relacionada.institucion_solicitante
                    almacen = solicitud_relacionada.almacen_destino
                    folio_pedido = solicitud_relacionada.observaciones_solicitud.strip() if solicitud_relacionada.observaciones_solicitud else (solicitud_relacionada.folio or '')
        
        # Solo incluir en el reporte errores que están en un pedido (tienen solicitud asociada)
        if not solicitud_relacionada:
            continue
        
        # Aplicar filtros por destino del pedido (institución/almacén)
        if institucion_id and (not institucion or str(institucion.id) != str(institucion_id)):
            continue
        if almacen_id and (not almacen or str(almacen.id) != str(almacen_id)):
            continue
        
        # Crear clave única por destino (siempre del pedido)
        institucion_nombre = institucion.denominacion if institucion else 'Sin institución'
        almacen_nombre = almacen.nombre if almacen else 'Sin almacén'
        destino_key = f"{institucion_nombre}|{almacen_nombre}"
        
        if destino_key not in pedidos_sin_existencia:
            pedidos_sin_existencia[destino_key] = {
                'institucion': institucion_nombre,
                'almacen': almacen_nombre,
                'total_claves': 0,
                'total_solicitudes': 0,
                'cantidad_total': 0,
                'claves': set(),
                'folios_pedidos': set(),
            }
        
        pedidos_sin_existencia[destino_key]['total_solicitudes'] += 1
        pedidos_sin_existencia[destino_key]['cantidad_total'] += error.cantidad_solicitada or 0
        pedidos_sin_existencia[destino_key]['claves'].add(error.clave_solicitada)
        
        # Agregar folio del pedido si existe
        if folio_pedido:
            pedidos_sin_existencia[destino_key]['folios_pedidos'].add(folio_pedido)
    
    # Procesar datos
    for destino_data in pedidos_sin_existencia.values():
        destino_data['total_claves'] = len(destino_data.get('claves', set()))
        destino_data['claves'] = ', '.join(sorted(list(destino_data.get('claves', set())))) if destino_data.get('claves') else ''
        destino_data['folios_pedidos'] = ', '.join(sorted(list(destino_data.get('folios_pedidos', set())))) if destino_data.get('folios_pedidos') else ''
    
    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Pedidos Sin Existencia por Destino'
    
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
    headers = ['Institución Destino', 'Almacén Destino', 'Folio(s) Pedido', 'Total Claves', 'Total Solicitudes', 'Cantidad Total Solicitada', 'Claves Afectadas']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border
    
    # Datos
    for row, destino_data in enumerate(sorted(
        pedidos_sin_existencia.values(),
        key=lambda x: x['total_solicitudes'],
        reverse=True
    ), 2):
        # Asegurar que todos los valores sean strings o números, nunca None
        ws.cell(row=row, column=1).value = str(destino_data.get('institucion', 'Sin institución') or 'Sin institución')
        ws.cell(row=row, column=2).value = str(destino_data.get('almacen', 'Sin almacén') or 'Sin almacén')
        ws.cell(row=row, column=3).value = str(destino_data.get('folios_pedidos', '') or '')
        ws.cell(row=row, column=4).value = destino_data.get('total_claves', 0) or 0
        ws.cell(row=row, column=5).value = destino_data.get('total_solicitudes', 0) or 0
        ws.cell(row=row, column=6).value = destino_data.get('cantidad_total', 0) or 0
        ws.cell(row=row, column=7).value = str(destino_data.get('claves', '') or '')
        
        for col in range(1, 8):
            cell = ws.cell(row=row, column=col)
            cell.border = border
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    
    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 18
    ws.column_dimensions['F'].width = 25
    ws.column_dimensions['G'].width = 50
    
    # Generar respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="pedidos_sin_existencia_por_destino.xlsx"'
    wb.save(response)
    
    return response


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
    headers = ['Clave', 'Descripción', 'Cantidad Total Solicitada', 'Total Solicitudes', 'Prioridad']
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
        ws.cell(row=row, column=5).value = ''  # Prioridad: vacío para que lo llene quien corresponda
        
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
