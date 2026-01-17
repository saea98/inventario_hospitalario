"""
VISTAS PARA FASE 2: Gestión Logística
Incluye: Citas, Traslados y Conteo Físico
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

from .models import (
    CitaProveedor, OrdenTraslado, ItemTraslado, 
    ConteoFisico, ItemConteoFisico, Folio, TipoEntrega,
    Lote, Almacen, Proveedor
)
from .forms import (
    CitaProveedorForm, OrdenTrasladoForm, LogisticaTrasladoForm
, CargaMasivaCitasForm)
from .servicios_notificaciones import notificaciones


# ============================================================================
# VISTAS PARA CITAS DE PROVEEDORES
# ============================================================================

@login_required
def lista_citas(request):
    """Lista todas las citas programadas"""
    citas = CitaProveedor.objects.all().order_by('-fecha_cita')
    
    # Filtros
    estado = request.GET.get('estado')
    proveedor = request.GET.get('proveedor')
    
    if estado:
        citas = citas.filter(estado=estado)
    
    if proveedor:
        citas = citas.filter(proveedor__razon_social__icontains=proveedor)
    
    # Contar por estado
    estados_count = {
        'programada': citas.filter(estado='programada').count(),
        'autorizada': citas.filter(estado='autorizada').count(),
        'completada': citas.filter(estado='completada').count(),
        'cancelada': citas.filter(estado='cancelada').count(),
    }
    
    context = {
        'citas': citas,
        'estados': CitaProveedor.ESTADOS_CITA,
        'estados_count': estados_count,
        'estado_seleccionado': estado,
        'proveedor_seleccionado': proveedor,
    }
    return render(request, 'inventario/citas/lista.html', context)


@login_required
def crear_cita(request):
    """Crear una nueva cita o cargar citas masivas"""
    
    # Determinar qué tipo de operación se está realizando
    tipo_operacion = request.POST.get('tipo_operacion', 'manual') if request.method == 'POST' else 'manual'
    
    if request.method == 'POST':
        if tipo_operacion == 'masiva':
            # Procesar carga masiva
            form_masiva = CargaMasivaCitasForm(request.POST, request.FILES)
            form_manual = CitaProveedorForm()
            
            if form_masiva.is_valid():
                try:
                    from .citas_masivas import CargaMasivaCitas
                    
                    archivo = request.FILES['archivo']
                    cargador = CargaMasivaCitas()
                    resultado = cargador.procesar_archivo(archivo)
                    
                    if resultado['exito']:
                        messages.success(
                            request,
                            f"✓ Carga completada: {resultado['citas_creadas']} citas creadas"
                        )
                        
                        if resultado['advertencias']:
                            for adv in resultado['advertencias'][:5]:  # Mostrar primeras 5
                                messages.warning(request, f"⚠️ {adv}")
                            if len(resultado['advertencias']) > 5:
                                messages.warning(request, f"⚠️ ...y {len(resultado['advertencias']) - 5} advertencias más")
                        
                        return redirect('logistica:lista_citas')
                    else:
                        for error in resultado['errores']:
                            messages.error(request, f"❌ {error}")
                        
                        for adv in resultado['advertencias'][:5]:
                            messages.warning(request, f"⚠️ {adv}")
                
                except Exception as e:
                    messages.error(request, f"Error al procesar archivo: {str(e)}")
            else:
                messages.error(request, "Verifica el archivo seleccionado")
        
        else:
            # Procesar captura manual
            form_manual = CitaProveedorForm(request.POST)
            form_masiva = CargaMasivaCitasForm()
            
            if form_manual.is_valid():
                cita = form_manual.save(commit=False)
                cita.usuario_creacion = request.user
                cita.save()
                
                # Enviar notificación
                notificaciones.notificar_cita_creada(cita)
                
                messages.success(request, f'✓ Cita creada exitosamente con {cita.proveedor.razon_social}')
                return redirect('logistica:lista_citas')
            else:
                messages.error(request, 'Error al crear la cita. Verifica los datos.')
    
    else:
        form_manual = CitaProveedorForm()
        form_masiva = CargaMasivaCitasForm()
    
    context = {
        'form_manual': form_manual,
        'form_masiva': form_masiva,
        'tipo_operacion': tipo_operacion,
    }
    return render(request, 'inventario/citas/crear.html', context)

@login_required
def editar_cita(request, pk):
    """Editar una cita existente"""
    cita = get_object_or_404(CitaProveedor, pk=pk)
    
    # Solo permitir editar si está en estado 'programada'
    if cita.estado != 'programada':
        messages.warning(request, f'No se puede editar una cita en estado {cita.get_estado_display()}')
        return redirect('logistica:lista_citas')
    
    if request.method == 'POST':
        form = CitaProveedorForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            messages.success(request, '✓ Cita actualizada exitosamente')
            return redirect('logistica:lista_citas')
    else:
        form = CitaProveedorForm(instance=cita)
    
    return render(request, 'inventario/citas/editar.html', {
        'form': form,
        'cita': cita
    })


@login_required
def detalle_cita(request, pk):
    """Ver detalles de una cita"""
    cita = get_object_or_404(CitaProveedor, pk=pk)
    
    context = {
        'cita': cita,
        'puede_autorizar': cita.estado == 'programada',
        'puede_completar': cita.estado == 'autorizada',
    }
    return render(request, 'inventario/citas/detalle.html', context)


@login_required
def autorizar_cita(request, pk):
    """Autorizar una cita (cambiar estado a 'autorizada')"""
    cita = get_object_or_404(CitaProveedor, pk=pk)
    
    if cita.estado != 'programada':
        messages.warning(request, f'Solo se pueden autorizar citas en estado "Programada"')
        return redirect('logistica:detalle_cita', pk=pk)
    
    if request.method == 'POST':
        cita.estado = 'autorizada'
        cita.fecha_autorizacion = timezone.now()
        cita.usuario_autorizacion = request.user
        cita.save()
        
        # Enviar notificación
        notificaciones.notificar_cita_autorizada(cita)
        
        messages.success(request, f'✓ Cita autorizada: {cita.proveedor.razon_social}')
        return redirect('logistica:detalle_cita', pk=pk)
    
    return render(request, 'inventario/citas/autorizar.html', {'cita': cita})


@login_required
def cancelar_cita(request, pk):
    """Cancelar una cita"""
    cita = get_object_or_404(CitaProveedor, pk=pk)
    
    if cita.estado == 'cancelada':
        messages.warning(request, 'Esta cita ya está cancelada')
        return redirect('logistica:lista_citas')
    
    if request.method == 'POST':
        cita.estado = 'cancelada'
        cita.save()
        
        # Enviar notificación
        notificaciones.notificar_cita_cancelada(cita)
        
        messages.success(request, f'✓ Cita cancelada')
        return redirect('logistica:lista_citas')
    
    return render(request, 'inventario/citas/cancelar.html', {'cita': cita})


# ============================================================================
# VISTAS PARA TRASLADOS
# ============================================================================

@login_required
def lista_traslados(request):
    """Lista todas las órdenes de traslado"""
    traslados = OrdenTraslado.objects.all().order_by('-fecha_creacion')
    
    # Filtros
    estado = request.GET.get('estado')
    almacen_origen = request.GET.get('almacen_origen')
    
    if estado:
        traslados = traslados.filter(estado=estado)
    
    if almacen_origen:
        traslados = traslados.filter(almacen_origen__id=almacen_origen)
    
    # Contar por estado
    estados_count = {
        'creada': traslados.filter(estado='creada').count(),
        'logistica_asignada': traslados.filter(estado='logistica_asignada').count(),
        'en_transito': traslados.filter(estado='en_transito').count(),
        'recibida': traslados.filter(estado='recibida').count(),
        'completada': traslados.filter(estado='completada').count(),
    }
    
    almacenes = Almacen.objects.all()
    
    context = {
        'traslados': traslados,
        'estados': OrdenTraslado.ESTADOS_TRASLADO,
        'almacenes': almacenes,
        'estados_count': estados_count,
        'estado_seleccionado': estado,
        'almacen_seleccionado': almacen_origen,
    }
    return render(request, 'inventario/traslados/lista.html', context)


@login_required
def crear_traslado(request):
    """Crear una nueva orden de traslado"""
    if request.method == 'POST':
        form = OrdenTrasladoForm(request.POST)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.usuario_creacion = request.user
            
            # Generar folio automáticamente
            try:
                tipo_entrega = TipoEntrega.objects.get(codigo='TRA')
                folio_obj = Folio.objects.get(tipo_entrega=tipo_entrega)
                orden.folio = folio_obj.generar_folio()
            except:
                orden.folio = f"TRA-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            orden.save()
            messages.success(request, f'✓ Orden de traslado creada: {orden.folio}')
            return redirect('detalle_traslado', pk=orden.pk)
    else:
        form = OrdenTrasladoForm()
    
    return render(request, 'inventario/traslados/crear.html', {'form': form})


@login_required
def detalle_traslado(request, pk):
    """Ver detalles de una orden de traslado"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    items = orden.items.all()
    
    context = {
        'orden': orden,
        'items': items,
        'puede_asignar_logistica': orden.estado == 'creada',
        'puede_iniciar_transito': orden.estado == 'logistica_asignada',
    }
    return render(request, 'inventario/traslados/detalle.html', context)


