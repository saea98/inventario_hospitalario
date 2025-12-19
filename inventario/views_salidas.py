"""
Vistas para la Fase 4: Gestión de Salidas y Distribución de Existencias
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum, F, DecimalField, Q
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
import json

from .models import (
    SalidaExistencias, ItemSalidaExistencias, DistribucionArea, ItemDistribucion,
    Lote, Almacen, Institucion, TipoEntrega, User
)
from .decorators_roles import requiere_rol


# ============================================================
# LISTA DE SALIDAS
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Almacenista')
def lista_salidas(request):
    """Lista todas las salidas de existencias"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion_destino if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtrar salidas por institución
    salidas = SalidaExistencias.objects.filter(institucion_destino=institucion).select_related(
        'almacen', 'tipo_entrega', 'usuario_creacion'
    )
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        salidas = salidas.filter(estado=estado)
    
    almacen = request.GET.get('almacen')
    if almacen:
        salidas = salidas.filter(almacen_id=almacen)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda')
    if busqueda:
        salidas = salidas.filter(
            Q(folio__icontains=busqueda) |
            Q(numero_autorizacion__icontains=busqueda) |
            Q(responsable_salida__icontains=busqueda)
        )
    
    # Ordenamiento
    salidas = salidas.order_by('-fecha_creacion')
    
    context = {
        'salidas': salidas,
        'estados': SalidaExistencias.ESTADOS_SALIDA,
        'almacenes': Almacen.objects.filter(institucion_destino=institucion),
        'estado_filtro': estado,
        'almacen_filtro': almacen,
        'busqueda': busqueda,
    }
    
    return render(request, 'inventario/salidas/lista_salidas.html', context)


