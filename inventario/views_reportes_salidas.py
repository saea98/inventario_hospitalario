"""
Vistas para Reportes de Salidas y Análisis
Basados en MovimientoInventario generados por Fase 5
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F, DecimalField
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta, datetime
import json

from .models import (
    MovimientoInventario, Lote, Institucion, Almacen
)
from .decorators_roles import requiere_rol


# ============================================================
# REPORTE GENERAL DE SALIDAS
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Analista')
def reporte_general_salidas(request):
    """Reporte general de salidas basado en MovimientoInventario"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Consulta base: Movimientos de tipo SALIDA de la institución
    movimientos = MovimientoInventario.objects.filter(
        tipo_movimiento='SALIDA',
        lote__institucion=institucion
    )
    
    # Aplicar filtros de fecha
    if fecha_inicio:
        movimientos = movimientos.filter(fecha_movimiento__gte=fecha_inicio)
    if fecha_fin:
        movimientos = movimientos.filter(fecha_movimiento__lte=fecha_fin)
    
    # Estadísticas
    total_salidas = movimientos.count()
    total_cantidad = movimientos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    total_monto = movimientos.aggregate(
        total=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    )['total'] or 0
    
    # Salidas por almacén
    salidas_por_almacen = movimientos.values('lote__almacen__nombre').annotate(
        cantidad_movimientos=Count('id'),
        total_cantidad=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    ).order_by('-total_cantidad')
    
    # Top 10 productos más salidos
    top_productos = movimientos.values('lote__producto__descripcion').annotate(
        total_cantidad=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField()),
        cantidad_movimientos=Count('id')
    ).order_by('-total_cantidad')[:10]
    
    context = {
        'total_salidas': total_salidas,
        'total_cantidad': total_cantidad,
        'total_monto': total_monto,
        'promedio_cantidad': total_cantidad / total_salidas if total_salidas > 0 else 0,
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
    """Análisis de distribuciones basado en MovimientoInventario"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Consulta base
    movimientos = MovimientoInventario.objects.filter(
        tipo_movimiento='SALIDA',
        lote__institucion=institucion
    )
    
    # Aplicar filtros de fecha
    if fecha_inicio:
        movimientos = movimientos.filter(fecha_movimiento__gte=fecha_inicio)
    if fecha_fin:
        movimientos = movimientos.filter(fecha_movimiento__lte=fecha_fin)
    
    # Estadísticas
    total_movimientos = movimientos.count()
    total_cantidad = movimientos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    total_monto = movimientos.aggregate(
        total=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    )['total'] or 0
    
    # Distribuciones por almacén origen
    distribuciones_almacen = movimientos.values('lote__almacen__nombre').annotate(
        cantidad_movimientos=Count('id'),
        total_cantidad=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    ).order_by('-total_cantidad')
    
    # Análisis por motivo (propuesta)
    distribuciones_propuesta = movimientos.values('motivo').annotate(
        cantidad_movimientos=Count('id'),
        total_cantidad=Sum('cantidad'),
        total_monto=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    ).order_by('-total_cantidad')[:10]
    
    context = {
        'total_movimientos': total_movimientos,
        'total_cantidad': total_cantidad,
        'total_monto': total_monto,
        'distribuciones_almacen': distribuciones_almacen,
        'distribuciones_propuesta': distribuciones_propuesta,
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
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Últimos 30 días
    fecha_inicio = timezone.now() - timedelta(days=30)
    
    # Consulta base
    movimientos = MovimientoInventario.objects.filter(
        tipo_movimiento='SALIDA',
        lote__institucion=institucion,
        fecha_movimiento__gte=fecha_inicio
    )
    
    # Datos temporales por día
    datos_temporales = []
    for i in range(30, -1, -1):
        fecha = timezone.now() - timedelta(days=i)
        fecha_inicio_dia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_dia = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        movimientos_dia = movimientos.filter(
            fecha_movimiento__gte=fecha_inicio_dia,
            fecha_movimiento__lte=fecha_fin_dia
        )
        
        cantidad_movimientos = movimientos_dia.count()
        total_cantidad = movimientos_dia.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        total_monto = movimientos_dia.aggregate(
            total=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
        )['total'] or 0
        
        if cantidad_movimientos > 0:
            datos_temporales.append({
                'fecha': fecha.strftime('%d/%m/%Y'),
                'cantidad': cantidad_movimientos,
                'items': total_cantidad,
                'monto': float(total_monto) if total_monto else 0
            })
    
    # Estadísticas generales
    total_movimientos = movimientos.count()
    total_cantidad = movimientos.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    total_monto = movimientos.aggregate(
        total=Sum(F('cantidad') * F('lote__precio_unitario'), output_field=DecimalField())
    )['total'] or 0
    
    context = {
        'datos_temporales': datos_temporales,
        'total_movimientos': total_movimientos,
        'total_cantidad': total_cantidad,
        'total_monto': total_monto,
        'promedio_diario': total_movimientos / 30 if total_movimientos > 0 else 0,
    }
    
    return render(request, 'inventario/reportes_salidas/analisis_temporal.html', context)
