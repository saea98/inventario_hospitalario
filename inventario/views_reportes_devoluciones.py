"""
Vistas para Reportes y Análisis de Devoluciones de Proveedores
Fase 2.5 - Reportes y Análisis Avanzados
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, F, DecimalField, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta, datetime
import json
from decimal import Decimal

from .models import DevolucionProveedor, ItemDevolucion, Proveedor


# ============================================================
# REPORTES GENERALES
# ============================================================

@login_required
def reporte_general_devoluciones(request):
    """Reporte general de devoluciones con estadísticas básicas"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        messages.error(request, 'No tienes una institución asignada')
        return redirect('devoluciones:lista_devoluciones')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    estado_filtro = request.GET.get('estado', '')
    proveedor_filtro = request.GET.get('proveedor', '')
    
    # Query base
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    # Aplicar filtros
    if fecha_inicio:
        try:
            devoluciones = devoluciones.filter(fecha_creacion__gte=datetime.strptime(fecha_inicio, '%Y-%m-%d'))
        except ValueError:
            pass
    
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d') + timedelta(days=1)
            devoluciones = devoluciones.filter(fecha_creacion__lt=fecha_fin_dt)
        except ValueError:
            pass
    
    if estado_filtro:
        devoluciones = devoluciones.filter(estado=estado_filtro)
    
    if proveedor_filtro:
        devoluciones = devoluciones.filter(proveedor_id=proveedor_filtro)
    
    # Estadísticas generales
    total_devoluciones = devoluciones.count()
    total_monto = devoluciones.aggregate(total=Sum('total_valor', output_field=DecimalField()))['total'] or Decimal('0.00')
    total_items = ItemDevolucion.objects.filter(devolucion__in=devoluciones).aggregate(total=Sum('cantidad'))['total'] or 0
    
    # Por estado
    por_estado = devoluciones.values('estado').annotate(
        cantidad=Count('id'),
        monto=Sum('total_valor', output_field=DecimalField())
    ).order_by('estado')
    
    # Promedio por devolución
    promedio_monto = total_monto / total_devoluciones if total_devoluciones > 0 else Decimal('0.00')
    promedio_items = total_items / total_devoluciones if total_devoluciones > 0 else 0
    
    # Proveedores
    proveedores = Proveedor.objects.filter(institucion=institucion).order_by('razon_social')
    
    context = {
        'total_devoluciones': total_devoluciones,
        'total_monto': total_monto,
        'total_items': total_items,
        'promedio_monto': promedio_monto,
        'promedio_items': promedio_items,
        'por_estado': por_estado,
        'devoluciones': devoluciones[:20],  # Últimas 20
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado_filtro': estado_filtro,
        'proveedor_filtro': proveedor_filtro,
        'proveedores': proveedores,
        'estados': [('PENDIENTE', 'Pendiente'), ('AUTORIZADA', 'Autorizada'), ('COMPLETADA', 'Completada'), ('CANCELADA', 'Cancelada')],
    }
    
    return render(request, 'inventario/reportes/reporte_general_devoluciones.html', context)


# ============================================================
# ANÁLISIS DE PROVEEDORES
# ============================================================