# ============================================================
# CREAR SALIDA
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Almacenista')
@require_http_methods(["GET", "POST"])
def crear_salida(request):
    """Crear una nueva salida de existencias"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion_destino if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('lista_salidas')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear salida
                salida = SalidaExistencias(
                    institucion_destino=institucion,
                    almacen_id=request.POST.get('almacen'),
                    tipo_entrega_id=request.POST.get('tipo_entrega'),
                    fecha_salida_estimada=request.POST.get('fecha_salida_estimada'),
                    responsable_salida=request.POST.get('responsable_salida'),
                    telefono_responsable=request.POST.get('telefono_responsable'),
                    email_responsable=request.POST.get('email_responsable'),
                    observaciones=request.POST.get('observaciones'),
                    usuario_creacion=request.user,
                )
                salida.save()
                
                # Procesar items
                items_json = request.POST.get('items_json', '[]')
                items = json.loads(items_json)
                
                if not items:
                    messages.error(request, 'Debes agregar al menos un item.')
                    salida.delete()
                    return redirect('crear_salida')
                
                for item in items:
                    lote = Lote.objects.get(id=item['lote_id'])
                    ItemSalidaExistencias.objects.create(
                        salida=salida,
                        lote=lote,
                        cantidad=item['cantidad'],
                        precio_unitario=Decimal(item['precio_unitario']),
                        observaciones=item.get('observaciones', '')
                    )
                
                messages.success(request, f'Salida {salida.folio} creada exitosamente.')
                return redirect('detalle_salida', pk=salida.pk)
        
        except Exception as e:
            messages.error(request, f'Error al crear la salida: {str(e)}')
            return redirect('crear_salida')
    
    context = {
        'almacenes': Almacen.objects.filter(institucion_destino=institucion),
        'tipos_entrega': TipoEntrega.objects.filter(activo=True),
        'lotes': Lote.objects.filter(almacen__institucion_destino=institucion, activo=True),
    }
    
    return render(request, 'inventario/salidas/crear_salida.html', context)


# ============================================================
# DETALLE DE SALIDA
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Almacenista')
def detalle_salida(request, pk):
    """Mostrar detalle de una salida"""
    
    salida = get_object_or_404(SalidaExistencias, pk=pk)
    
    # Verificar que el usuario tenga acceso
    if salida.institucion_destino != request.user.almacen.institucion:
        messages.error(request, 'No tienes acceso a esta salida.')
        return redirect('lista_salidas')
    
    items = salida.itemsalidaexistencias_set.all().select_related('lote')
    distribuciones = salida.distribuciones.all()
    
    context = {
        'salida': salida,
        'items': items,
        'distribuciones': distribuciones,
        'total_items': salida.total_items,
        'total_valor': salida.total_valor,
    }
    
    return render(request, 'inventario/salidas/detalle_salida.html', context)


# ============================================================
# AUTORIZAR SALIDA
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario')
@require_http_methods(["GET", "POST"])
def autorizar_salida(request, pk):
    """Autorizar una salida de existencias"""
    
    salida = get_object_or_404(SalidaExistencias, pk=pk)
    
    # Verificar que el usuario tenga acceso
    if salida.institucion_destino != request.user.almacen.institucion:
        messages.error(request, 'No tienes acceso a esta salida.')
        return redirect('lista_salidas')
    
    if salida.estado != 'PENDIENTE':
        messages.error(request, 'Solo se pueden autorizar salidas en estado PENDIENTE.')
        return redirect('detalle_salida', pk=pk)
    
    if request.method == 'POST':
        try:
            salida.estado = 'AUTORIZADA'
            salida.numero_autorizacion = request.POST.get('numero_autorizacion')
            salida.fecha_autorizacion = timezone.now()
            salida.usuario_autorizo = request.user
            salida.save()
            
            messages.success(request, f'Salida {salida.folio} autorizada exitosamente.')
            return redirect('detalle_salida', pk=pk)
        
        except Exception as e:
            messages.error(request, f'Error al autorizar la salida: {str(e)}')
    
    return render(request, 'inventario/salidas/autorizar_salida.html', {'salida': salida})


# ============================================================
# CANCELAR SALIDA
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario')
@require_http_methods(["GET", "POST"])
def cancelar_salida(request, pk):
    """Cancelar una salida de existencias"""
    
    salida = get_object_or_404(SalidaExistencias, pk=pk)
    
    # Verificar que el usuario tenga acceso
    if salida.institucion_destino != request.user.almacen.institucion:
        messages.error(request, 'No tienes acceso a esta salida.')
        return redirect('lista_salidas')
    
    if salida.estado == 'CANCELADA':
        messages.error(request, 'Esta salida ya está cancelada.')
        return redirect('detalle_salida', pk=pk)
    
    if request.method == 'POST':
        try:
            salida.estado = 'CANCELADA'
            salida.observaciones = request.POST.get('motivo_cancelacion', '')
            salida.save()
            
            messages.success(request, f'Salida {salida.folio} cancelada exitosamente.')
            return redirect('detalle_salida', pk=pk)
        
        except Exception as e:
            messages.error(request, f'Error al cancelar la salida: {str(e)}')
    
    return render(request, 'inventario/salidas/cancelar_salida.html', {'salida': salida})


# ============================================================
# DISTRIBUIR A ÁREAS
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario', 'Almacenista')
@require_http_methods(["GET", "POST"])
def distribuir_salida(request, pk):
    """Distribuir una salida a diferentes áreas"""
    
    salida = get_object_or_404(SalidaExistencias, pk=pk)
    
    # Verificar que el usuario tenga acceso
    if salida.institucion_destino != request.user.almacen.institucion:
        messages.error(request, 'No tienes acceso a esta salida.')
        return redirect('lista_salidas')
    
    if salida.estado != 'AUTORIZADA':
        messages.error(request, 'Solo se pueden distribuir salidas autorizadas.')
        return redirect('detalle_salida', pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear distribución
                distribucion = DistribucionArea(
                    salida=salida,
                    area_destino=request.POST.get('area_destino'),
                    responsable_area=request.POST.get('responsable_area'),
                    telefono_responsable=request.POST.get('telefono_responsable'),
                    email_responsable=request.POST.get('email_responsable'),
                    fecha_entrega_estimada=request.POST.get('fecha_entrega_estimada'),
                    usuario_creacion=request.user,
                )
                distribucion.save()
                
                # Procesar items distribuidos
                items_json = request.POST.get('items_json', '[]')
                items = json.loads(items_json)
                
                if not items:
                    messages.error(request, 'Debes agregar al menos un item a distribuir.')
                    distribucion.delete()
                    return redirect('distribuir_salida', pk=pk)
                
                for item in items:
                    item_salida = ItemSalidaExistencias.objects.get(id=item['item_salida_id'])
                    ItemDistribucion.objects.create(
                        distribucion=distribucion,
                        item_salida=item_salida,
                        cantidad=item['cantidad'],
                        precio_unitario=item_salida.precio_unitario,
                        observaciones=item.get('observaciones', '')
                    )
                
                messages.success(request, f'Distribución a {distribucion.area_destino} creada exitosamente.')
                return redirect('detalle_salida', pk=pk)
        
        except Exception as e:
            messages.error(request, f'Error al crear la distribución: {str(e)}')
            return redirect('distribuir_salida', pk=pk)
    
    items = salida.itemsalidaexistencias_set.all()
    
    context = {
        'salida': salida,
        'items': items,
    }
    
    return render(request, 'inventario/salidas/distribuir_salida.html', context)


# ============================================================
# DASHBOARD DE SALIDAS
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario')
def dashboard_salidas(request):
    """Dashboard con estadísticas de salidas"""
    
    # Obtener institución del usuario
    institucion = request.user.almacen.institucion_destino if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Estadísticas generales
    salidas = SalidaExistencias.objects.filter(institucion_destino=institucion)
    
    total_salidas = salidas.count()
    salidas_pendientes = salidas.filter(estado='PENDIENTE').count()
    salidas_autorizadas = salidas.filter(estado='AUTORIZADA').count()
    salidas_completadas = salidas.filter(estado='COMPLETADA').count()
    
    # Montos
    total_monto = salidas.aggregate(
        total=Sum(F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'), 
                 output_field=DecimalField())
    )['total'] or Decimal('0.00')
    
    # Últimas salidas
    ultimas_salidas = salidas.order_by('-fecha_creacion')[:10]
    
    # Salidas por almacén
    salidas_por_almacen = salidas.values('almacen__nombre').annotate(
        cantidad=Sum('itemsalidaexistencias__cantidad'),
        monto=Sum(F('itemsalidaexistencias__cantidad') * F('itemsalidaexistencias__precio_unitario'), 
                 output_field=DecimalField())
    )
    
    context = {
        'total_salidas': total_salidas,
        'salidas_pendientes': salidas_pendientes,
        'salidas_autorizadas': salidas_autorizadas,
        'salidas_completadas': salidas_completadas,
        'total_monto': total_monto,
        'ultimas_salidas': ultimas_salidas,
        'salidas_por_almacen': list(salidas_por_almacen),
    }
    
    return render(request, 'inventario/salidas/dashboard_salidas.html', context)


# ============================================================
# APIs PARA GRÁFICOS
# ============================================================

@login_required
@require_http_methods(["GET"])
def api_grafico_estados(request):
    """API para gráfico de salidas por estado"""
    
    institucion = request.user.almacen.institucion_destino if request.user.almacen else None
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    salidas = SalidaExistencias.objects.filter(institucion_destino=institucion)
    
    datos = {
        'PENDIENTE': salidas.filter(estado='PENDIENTE').count(),
        'AUTORIZADA': salidas.filter(estado='AUTORIZADA').count(),
        'COMPLETADA': salidas.filter(estado='COMPLETADA').count(),
        'CANCELADA': salidas.filter(estado='CANCELADA').count(),
    }
    
    return JsonResponse({
        'labels': list(datos.keys()),
        'data': list(datos.values()),
        'colors': ['#FFC107', '#17A2B8', '#28A745', '#DC3545']
    })


@login_required
@require_http_methods(["GET"])
def api_grafico_almacenes(request):
    """API para gráfico de salidas por almacén"""
    
    institucion = request.user.almacen.institucion_destino if request.user.almacen else None
    if not institucion:
        return JsonResponse({'error': 'No tienes institución asignada'}, status=400)
    
    salidas = SalidaExistencias.objects.filter(institucion_destino=institucion)
    
    datos = salidas.values('almacen__nombre').annotate(
        cantidad=Sum('itemsalidaexistencias__cantidad')
    ).order_by('-cantidad')[:10]
    
    labels = [d['almacen__nombre'] for d in datos]
    values = [d['cantidad'] or 0 for d in datos]
    
    return JsonResponse({
        'labels': labels,
        'data': values,
    })
