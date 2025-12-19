"""
Vistas para Reportes de Salidas y Distribuciones
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, F, DecimalField, Count, Q
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import SalidaExistencias, ItemSalidaExistencias, DistribucionArea, ItemDistribucion
from .decorators_roles import requiere_rol


# ============================================================
# REPORTES GENERALES
# ============================================================

@login_required
@requiere_rol(['Administrador', 'Gestor de Inventario'])
def reporte_general_salidas(request):
    """Reporte general de salidas"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado')
    
    salidas = SalidaExistencias.objects.filter(institucion=institucion)
    
    if fecha_inicio:
        salidas = salidas.filter(fecha_creacion__date__gte=fecha_inicio)
    if fecha_fin:
        salidas = salidas.filter(fecha_creacion__date__lte=fecha_fin)
    if estado:
        salidas = salidas.filter(estado=estado)
    
    # Estadísticas
    total_salidas = salidas.count()
    total_items = salidas.aggregate(
        total=Sum('itemsalidaexistencias__cantidad')
    )['total'] or 0
    
    total_monto = salidas.aggregate(
        total=Sum(
            F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'),
            output_field=DecimalField()
        )
    )['total'] or Decimal('0.00')
    
    # Salidas por estado
    salidas_por_estado = salidas.values('estado').annotate(
        cantidad=Count('id'),
        monto=Sum(
            F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'),
            output_field=DecimalField()
        )
    )
    
    # Salidas por almacén
    salidas_por_almacen = salidas.values('almacen__nombre').annotate(
        cantidad=Count('id'),
        items=Sum('itemsalidaexistencias__cantidad'),
        monto=Sum(
            F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'),
            output_field=DecimalField()
        )
    ).order_by('-monto')
    
    # Productos más salidos
    productos_top = ItemSalidaExistencias.objects.filter(
        salida__institucion=institucion
    ).values('lote__producto__nombre').annotate(
        cantidad_total=Sum('cantidad'),
        monto_total=Sum(
            F('cantidad') * F('precio_unitario'),
            output_field=DecimalField()
        )
    ).order_by('-cantidad_total')[:10]
    
    context = {
        'total_salidas': total_salidas,
        'total_items': total_items,
        'total_monto': total_monto,
        'salidas_por_estado': list(salidas_por_estado),
        'salidas_por_almacen': list(salidas_por_almacen),
        'productos_top': list(productos_top),
        'estados': SalidaExistencias.ESTADOS_SALIDA,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado_filtro': estado,
    }
    
    return render(request, 'inventario/reportes_salidas/reporte_general.html', context)


# ============================================================
# ANÁLISIS DE DISTRIBUCIONES
# ============================================================

@login_required
@requiere_rol(['Administrador', 'Gestor de Inventario'])
def analisis_distribuciones(request):
    """Análisis de distribuciones a áreas"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado')
    
    distribuciones = DistribucionArea.objects.filter(
        salida__institucion=institucion
    )
    
    if fecha_inicio:
        distribuciones = distribuciones.filter(fecha_creacion__date__gte=fecha_inicio)
    if fecha_fin:
        distribuciones = distribuciones.filter(fecha_creacion__date__lte=fecha_fin)
    if estado:
        distribuciones = distribuciones.filter(estado=estado)
    
    # Estadísticas
    total_distribuciones = distribuciones.count()
    total_items_distribuidos = distribuciones.aggregate(
        total=Sum('itemdistribucion__cantidad')
    )['total'] or 0
    
    total_monto_distribuido = distribuciones.aggregate(
        total=Sum(
            F('itemdistribucion__cantidad') * F('itemdistribucion__precio_unitario'),
            output_field=DecimalField()
        )
    )['total'] or Decimal('0.00')
    
    # Distribuciones por estado
    dist_por_estado = distribuciones.values('estado').annotate(
        cantidad=Count('id'),
        monto=Sum(
            F('itemdistribucion__cantidad') * F('itemdistribucion__precio_unitario'),
            output_field=DecimalField()
        )
    )
    
    # Distribuciones por área
    dist_por_area = distribuciones.values('area_destino').annotate(
        cantidad=Count('id'),
        items=Sum('itemdistribucion__cantidad'),
        monto=Sum(
            F('itemdistribucion__cantidad') * F('itemdistribucion__precio_unitario'),
            output_field=DecimalField()
        )
    ).order_by('-monto')
    
    # Áreas con más distribuciones
    areas_top = dist_por_area[:10]
    
    context = {
        'total_distribuciones': total_distribuciones,
        'total_items_distribuidos': total_items_distribuidos,
        'total_monto_distribuido': total_monto_distribuido,
        'dist_por_estado': list(dist_por_estado),
        'dist_por_area': list(dist_por_area),
        'areas_top': list(areas_top),
        'estados': DistribucionArea.ESTADOS_DISTRIBUCION,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado_filtro': estado,
    }
    
    return render(request, 'inventario/reportes_salidas/analisis_distribuciones.html', context)


# ============================================================
# ANÁLISIS TEMPORAL
# ============================================================

@login_required
@requiere_rol(['Administrador', 'Gestor de Inventario'])
def analisis_temporal_salidas(request):
    """Análisis temporal de salidas"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Período por defecto: últimos 30 días
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Permitir filtro personalizado
    param_inicio = request.GET.get('fecha_inicio')
    param_fin = request.GET.get('fecha_fin')
    
    if param_inicio:
        fecha_inicio = param_inicio
    if param_fin:
        fecha_fin = param_fin
    
    salidas = SalidaExistencias.objects.filter(
        institucion=institucion,
        fecha_creacion__date__gte=fecha_inicio,
        fecha_creacion__date__lte=fecha_fin
    )
    
    # Salidas por día
    salidas_por_dia = salidas.values('fecha_creacion__date').annotate(
        cantidad=Count('id'),
        items=Sum('itemsalidaexistencias__cantidad'),
        monto=Sum(
            F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'),
            output_field=DecimalField()
        )
    ).order_by('fecha_creacion__date')
    
    # Salidas por semana
    salidas_por_semana = salidas.values('fecha_creacion__week').annotate(
        cantidad=Count('id'),
        items=Sum('itemsalidaexistencias__cantidad'),
        monto=Sum(
            F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'),
            output_field=DecimalField()
        )
    ).order_by('fecha_creacion__week')
    
    # Salidas por mes
    salidas_por_mes = salidas.values('fecha_creacion__month').annotate(
        cantidad=Count('id'),
        items=Sum('itemsalidaexistencias__cantidad'),
        monto=Sum(
            F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'),
            output_field=DecimalField()
        )
    ).order_by('fecha_creacion__month')
    
    context = {
        'salidas_por_dia': list(salidas_por_dia),
        'salidas_por_semana': list(salidas_por_semana),
        'salidas_por_mes': list(salidas_por_mes),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_salidas': salidas.count(),
    }
    
    return render(request, 'inventario/reportes_salidas/analisis_temporal.html', context)