@login_required
def analisis_proveedores(request):
    """Análisis detallado de proveedores y sus devoluciones"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        messages.error(request, 'No tienes una institución asignada')
        return redirect('devoluciones:lista_devoluciones')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    
    # Query base
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    # Aplicar filtros de fecha
    if fecha_inicio:
        try:
            devoluciones = devoluciones.filter(fecha_creacion__gte=datetime.strptime(fecha_inicio, '%Y-%m-%d'))
        except ValueError:
            pass
    
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d') + timedelta(days=1)
            devoluciones = devoluciones.filter(fecha_creacion__lt=fecha_fin_dt)
        except ValueError:
            pass
    
    # Análisis por proveedor
    analisis_proveedores = devoluciones.values('proveedor__id', 'proveedor__razon_social').annotate(
        total_devoluciones=Count('id'),
        monto_total=Sum('total_valor', output_field=DecimalField()),
        items_total=Sum('itemdevolucion__cantidad'),
        monto_promedio=Avg('total_valor', output_field=DecimalField()),
        pendientes=Count('id', filter=Q(estado='PENDIENTE')),
        autorizadas=Count('id', filter=Q(estado='AUTORIZADA')),
        completadas=Count('id', filter=Q(estado='COMPLETADA')),
        canceladas=Count('id', filter=Q(estado='CANCELADA')),
    ).order_by('-monto_total')
    
    # Motivos más frecuentes
    motivos_frecuentes = devoluciones.values('motivo_general').annotate(
        cantidad=Count('id'),
        monto=Sum('total_valor', output_field=DecimalField())
    ).order_by('-cantidad')[:10]
    
    context = {
        'analisis_proveedores': analisis_proveedores,
        'motivos_frecuentes': motivos_frecuentes,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_proveedores': len(analisis_proveedores),
    }
    
    return render(request, 'inventario/reportes/analisis_proveedores.html', context)


# ============================================================
# ANÁLISIS TEMPORAL
# ============================================================

@login_required
def analisis_temporal(request):
    """Análisis de tendencias temporales de devoluciones"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        messages.error(request, 'No tienes una institución asignada')
        return redirect('devoluciones:lista_devoluciones')
    
    # Filtros
    tipo_periodo = request.GET.get('tipo_periodo', 'mes')  # mes, año
    
    # Query base
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    # Agrupar por período
    if tipo_periodo == 'mes':
        tendencia = devoluciones.annotate(
            periodo=TruncMonth('fecha_creacion')
        ).values('periodo').annotate(
            cantidad=Count('id'),
            monto=Sum('total_valor', output_field=DecimalField()),
            items=Sum('itemdevolucion__cantidad'),
        ).order_by('periodo')
    else:  # año
        tendencia = devoluciones.annotate(
            periodo=TruncYear('fecha_creacion')
        ).values('periodo').annotate(
            cantidad=Count('id'),
            monto=Sum('total_valor', output_field=DecimalField()),
            items=Sum('itemdevolucion__cantidad'),
        ).order_by('periodo')
    
    # Tiempo promedio de autorización
    autorizadas = devoluciones.filter(estado__in=['AUTORIZADA', 'COMPLETADA'], fecha_autorizacion__isnull=False)
    tiempo_promedio_autorizacion = None
    if autorizadas.exists():
        tiempos = []
        for dev in autorizadas:
            if dev.fecha_autorizacion and dev.fecha_creacion:
                tiempo = (dev.fecha_autorizacion - dev.fecha_creacion).total_seconds() / 86400
                tiempos.append(tiempo)
        if tiempos:
            tiempo_promedio_autorizacion = sum(tiempos) / len(tiempos)
    
    # Tiempo promedio de entrega
    completadas = devoluciones.filter(estado='COMPLETADA', fecha_entrega_real__isnull=False)
    tiempo_promedio_entrega = None
    if completadas.exists():
        tiempos = []
        for dev in completadas:
            if dev.fecha_entrega_real and dev.fecha_creacion:
                tiempo = (dev.fecha_entrega_real - dev.fecha_creacion.date()).days
                tiempos.append(tiempo)
        if tiempos:
            tiempo_promedio_entrega = sum(tiempos) / len(tiempos)
    
    context = {
        'tendencia': tendencia,
        'tipo_periodo': tipo_periodo,
        'tiempo_promedio_autorizacion': tiempo_promedio_autorizacion,
        'tiempo_promedio_entrega': tiempo_promedio_entrega,
    }
    
    return render(request, 'inventario/reportes/analisis_temporal.html', context)


# ============================================================
# API PARA GRÁFICOS (JSON)
# ============================================================

@login_required
def api_grafico_estado(request):
    """API para obtener datos de gráfico de estados"""
    
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    datos = devoluciones.values('estado').annotate(
        cantidad=Count('id')
    ).order_by('estado')
    
    labels = []
    values = []
    colors = {
        'PENDIENTE': '#FFC107',
        'AUTORIZADA': '#17A2B8',
        'COMPLETADA': '#28A745',
        'CANCELADA': '#6C757D',
    }
    
    for item in datos:
        labels.append(item['estado'])
        values.append(item['cantidad'])
    
    return JsonResponse({
        'labels': labels,
        'data': values,
        'colors': [colors.get(label, '#999') for label in labels],
    })


@login_required
def api_grafico_proveedores(request):
    """API para obtener datos de gráfico de proveedores"""
    
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    datos = devoluciones.values('proveedor__razon_social').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')[:10]
    
    labels = [item['proveedor__razon_social'] for item in datos]
    values = [item['cantidad'] for item in datos]
    
    return JsonResponse({
        'labels': labels,
        'data': values,
    })


@login_required
def api_grafico_tendencia(request):
    """API para obtener datos de gráfico de tendencia temporal"""
    
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    # Últimos 12 meses
    fecha_inicio = timezone.now() - timedelta(days=365)
    devoluciones = devoluciones.filter(fecha_creacion__gte=fecha_inicio)
    
    tendencia = devoluciones.annotate(
        periodo=TruncMonth('fecha_creacion')
    ).values('periodo').annotate(
        cantidad=Count('id'),
        monto=Sum('total_valor', output_field=DecimalField()),
    ).order_by('periodo')
    
    labels = [item['periodo'].strftime('%b %Y') if item['periodo'] else 'N/A' for item in tendencia]
    values_cantidad = [item['cantidad'] for item in tendencia]
    values_monto = [float(item['monto'] or 0) for item in tendencia]
    
    return JsonResponse({
        'labels': labels,
        'data_cantidad': values_cantidad,
        'data_monto': values_monto,
    })


@login_required
def api_grafico_motivos(request):
    """API para obtener datos de gráfico de motivos"""
    
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    datos = devoluciones.values('motivo_general').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')
    
    labels = [item.get('motivo_general', 'N/A') for item in datos]
    values = [item['cantidad'] for item in datos]
    
    return JsonResponse({
        'labels': labels,
        'data': values,
    })
