"""
Vistas para Reportes de Salidas y Análisis
Basados en datos existentes del módulo de Pedidos/Solicitudes
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F, DecimalField
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    SalidaExistencias, ItemSalidaExistencias, Institucion, Almacen
)
from .decorators_roles import requiere_rol


# ============================================================
# REPORTE GENERAL DE SALIDAS
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista')
def reporte_general_salidas(request):
    """Reporte general de salidas con estadísticas"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Consulta base
    salidas = SalidaExistencias.objects.filter(institucion_destino=institucion)
    
    # Aplicar filtros de fecha
    if fecha_inicio:
        salidas = salidas.filter(fecha_salida__gte=fecha_inicio)
    if fecha_fin:
        salidas = salidas.filter(fecha_salida__lte=fecha_fin)
    
    # Estadísticas
    total_salidas = salidas.count()
    
    # Total de items y monto
    items_stats = ItemSalidaExistencias.objects.filter(
        salida__institucion_destino=institucion
    ).aggregate(
        total_items=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('precio_unitario'), output_field=DecimalField())
    )
    
    total_items = items_stats['total_items'] or 0
    total_monto = items_stats['total_monto'] or 0
    
    # Salidas por almacén
    salidas_por_almacen = salidas.values('almacen_origen__nombre').annotate(
        cantidad=Count('id'),
        items=Sum(F('itemsalidaexistencias_set__cantidad'), output_field=DecimalField())
    ).order_by('-cantidad')
    
    # Top 10 productos más salidos
    top_productos = ItemSalidaExistencias.objects.filter(
        salida__institucion_destino=institucion
    ).values('lote__producto__descripcion').annotate(
        total_cantidad=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('precio_unitario'), output_field=DecimalField())
    ).order_by('-total_cantidad')[:10]
    
    context = {
        'total_salidas': total_salidas,
        'total_items': total_items,
        'total_monto': total_monto,
        'promedio_items': total_items / total_salidas if total_salidas > 0 else 0,
        'salidas_por_almacen': salidas_por_almacen,
        'top_productos': top_productos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'inventario/reportes_salidas/reporte_general.html', context)


# ============================================================
# ANÁLISIS DE DISTRIBUCIONES
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista')
def analisis_distribuciones(request):
    """Análisis de distribuciones a áreas"""
    
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Estadísticas de distribuciones
    distribuciones = SalidaExistencias.objects.filter(
        institucion_destino=institucion
    ).prefetch_related('distribuciones')
    
    if fecha_inicio:
        distribuciones = distribuciones.filter(fecha_salida__gte=fecha_inicio)
    if fecha_fin:
        distribuciones = distribuciones.filter(fecha_salida__lte=fecha_fin)
    
    # Contar distribuciones por estado
    dist_por_estado = {}
    total_dist = 0
    
    for salida in distribuciones:
        for dist in salida.distribuciones.all():
            estado = dist.get_estado_display() if hasattr(dist, 'get_estado_display') else dist.estado
            if estado not in dist_por_estado:
                dist_por_estado[estado] = 0
            dist_por_estado[estado] += 1
            total_dist += 1
    
    # Distribuciones por área
    areas = {}
    for salida in distribuciones:
        for dist in salida.distribuciones.all():
            area = dist.area_destino
            if area not in areas:
                areas[area] = {'cantidad': 0, 'items': 0}
            areas[area]['cantidad'] += 1
            areas[area]['items'] += dist.total_items
    
    context = {
        'total_distribuciones': total_dist,
        'dist_por_estado': dist_por_estado,
        'areas': areas,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'inventario/reportes_salidas/analisis_distribuciones.html', context)


# ============================================================
# ANÁLISIS TEMPORAL
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista')
def analisis_temporal(request):
    """Análisis temporal de salidas (últimos 30 días)"""
    
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Últimos 30 días
    fecha_inicio = timezone.now() - timedelta(days=30)
    
    salidas = SalidaExistencias.objects.filter(
        institucion_destino=institucion,
        fecha_salida__gte=fecha_inicio
    ).order_by('fecha_salida')
    
    # Agrupar por día
    salidas_por_dia = {}
    for salida in salidas:
        fecha = salida.fecha_salida.date()
        if fecha not in salidas_por_dia:
            salidas_por_dia[fecha] = {'cantidad': 0, 'items': 0, 'monto': 0}
        salidas_por_dia[fecha]['cantidad'] += 1
        
        # Sumar items y monto
        items_info = ItemSalidaExistencias.objects.filter(salida=salida).aggregate(
            total_items=Sum('cantidad'),
            total_monto=Sum(F('cantidad') * F('precio_unitario'), output_field=DecimalField())
        )
        salidas_por_dia[fecha]['items'] += items_info['total_items'] or 0
        salidas_por_dia[fecha]['monto'] += items_info['total_monto'] or 0
    
    # Convertir a lista ordenada
    datos_temporales = [
        {
            'fecha': fecha,
            'cantidad': datos['cantidad'],
            'items': datos['items'],
            'monto': float(datos['monto']) if datos['monto'] else 0
        }
        for fecha, datos in sorted(salidas_por_dia.items())
    ]
    
    context = {
        'datos_temporales': datos_temporales,
        'fecha_inicio': fecha_inicio.date(),
        'fecha_fin': timezone.now().date(),
    }
    
    return render(request, 'inventario/reportes_salidas/analisis_temporal.html', context)
