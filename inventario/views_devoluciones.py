"""
Vistas para la Fase 2.4: Devoluciones de Proveedores
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F, DecimalField
from django.utils import timezone
from datetime import datetime, timedelta

from .models import DevolucionProveedor, ItemDevolucion, Lote, Proveedor, Institucion
from .forms_devoluciones import DevolucionProveedorForm, ItemDevolucionForm, ItemDevolucionFormSet


# ============================================================
# DASHBOARD DE DEVOLUCIONES
# ============================================================

@login_required
def dashboard_devoluciones(request):
    """Dashboard de devoluciones de proveedores"""
    
    # Obtener institución del usuario a través del almacén
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    # Filtro base
    if institucion:
        devoluciones = DevolucionProveedor.objects.filter(institucion=institucion)
    else:
        devoluciones = DevolucionProveedor.objects.all()
    
    # Estadísticas
    total_devoluciones = devoluciones.count()
    pendientes = devoluciones.filter(estado='PENDIENTE').count()
    autorizadas = devoluciones.filter(estado='AUTORIZADA').count()
    completadas = devoluciones.filter(estado='COMPLETADA').count()
    canceladas = devoluciones.filter(estado='CANCELADA').count()
    
    # Monto total
    monto_total = devoluciones.aggregate(
        total=Sum(F('itemdevolucion__cantidad') * F('itemdevolucion__precio_unitario'), output_field=DecimalField())
    )['total'] or 0
    
    # Devoluciones recientes
    devoluciones_recientes = devoluciones.order_by('-fecha_creacion')[:10]
    
    # Devoluciones próximas a vencer (sin entregar en 30 días)
    fecha_limite = timezone.now() - timedelta(days=30)
    devoluciones_vencidas = devoluciones.filter(
        estado__in=['PENDIENTE', 'AUTORIZADA'],
        fecha_creacion__lt=fecha_limite
    ).count()
    
    # Proveedores con más devoluciones
    proveedores_devolucion = devoluciones.values('proveedor__razon_social').annotate(
        total=Sum(F('itemdevolucion__cantidad'), output_field=DecimalField())
    ).order_by('-total')[:5]
    
    context = {
        'total_devoluciones': total_devoluciones,
        'pendientes': pendientes,
        'autorizadas': autorizadas,
        'completadas': completadas,
        'canceladas': canceladas,
        'monto_total': monto_total,
        'devoluciones_recientes': devoluciones_recientes,
        'devoluciones_vencidas': devoluciones_vencidas,
        'proveedores_devolucion': proveedores_devolucion,
    }
    
    return render(request, 'inventario/devoluciones/dashboard_devoluciones.html', context)


# ============================================================
# LISTA DE DEVOLUCIONES
# ============================================================

@login_required
def lista_devoluciones(request):
    """Lista de devoluciones con filtros y búsqueda"""
    
    # Obtener institución del usuario a través del almacén
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    # Filtro base
    if institucion:
        devoluciones = DevolucionProveedor.objects.filter(institucion=institucion).select_related('proveedor')
    else:
        devoluciones = DevolucionProveedor.objects.all().select_related('proveedor')
    
    # Filtros
    filtro_estado = request.GET.get('estado', '')
    filtro_proveedor = request.GET.get('proveedor', '')
    busqueda_folio = request.GET.get('busqueda_folio', '')
    busqueda_proveedor = request.GET.get('busqueda_proveedor', '')
    busqueda_autorizacion = request.GET.get('busqueda_autorizacion', '')
    
    # Aplicar filtros
    if filtro_estado:
        devoluciones = devoluciones.filter(estado=filtro_estado)
    
    if filtro_proveedor:
        devoluciones = devoluciones.filter(proveedor_id=int(filtro_proveedor))
    
    # Búsquedas separadas
    if busqueda_folio:
        devoluciones = devoluciones.filter(folio__icontains=busqueda_folio)
    
    if busqueda_proveedor:
        devoluciones = devoluciones.filter(proveedor__razon_social__icontains=busqueda_proveedor)
    
    if busqueda_autorizacion:
        devoluciones = devoluciones.filter(numero_autorizacion__icontains=busqueda_autorizacion)
    
    # Ordenar
    devoluciones = devoluciones.order_by('-fecha_creacion')
    
    # Opciones para filtros
    proveedores = Proveedor.objects.filter(activo=True)
    estados = DevolucionProveedor.ESTADOS_CHOICES
    
    context = {
        'devoluciones': devoluciones,
        'proveedores': proveedores,
        'estados': estados,
        'filtro_estado': filtro_estado,
        'filtro_proveedor': filtro_proveedor,
        'busqueda_folio': busqueda_folio,
        'busqueda_proveedor': busqueda_proveedor,
        'busqueda_autorizacion': busqueda_autorizacion,
    }
    
    return render(request, 'inventario/devoluciones/lista_devoluciones.html', context)


# ============================================================
# CREAR DEVOLUCIÓN
# ============================================================

@login_required
def crear_devolucion(request):
    """Crear nueva devolución de proveedor"""
    
    # Obtener institución del usuario a través del almacén
    institucion = request.user.almacen.institucion if hasattr(request.user, 'almacen') and request.user.almacen else None
    
    # Validar que el usuario tenga institución asignada
    if not institucion:
        messages.error(request, 'No tienes una institución asignada. Contacta al administrador.')
        return redirect('devoluciones:lista_devoluciones')
    
    if request.method == 'POST':
        form = DevolucionProveedorForm(request.POST, institucion=institucion)
        formset = ItemDevolucionFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Crear devolución
            devolucion = form.save(commit=False)
            devolucion.institucion = institucion  # Asegurar que se asigna la institución
            devolucion.usuario_creacion = request.user
            devolucion.save()
            
            # Crear items
            for item_form in formset.forms:
                if item_form.cleaned_data:
                    item = item_form.save(commit=False)
                    item.devolucion = devolucion
                    item.save()
            
            messages.success(request, f'Devolución {devolucion.folio} creada exitosamente')
            return redirect('devoluciones:detalle_devolucion', devolucion_id=devolucion.id)
    else:
        form = DevolucionProveedorForm(institucion=institucion)
        formset = ItemDevolucionFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Crear Nueva Devolución',
    }
    
    return render(request, 'inventario/devoluciones/crear_devolucion.html', context)


# ============================================================
# DETALLE DE DEVOLUCIÓN
# ============================================================

@login_required
def detalle_devolucion(request, devolucion_id):
    """Detalle de una devolución específica"""
    
    devolucion = get_object_or_404(DevolucionProveedor, id=devolucion_id)
    items = devolucion.itemdevolucion_set.all().select_related('lote', 'lote__producto')
    
    # Verificar permisos
    if hasattr(request.user, 'institucion') and devolucion.institucion != request.user.institucion:
        messages.error(request, 'No tienes permiso para ver esta devolución')
        return redirect('devoluciones:lista_devoluciones')
    
    context = {
        'devolucion': devolucion,
        'items': items,
        'total_items': devolucion.total_items,
        'total_valor': devolucion.total_valor,
    }
    
    return render(request, 'inventario/devoluciones/detalle_devolucion.html', context)


# ============================================================
# AUTORIZAR DEVOLUCIÓN
# ============================================================

@login_required
def autorizar_devolucion(request, devolucion_id):
    """Autorizar una devolución"""
    
    devolucion = get_object_or_404(DevolucionProveedor, id=devolucion_id)
    
    # Verificar permisos
    if hasattr(request.user, 'institucion') and devolucion.institucion != request.user.institucion:
        messages.error(request, 'No tienes permiso para autorizar esta devolución')
        return redirect('devoluciones:lista_devoluciones')
    
    if devolucion.estado != 'PENDIENTE':
        messages.error(request, 'Solo se pueden autorizar devoluciones en estado PENDIENTE')
        return redirect('devoluciones:detalle_devolucion', devolucion_id=devolucion_id)
    
    if request.method == 'POST':
        numero_autorizacion = request.POST.get('numero_autorizacion', '')
        
        if not numero_autorizacion:
            messages.error(request, 'El número de autorización es requerido')
            return redirect('devoluciones:detalle_devolucion', devolucion_id=devolucion_id)
        
        devolucion.estado = 'AUTORIZADA'
        devolucion.numero_autorizacion = numero_autorizacion
        devolucion.fecha_autorizacion = timezone.now()
        devolucion.usuario_autorizo = request.user
        devolucion.save()
        
        messages.success(request, f'Devolución {devolucion.folio} autorizada exitosamente')
        return redirect('devoluciones:detalle_devolucion', devolucion_id=devolucion_id)
    
    context = {
        'devolucion': devolucion,
    }
    
    return render(request, 'inventario/devoluciones/autorizar_devolucion.html', context)


# ============================================================
# COMPLETAR DEVOLUCIÓN
# ============================================================

@login_required
def completar_devolucion(request, devolucion_id):
    """Completar una devolución (marcar como entregada)"""
    
    devolucion = get_object_or_404(DevolucionProveedor, id=devolucion_id)
    
    # Verificar permisos
    if hasattr(request.user, 'institucion') and devolucion.institucion != request.user.institucion:
        messages.error(request, 'No tienes permiso para completar esta devolución')
        return redirect('devoluciones:lista_devoluciones')
    
    if devolucion.estado != 'AUTORIZADA':
        messages.error(request, 'Solo se pueden completar devoluciones en estado AUTORIZADA')
        return redirect('devoluciones:detalle_devolucion', devolucion_id=devolucion_id)
    
    if request.method == 'POST':
        fecha_entrega = request.POST.get('fecha_entrega_real', '')
        numero_guia = request.POST.get('numero_guia', '')
        empresa_transporte = request.POST.get('empresa_transporte', '')
        numero_nota_credito = request.POST.get('numero_nota_credito', '')
        fecha_nota_credito = request.POST.get('fecha_nota_credito', '')
        
        try:
            devolucion.estado = 'COMPLETADA'
            devolucion.fecha_entrega_real = datetime.strptime(fecha_entrega, '%Y-%m-%d').date() if fecha_entrega else None
            devolucion.numero_guia = numero_guia
            devolucion.empresa_transporte = empresa_transporte
            devolucion.numero_nota_credito = numero_nota_credito
            devolucion.fecha_nota_credito = datetime.strptime(fecha_nota_credito, '%Y-%m-%d').date() if fecha_nota_credito else None
            devolucion.monto_nota_credito = devolucion.total_valor
            devolucion.save()
            
            messages.success(request, f'Devolución {devolucion.folio} completada exitosamente')
            return redirect('devoluciones:detalle_devolucion', devolucion_id=devolucion_id)
        except ValueError as e:
            messages.error(request, f'Error en los datos: {str(e)}')
    
    context = {
        'devolucion': devolucion,
    }
    
    return render(request, 'inventario/devoluciones/completar_devolucion.html', context)


# ============================================================
# CANCELAR DEVOLUCIÓN
# ============================================================

@login_required
def cancelar_devolucion(request, devolucion_id):
    """Cancelar una devolución"""
    
    devolucion = get_object_or_404(DevolucionProveedor, id=devolucion_id)
    
    # Verificar permisos
    if hasattr(request.user, 'institucion') and devolucion.institucion != request.user.institucion:
        messages.error(request, 'No tienes permiso para cancelar esta devolución')
        return redirect('devoluciones:lista_devoluciones')
    
    if devolucion.estado == 'CANCELADA':
        messages.error(request, 'Esta devolución ya está cancelada')
        return redirect('devoluciones:detalle_devolucion', devolucion_id=devolucion_id)
    
    if request.method == 'POST':
        motivo_cancelacion = request.POST.get('motivo_cancelacion', '')
        
        if not motivo_cancelacion:
            messages.error(request, 'El motivo de cancelación es requerido')
            return redirect('devoluciones:detalle_devolucion', devolucion_id=devolucion_id)
        
        devolucion.estado = 'CANCELADA'
        devolucion.descripcion = f"Cancelada: {motivo_cancelacion}"
        devolucion.save()
        
        messages.success(request, f'Devolución {devolucion.folio} cancelada exitosamente')
        return redirect('devoluciones:detalle_devolucion', devolucion_id=devolucion_id)
    
    context = {
        'devolucion': devolucion,
    }
    
    return render(request, 'inventario/devoluciones/cancelar_devolucion.html', context)
