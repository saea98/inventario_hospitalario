from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime

from .models import ConteoFisico, ItemConteoFisico, Lote, Producto, MovimientoInventario, UbicacionAlmacen, LoteUbicacion
from .forms import ConteoFisicoForm
from .servicios_notificaciones import notificaciones


@login_required
def lista_conteos(request):
    """Listar todos los conteos físicos"""
    conteos = ConteoFisico.objects.all().order_by('-fecha_creacion')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        conteos = conteos.filter(estado=estado)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda')
    if busqueda:
        conteos = conteos.filter(folio__icontains=busqueda)
    
    # Estadísticas
    estadisticas = {
        'total': ConteoFisico.objects.count(),
        'en_progreso': ConteoFisico.objects.filter(estado='en_progreso').count(),
        'completados': ConteoFisico.objects.filter(estado='completado').count(),
        'cancelados': ConteoFisico.objects.filter(estado='cancelado').count(),
    }
    
    return render(request, 'inventario/conteo_fisico/lista.html', {
        'conteos': conteos,
        'estadisticas': estadisticas,
        'estado_filtro': estado,
        'busqueda': busqueda,
    })


@login_required
def crear_conteo(request):
    """Crear un nuevo conteo físico"""
    if request.method == 'POST':
        form = ConteoFisicoForm(request.POST)
        if form.is_valid():
            conteo = form.save(commit=False)
            conteo.usuario_creacion = request.user
            conteo.estado = 'creado'
            conteo.save()
            
            # Generar folio
            conteo.folio = f"CF-{conteo.id:06d}"
            conteo.save()
            
            messages.success(request, f'Conteo físico {conteo.folio} creado exitosamente')
            return redirect('logistica:detalle_conteo', pk=conteo.id)
    else:
        form = ConteoFisicoForm()
    
    return render(request, 'inventario/conteo_fisico/crear.html', {'form': form})


@login_required
def detalle_conteo(request, pk):
    """Ver detalles de un conteo físico"""
    conteo = get_object_or_404(ConteoFisico, pk=pk)
    items = ItemConteoFisico.objects.filter(conteo=conteo)
    
    return render(request, 'inventario/conteo_fisico/detalle.html', {
        'conteo': conteo,
        'items': items,
    })


@login_required
@require_http_methods(["POST"])
def iniciar_conteo(request, pk):
    """Iniciar un conteo físico"""
    conteo = get_object_or_404(ConteoFisico, pk=pk)
    
    if conteo.estado != 'creado':
        messages.error(request, 'Solo se pueden iniciar conteos en estado "creado"')
        return redirect('logistica:detalle_conteo', pk=pk)
    
    conteo.estado = 'en_progreso'
    conteo.fecha_inicio = timezone.now()
    conteo.usuario_inicio = request.user
    conteo.save()
    
    messages.success(request, f'Conteo {conteo.folio} iniciado')
    return redirect('logistica:detalle_conteo', pk=pk)


@login_required
def capturar_item(request, conteo_id):
    """Capturar un item en el conteo físico"""
    conteo = get_object_or_404(ConteoFisico, pk=conteo_id)
    
    if conteo.estado != 'en_progreso':
        messages.error(request, 'El conteo no está en progreso')
        return redirect('logistica:detalle_conteo', pk=conteo_id)
    
    if request.method == 'POST':
        lote_id = request.POST.get('lote_id')
        cantidad_contada = request.POST.get('cantidad_contada')
        ubicacion_id = request.POST.get('ubicacion_id')
        fecha_caducidad = request.POST.get('fecha_caducidad')
        
        try:
            lote = Lote.objects.get(id=lote_id)
            cantidad_contada = int(cantidad_contada)
            
            # Crear item de conteo
            item = ItemConteoFisico.objects.create(
                conteo=conteo,
                lote=lote,
                cantidad_sistema=lote.cantidad,
                cantidad_contada=cantidad_contada,
                ubicacion_anterior=lote.ubicacion,
                ubicacion_nueva_id=ubicacion_id if ubicacion_id else lote.ubicacion_id,
                fecha_caducidad_anterior=lote.fecha_caducidad,
                fecha_caducidad_nueva=fecha_caducidad if fecha_caducidad else lote.fecha_caducidad,
                usuario_captura=request.user,
            )
            
            # Calcular diferencia
            item.diferencia = cantidad_contada - lote.cantidad
            item.save()
            
            messages.success(request, f'Item capturado: {lote.producto.nombre}')
            
        except Lote.DoesNotExist:
            messages.error(request, 'Lote no encontrado')
        except ValueError:
            messages.error(request, 'Cantidad inválida')
    
    # Obtener lotes disponibles
    lotes = Lote.objects.filter(cantidad__gt=0).select_related('producto', 'ubicacion')
    items = ItemConteoFisico.objects.filter(conteo=conteo)
    ubicaciones = UbicacionAlmacen.objects.filter(activo=True)
    
    return render(request, 'inventario/conteo_fisico/capturar_item.html', {
        'conteo': conteo,
        'lotes': lotes,
        'items': items,
        'ubicaciones': ubicaciones,
    })