# ============================================================
# APIs PARA GRÁFICOS DE REPORTES
# ============================================================

@login_required
@require_http_methods(["GET"])
def api_grafico_salidas_por_estado(request):
    """API para gráfico de salidas por estado"""
    
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    salidas = SalidaExistencias.objects.filter(institucion=institucion)
    
    datos = salidas.values('estado').annotate(
        cantidad=Count('id'),
        monto=Sum(
            F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'),
            output_field=DecimalField()
        )
    )
    
    labels = []
    cantidades = []
    montos = []
    colores = {'PENDIENTE': '#FFC107', 'AUTORIZADA': '#17A2B8', 'COMPLETADA': '#28A745', 'CANCELADA': '#DC3545'}
    colors = []
    
    for d in datos:
        estado = d['estado']
        labels.append(dict(SalidaExistencias.ESTADOS_SALIDA).get(estado, estado))
        cantidades.append(d['cantidad'])
        montos.append(float(d['monto'] or 0))
        colors.append(colores.get(estado, '#6C757D'))
    
    return JsonResponse({
        'labels': labels,
        'cantidades': cantidades,
        'montos': montos,
        'colors': colors
    })


@login_required
@require_http_methods(["GET"])
def api_grafico_salidas_por_almacen(request):
    """API para gráfico de salidas por almacén"""
    
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    salidas = SalidaExistencias.objects.filter(institucion=institucion)
    
    datos = salidas.values('almacen__nombre').annotate(
        cantidad=Count('id'),
        items=Sum('itemsalidaexistencias__cantidad'),
        monto=Sum(
            F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'),
            output_field=DecimalField()
        )
    ).order_by('-monto')[:10]
    
    labels = [d['almacen__nombre'] for d in datos]
    cantidades = [d['cantidad'] for d in datos]
    items = [d['items'] or 0 for d in datos]
    montos = [float(d['monto'] or 0) for d in datos]
    
    return JsonResponse({
        'labels': labels,
        'cantidades': cantidades,
        'items': items,
        'montos': montos
    })


@login_required
@require_http_methods(["GET"])
def api_grafico_distribuciones_por_estado(request):
    """API para gráfico de distribuciones por estado"""
    
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    distribuciones = DistribucionArea.objects.filter(
        salida__institucion=institucion
    )
    
    datos = distribuciones.values('estado').annotate(
        cantidad=Count('id'),
        monto=Sum(
            F('itemdistribucion__cantidad') * F('itemdistribucion__precio_unitario'),
            output_field=DecimalField()
        )
    )
    
    labels = []
    cantidades = []
    colores = {'PENDIENTE': '#FFC107', 'EN_TRANSITO': '#17A2B8', 'ENTREGADA': '#28A745', 'RECHAZADA': '#DC3545'}
    colors = []
    
    for d in datos:
        estado = d['estado']
        labels.append(dict(DistribucionArea.ESTADOS_DISTRIBUCION).get(estado, estado))
        cantidades.append(d['cantidad'])
        colors.append(colores.get(estado, '#6C757D'))
    
    return JsonResponse({
        'labels': labels,
        'data': cantidades,
        'colors': colors
    })


@login_required
@require_http_methods(["GET"])
def api_grafico_salidas_por_dia(request):
    """API para gráfico de salidas por día"""
    
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    # Últimos 30 días
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    salidas = SalidaExistencias.objects.filter(
        institucion=institucion,
        fecha_creacion__date__gte=fecha_inicio,
        fecha_creacion__date__lte=fecha_fin
    )
    
    datos = salidas.values('fecha_creacion__date').annotate(
        cantidad=Count('id'),
        monto=Sum(
            F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'),
            output_field=DecimalField()
        )
    ).order_by('fecha_creacion__date')
    
    labels = [d['fecha_creacion__date'].strftime('%d/%m') for d in datos]
    cantidades = [d['cantidad'] for d in datos]
    montos = [float(d['monto'] or 0) for d in datos]
    
    return JsonResponse({
        'labels': labels,
        'cantidades': cantidades,
        'montos': montos
    })
