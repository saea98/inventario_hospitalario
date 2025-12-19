"""
Vistas para la Fase 4: Gestión de Salidas y Distribución de Existencias
Versión simplificada que coincide con la estructura real de la BD
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
    Lote, Almacen, Institucion, User
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
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    # Filtrar salidas por institución
    salidas = SalidaExistencias.objects.filter(institucion_destino=institucion).select_related(
        'almacen_origen', 'usuario_autoriza'
    )
    
    # Búsqueda
    busqueda = request.GET.get('busqueda')
    if busqueda:
        salidas = salidas.filter(
            Q(folio__icontains=busqueda) |
            Q(nombre_receptor__icontains=busqueda)
        )
    
    # Ordenamiento
    salidas = salidas.order_by('-fecha_salida')
    
    context = {
        'salidas': salidas,
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
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('lista_salidas')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Crear salida
                salida = SalidaExistencias(
                    institucion_destino=institucion,
                    almacen_origen_id=request.POST.get('almacen_origen'),
                    fecha_salida=timezone.now(),
                    nombre_receptor=request.POST.get('nombre_receptor'),
                    firma_receptor=request.POST.get('firma_receptor'),
                    solicitud_id=request.POST.get('solicitud'),
                    observaciones=request.POST.get('observaciones', ''),
                )
                salida.save()
                
                messages.success(request, f'Salida {salida.folio} creada exitosamente.')
                return redirect('detalle_salida', pk=salida.pk)
        
        except Exception as e:
            messages.error(request, f'Error al crear la salida: {str(e)}')
            return redirect('crear_salida')
    
    context = {
        'almacenes': Almacen.objects.filter(institucion=institucion),
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
        messages.error(request, 'No tienes permiso para ver esta salida.')
        return redirect('salidas:lista_salidas')
    
    # Obtener información relacionada
    items = ItemSalidaExistencias.objects.filter(salida=salida)
    distribuciones = DistribucionArea.objects.filter(salida=salida)
    
    context = {
        'salida': salida,
        'items': items,
        'distribuciones': distribuciones,
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
    
    if salida.institucion_destino != request.user.almacen.institucion:
        messages.error(request, 'No tienes acceso a esta salida.')
        return redirect('lista_salidas')
    
    if request.method == 'POST':
        try:
            salida.usuario_autoriza = request.user
            salida.save()
            
            messages.success(request, f'Salida {salida.folio} autorizada exitosamente.')
            return redirect('detalle_salida', pk=pk)
        
        except Exception as e:
            messages.error(request, f'Error al autorizar la salida: {str(e)}')
    
    return render(request, 'inventario/salidas/autorizar_salida.html', {'salida': salida})


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
                
                messages.success(request, 'Distribución creada exitosamente.')
                return redirect('detalle_salida', pk=pk)
        
        except Exception as e:
            messages.error(request, f'Error al distribuir: {str(e)}')
    
    context = {
        'salida': salida,
        'items': ItemSalidaExistencias.objects.filter(salida=salida),
    }
    
    return render(request, 'inventario/salidas/distribuir_salida.html', context)


# ============================================================
# DASHBOARD DE SALIDAS
# ============================================================

@login_required
@requiere_rol('Administrador', 'Gestor de Inventario')
def dashboard_salidas(request):
    """Dashboard con estadísticas de salidas"""
    
    institucion = request.user.almacen.institucion if request.user.almacen else None
    if not institucion:
        messages.error(request, 'No tienes una institución asignada.')
        return redirect('dashboard')
    
    salidas = SalidaExistencias.objects.filter(institucion_destino=institucion)
    
    # Estadísticas
    total_salidas = salidas.count()
    total_items = ItemSalidaExistencias.objects.filter(salida__institucion_destino=institucion).aggregate(
        total=Sum('cantidad')
    )['total'] or 0
    
    context = {
        'total_salidas': total_salidas,
        'total_items': total_items,
        'salidas_recientes': salidas.order_by('-fecha_salida')[:10],
    }
    
    return render(request, 'inventario/salidas/dashboard_salidas.html', context)