@login_required
@require_http_methods(["POST"])
def completar_conteo(request, pk):
    """Completar un conteo físico y aplicar cambios"""
    conteo = get_object_or_404(ConteoFisico, pk=pk)
    
    if conteo.estado != 'en_progreso':
        messages.error(request, 'Solo se pueden completar conteos en progreso')
        return redirect('logistica:detalle_conteo', pk=pk)
    
    with transaction.atomic():
        items = ItemConteoFisico.objects.filter(conteo=conteo)
        lotes_actualizados = set()
        
        for item in items:
            lote = item.lote
            
            # Actualizar cantidad por ubicación (LoteUbicacion)
            if item.ubicacion:
                lote_ubicacion, created = LoteUbicacion.objects.get_or_create(
                    lote=lote,
                    ubicacion=item.ubicacion,
                    defaults={'cantidad': item.cantidad_fisica, 'usuario_asignacion': request.user}
                )
                
                # Calcular diferencia en esta ubicación
                diferencia_ubicacion = item.cantidad_fisica - item.cantidad_teorica
                
                if diferencia_ubicacion != 0:
                    # Crear movimiento de ajuste por ubicación
                    MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento='ajuste',
                        cantidad=diferencia_ubicacion,
                        motivo=f'Ajuste por conteo físico {conteo.folio} en ubicacion {item.ubicacion.codigo}',
                        folio=conteo.folio,
                        usuario=request.user,
                    )
                    
                    # Actualizar cantidad en LoteUbicacion
                    lote_ubicacion.cantidad = item.cantidad_fisica
                    lote_ubicacion.usuario_asignacion = request.user
                    lote_ubicacion.save()
                    
                    lotes_actualizados.add(lote.id)
            
            # Aplicar cambios de fecha de caducidad si aplica
            if item.fecha_caducidad_nueva != lote.fecha_caducidad:
                lote.fecha_caducidad = item.fecha_caducidad_nueva
                lote.save()
        
        # Recalcular cantidad total del Lote como suma de todas sus ubicaciones
        for lote_id in lotes_actualizados:
            lote = Lote.objects.get(id=lote_id)
            cantidad_total = LoteUbicacion.objects.filter(lote=lote).aggregate(
                total=Sum('cantidad')
            )['total'] or 0
            lote.cantidad = cantidad_total
            lote.save()
        
        # Marcar conteo como completado
        conteo.estado = 'completado'
        conteo.fecha_finalizacion = timezone.now()
        conteo.usuario_finalizacion = request.user
        conteo.save()
        
        # Enviar notificación
        notificaciones.notificar_conteo_completado(conteo)
        
        messages.success(request, f'Conteo {conteo.folio} completado y cambios aplicados')
    
    return redirect('logistica:detalle_conteo', pk=pk)
@login_required
@require_http_methods(["POST"])
def cancelar_conteo(request, pk):
    """Cancelar un conteo físico"""
    conteo = get_object_or_404(ConteoFisico, pk=pk)
    
    if conteo.estado == 'completado':
        messages.error(request, 'No se puede cancelar un conteo completado')
        return redirect('logistica:detalle_conteo', pk=pk)
    
    conteo.estado = 'cancelado'
    conteo.save()
    
    messages.success(request, f'Conteo {conteo.folio} cancelado')
    return redirect('logistica:lista_conteos')


@login_required
@require_http_methods(["POST"])
def eliminar_item_conteo(request, item_id):
    """Eliminar un item del conteo"""
    item = get_object_or_404(ItemConteoFisico, pk=item_id)
    conteo_id = item.conteo.id
    
    if item.conteo.estado != 'en_progreso':
        messages.error(request, 'Solo se pueden eliminar items de conteos en progreso')
    else:
        item.delete()
        messages.success(request, 'Item eliminado del conteo')
    
    return redirect('logistica:capturar_item', conteo_id=conteo_id)