@login_required
def asignar_logistica_traslado(request, pk):
    """Asignar vehículo, chofer y ruta a una orden de traslado"""
    orden = get_object_or_404(OrdenTraslado, pk=pk)
    
    if orden.estado != 'creada':
        messages.warning(request, 'Solo se puede asignar logística a órdenes en estado "Creada"')
        return redirect('detalle_traslado', pk=pk)
    
    if request.method == 'POST':
        form = LogisticaTrasladoForm(request.POST, instance=orden)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.estado = 'logistica_asignada'
            orden.save()
            messages.success(request, '✓ Logística asignada exitosamente')
            return redirect('detalle_traslado', pk=orden.pk)
    else:
        form = LogisticaTrasladoForm(instance=orden)
    
    return render(request, 'inventario/traslados/asignar_logistica.html', {
        'form': form,
        'orden': orden
    })


# ============================================================================
# VISTAS PARA CONTEO FÍSICO
# ============================================================================

@login_required
def lista_conteos(request):
    """Lista todos los conteos físicos"""
    conteos = ConteoFisico.objects.all().order_by('-fecha_inicio')
    
    # Filtros
    estado = request.GET.get('estado')
    almacen = request.GET.get('almacen')
    
    if estado:
        conteos = conteos.filter(estado=estado)
    
    if almacen:
        conteos = conteos.filter(almacen__id=almacen)
    
    # Contar por estado
    estados_count = {
        'iniciado': conteos.filter(estado='iniciado').count(),
        'en_progreso': conteos.filter(estado='en_progreso').count(),
        'completado': conteos.filter(estado='completado').count(),
    }
    
    almacenes = Almacen.objects.all()
    
    context = {
        'conteos': conteos,
        'almacenes': almacenes,
        'estados_count': estados_count,
        'estado_seleccionado': estado,
        'almacen_seleccionado': almacen,
    }
    return render(request, 'inventario/conteo_fisico/lista.html', context)


