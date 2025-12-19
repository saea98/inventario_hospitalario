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
    
    # Calcular monto total desde ItemDevolucion
    items_devoluciones = ItemDevolucion.objects.filter(devolucion__in=devoluciones)
    total_items = items_devoluciones.aggregate(total=Sum('cantidad'))['total'] or 0
    
    # Calcular monto total como suma de subtotales (cantidad * precio_unitario)
    total_monto = Decimal('0.00')
    for item in items_devoluciones:
        total_monto += item.cantidad * item.precio_unitario
    
    # Por estado - calcular monto desde items
    por_estado_list = []
    for estado_choice in DevolucionProveedor.ESTADOS_CHOICES:
        estado_value = estado_choice[0]
        devs_estado = devoluciones.filter(estado=estado_value)
        cantidad = devs_estado.count()
        items_estado = ItemDevolucion.objects.filter(devolucion__in=devs_estado)
        monto_estado = Decimal('0.00')
        for item in items_estado:
            monto_estado += item.cantidad * item.precio_unitario
        
        if cantidad > 0 or monto_estado > 0:
            por_estado_list.append({
                'estado': estado_value,
                'get_estado_display': dict(DevolucionProveedor.ESTADOS_CHOICES)[estado_value],
                'cantidad': cantidad,
                'monto': monto_estado
            })
    
    por_estado = por_estado_list
    
    # Promedio por devolución
    promedio_monto = total_monto / total_devoluciones if total_devoluciones > 0 else Decimal('0.00')
    promedio_items = total_items / total_devoluciones if total_devoluciones > 0 else 0
    
    # Proveedores
    proveedores = Proveedor.objects.all().order_by('razon_social')
    
    # Últimas devoluciones con monto calculado
    devoluciones_lista = devoluciones.order_by('-fecha_creacion')[:20]
    for dev in devoluciones_lista:
        items = ItemDevolucion.objects.filter(devolucion=dev)
        dev.total_valor = sum(item.cantidad * item.precio_unitario for item in items)
        dev.total_items = sum(item.cantidad for item in items)
    
    context = {
        'total_devoluciones': total_devoluciones,
        'total_monto': total_monto,
        'total_items': total_items,
        'promedio_monto': promedio_monto,
        'promedio_items': promedio_items,
        'por_estado': por_estado,
        'devoluciones': devoluciones_lista,
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
    
    # Análisis por proveedor
    analisis_proveedores_list = []
    for proveedor in Proveedor.objects.all():
        devs_proveedor = devoluciones.filter(proveedor=proveedor)
        items_proveedor = ItemDevolucion.objects.filter(devolucion__in=devs_proveedor)
        
        total_dev = devs_proveedor.count()
        total_items = items_proveedor.aggregate(total=Sum('cantidad'))['total'] or 0
        total_monto = sum(item.cantidad * item.precio_unitario for item in items_proveedor)
        
        if total_dev > 0:
            analisis_proveedores_list.append({
                'proveedor__razon_social': proveedor.razon_social,
                'total_devoluciones': total_dev,
                'monto_total': total_monto,
                'items_total': total_items,
                'monto_promedio': total_monto / total_dev if total_dev > 0 else Decimal('0.00'),
                'pendientes': devs_proveedor.filter(estado='PENDIENTE').count(),
                'autorizadas': devs_proveedor.filter(estado='AUTORIZADA').count(),
                'completadas': devs_proveedor.filter(estado='COMPLETADA').count(),
                'canceladas': devs_proveedor.filter(estado='CANCELADA').count(),
            })
    
    # Ordenar por total de devoluciones
    analisis_proveedores_list.sort(key=lambda x: x['total_devoluciones'], reverse=True)
    
    # Motivos más frecuentes
    motivos_frecuentes = []
    motivos_dict = {}
    for item in ItemDevolucion.objects.filter(devolucion__in=devoluciones):
        motivo = item.devolucion.motivo_general
        if motivo not in motivos_dict:
            motivos_dict[motivo] = {'cantidad': 0, 'monto': Decimal('0.00')}
        motivos_dict[motivo]['cantidad'] += 1
        motivos_dict[motivo]['monto'] += item.cantidad * item.precio_unitario
    
    for motivo, data in sorted(motivos_dict.items(), key=lambda x: x[1]['cantidad'], reverse=True):
        motivos_frecuentes.append({
            'motivo_general': dict(DevolucionProveedor.MOTIVOS_CHOICES).get(motivo, motivo),
            'cantidad': data['cantidad'],
            'monto': data['monto']
        })
    
    total_devoluciones = devoluciones.count()
    total_proveedores = len(analisis_proveedores_list)
    
    # Filtrar solo proveedores que tienen devoluciones
    proveedores_con_devoluciones = [ap['proveedor__razon_social'] for ap in analisis_proveedores_list]
    
    context = {
        'analisis_proveedores': analisis_proveedores_list,
        'motivos_frecuentes': motivos_frecuentes,
        'total_devoluciones': total_devoluciones,
        'total_proveedores': len(proveedores_con_devoluciones),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'inventario/reportes/analisis_proveedores.html', context)


# ============================================================
# ANÁLISIS TEMPORAL
# ============================================================

@login_required
def analisis_temporal(request):
    """Análisis temporal de devoluciones"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        messages.error(request, 'No tienes una institución asignada')
        return redirect('devoluciones:lista_devoluciones')
    
    # Tipo de período
    tipo_periodo = request.GET.get('tipo_periodo', 'mes')
    
    # Query base
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    # Tendencia por período
    tendencia_list = []
    if tipo_periodo == 'mes':
        # Últimos 12 meses
        for i in range(11, -1, -1):
            fecha_mes = timezone.now() - timedelta(days=30*i)
            mes_inicio = fecha_mes.replace(day=1)
            if i > 0:
                mes_fin = (fecha_mes - timedelta(days=30*(i-1))).replace(day=1)
            else:
                mes_fin = timezone.now() + timedelta(days=30)
            
            devs_mes = devoluciones.filter(fecha_creacion__gte=mes_inicio, fecha_creacion__lt=mes_fin)
            items_mes = ItemDevolucion.objects.filter(devolucion__in=devs_mes)
            
            cantidad = devs_mes.count()
            monto = sum(item.cantidad * item.precio_unitario for item in items_mes)
            items_total = items_mes.aggregate(total=Sum('cantidad'))['total'] or 0
            
            tendencia_list.append({
                'periodo': mes_inicio,
                'cantidad': cantidad,
                'monto': monto,
                'items': items_total,
            })
    else:
        # Por año
        for i in range(4, -1, -1):
            año = timezone.now().year - i
            año_inicio = datetime(año, 1, 1)
            año_fin = datetime(año + 1, 1, 1)
            
            devs_año = devoluciones.filter(fecha_creacion__gte=año_inicio, fecha_creacion__lt=año_fin)
            items_año = ItemDevolucion.objects.filter(devolucion__in=devs_año)
            
            cantidad = devs_año.count()
            monto = sum(item.cantidad * item.precio_unitario for item in items_año)
            items_total = items_año.aggregate(total=Sum('cantidad'))['total'] or 0
            
            tendencia_list.append({
                'periodo': año_inicio,
                'cantidad': cantidad,
                'monto': monto,
                'items': items_total,
            })
    
    # Tiempo promedio de autorización
    devoluciones_autorizadas = devoluciones.filter(fecha_autorizacion__isnull=False)
    tiempo_promedio_autorizacion = None
    if devoluciones_autorizadas.exists():
        total_dias = Decimal('0')
        for dev in devoluciones_autorizadas:
            if dev.fecha_autorizacion:
                dias = (dev.fecha_autorizacion - dev.fecha_creacion).days
                total_dias += dias
        tiempo_promedio_autorizacion = float(total_dias) / devoluciones_autorizadas.count() if devoluciones_autorizadas.count() > 0 else 0
    
    # Tiempo promedio de entrega
    devoluciones_completadas = devoluciones.filter(fecha_entrega_real__isnull=False)
    tiempo_promedio_entrega = None
    if devoluciones_completadas.exists():
        total_dias = Decimal('0')
        for dev in devoluciones_completadas:
            if dev.fecha_entrega_real:
                dias = (dev.fecha_entrega_real - dev.fecha_creacion.date()).days
                total_dias += dias
        tiempo_promedio_entrega = float(total_dias) / devoluciones_completadas.count() if devoluciones_completadas.count() > 0 else 0
    
    context = {
        'tendencia': tendencia_list,
        'tiempo_promedio_autorizacion': tiempo_promedio_autorizacion,
        'tiempo_promedio_entrega': tiempo_promedio_entrega,
        'tipo_periodo': tipo_periodo,
    }
    
    return render(request, 'inventario/reportes/analisis_temporal.html', context)


# ============================================================
# APIs PARA GRÁFICOS
# ============================================================

@login_required
def api_grafico_estado(request):
    """API para gráfico de estados"""
    
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        return JsonResponse({'error': 'No institution'}, status=403)
    
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    data = {
        'labels': ['Pendiente', 'Autorizada', 'Completada', 'Cancelada'],
        'data': [
            devoluciones.filter(estado='PENDIENTE').count(),
            devoluciones.filter(estado='AUTORIZADA').count(),
            devoluciones.filter(estado='COMPLETADA').count(),
            devoluciones.filter(estado='CANCELADA').count(),
        ],
        'colors': ['#FFC107', '#17A2B8', '#28A745', '#6C757D']
    }
    
    return JsonResponse(data)


@login_required
def api_grafico_proveedores(request):
    """API para gráfico de proveedores"""
    
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        return JsonResponse({'error': 'No institution'}, status=403)
    
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    # Top 10 proveedores
    proveedores_count = {}
    for dev in devoluciones:
        prov_name = dev.proveedor.razon_social
        proveedores_count[prov_name] = proveedores_count.get(prov_name, 0) + 1
    
    # Ordenar y tomar top 10
    sorted_proveedores = sorted(proveedores_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    data = {
        'labels': [prov[0] for prov in sorted_proveedores],
        'data': [prov[1] for prov in sorted_proveedores]
    }
    
    return JsonResponse(data)


@login_required
def api_grafico_tendencia(request):
    """API para gráfico de tendencia"""
    
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        return JsonResponse({'error': 'No institution'}, status=403)
    
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    # Últimos 12 meses
    labels = []
    data_cantidad = []
    data_monto = []
    
    for i in range(11, -1, -1):
        fecha_mes = timezone.now() - timedelta(days=30*i)
        mes_inicio = fecha_mes.replace(day=1)
        if i > 0:
            mes_fin = (fecha_mes - timedelta(days=30*(i-1))).replace(day=1)
        else:
            mes_fin = timezone.now() + timedelta(days=30)
        
        devs_mes = devoluciones.filter(fecha_creacion__gte=mes_inicio, fecha_creacion__lt=mes_fin)
        items_mes = ItemDevolucion.objects.filter(devolucion__in=devs_mes)
        
        cantidad = devs_mes.count()
        monto = sum(item.cantidad * item.precio_unitario for item in items_mes)
        
        labels.append(mes_inicio.strftime('%b %Y'))
        data_cantidad.append(cantidad)
        data_monto.append(float(monto))
    
    data = {
        'labels': labels,
        'data_cantidad': data_cantidad,
        'data_monto': data_monto
    }
    
    return JsonResponse(data)


@login_required
def api_grafico_motivos(request):
    """API para gráfico de motivos"""
    
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    if not institucion:
        return JsonResponse({'error': 'No institution'}, status=403)
    
    devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    
    # Contar motivos
    motivos_count = {}
    for dev in devoluciones:
        motivo = dict(DevolucionProveedor.MOTIVOS_CHOICES).get(dev.motivo_general, dev.motivo_general)
        motivos_count[motivo] = motivos_count.get(motivo, 0) + 1
    
    # Ordenar
    sorted_motivos = sorted(motivos_count.items(), key=lambda x: x[1], reverse=True)
    
    data = {
        'labels': [motivo[0] for motivo in sorted_motivos],
        'data': [motivo[1] for motivo in sorted_motivos]
    }
    
    return JsonResponse(data)