@login_required
def iniciar_conteo(request):
    """Iniciar una nueva sesión de conteo físico"""
    if request.method == 'POST':
        almacen_id = request.POST.get('almacen')
        observaciones = request.POST.get('observaciones', '')
        
        try:
            almacen = Almacen.objects.get(pk=almacen_id)
            
            conteo = ConteoFisico.objects.create(
                almacen=almacen,
                observaciones=observaciones,
                usuario_creacion=request.user,
                estado='iniciado'
            )
            
            # Generar folio automáticamente
            try:
                tipo_entrega = TipoEntrega.objects.get(codigo='CNT')
                folio_obj = Folio.objects.get(tipo_entrega=tipo_entrega)
                conteo.folio = folio_obj.generar_folio()
                conteo.save()
            except:
                conteo.folio = f"CNT-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                conteo.save()
            
            messages.success(request, f'✓ Conteo iniciado: {conteo.folio}')
            return redirect('capturar_conteo', pk=conteo.pk)
        except Almacen.DoesNotExist:
            messages.error(request, 'Almacén no encontrado')
    
    almacenes = Almacen.objects.all()
    context = {'almacenes': almacenes}
    return render(request, 'inventario/conteo_fisico/iniciar.html', context)


@login_required
def capturar_conteo(request, pk):
    """Capturar datos de conteo físico"""
    conteo = get_object_or_404(ConteoFisico, pk=pk)
    items = conteo.items.all()
    
    # Obtener lotes disponibles del almacén
    lotes_disponibles = Lote.objects.filter(
        institucion__almacen=conteo.almacen,
        cantidad_disponible__gt=0
    ).order_by('numero_lote')
    
    context = {
        'conteo': conteo,
        'items': items,
        'lotes_disponibles': lotes_disponibles,
    }
    return render(request, 'inventario/conteo_fisico/capturar.html', context)


@login_required
def detalle_conteo(request, pk):
    """Ver detalles de un conteo físico"""
    conteo = get_object_or_404(ConteoFisico, pk=pk)
    items = conteo.items.all()
    
    # Calcular diferencias
    total_teorico = sum(item.cantidad_teorica for item in items)
    total_fisico = sum(item.cantidad_fisica for item in items)
    diferencia_total = total_fisico - total_teorico
    
    context = {
        'conteo': conteo,
        'items': items,
        'total_teorico': total_teorico,
        'total_fisico': total_fisico,
        'diferencia_total': diferencia_total,
    }
    return render(request, 'inventario/conteo_fisico/detalle.html', context)
