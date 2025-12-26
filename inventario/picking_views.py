"""
Fase 6 - Optimización de Picking para Suministro
Vistas para ordenar y visualizar propuestas de forma optimizada
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, F
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.template.loader import get_template
from datetime import datetime
from xhtml2pdf import pisa

from .pedidos_models import PropuestaPedido, ItemPropuesta, LoteAsignado
from .models import Lote, UbicacionAlmacen, Almacen
from .decorators_roles import requiere_rol
from .fase5_utils import generar_movimientos_suministro


# ============================================================
# DASHBOARD DE PICKING
# ============================================================

@requiere_rol('Almacenista', 'Administrador', 'Gestor de Inventario')
def dashboard_picking(request):
    """
    Dashboard de picking - Muestra propuestas disponibles para picking
    Optimizado para tablet
    """
    
    # Obtener propuestas en estado REVISADA o EN_SURTIMIENTO
    propuestas = PropuestaPedido.objects.filter(
        estado__in=['REVISADA', 'EN_SURTIMIENTO']
    ).select_related('solicitud').order_by('-fecha_generacion')
    
    # Filtros
    almacen_filter = request.GET.get('almacen')
    if almacen_filter:
        propuestas = propuestas.filter(solicitud__almacen_destino_id=almacen_filter)
    
    estado_filter = request.GET.get('estado')
    if estado_filter:
        propuestas = propuestas.filter(estado=estado_filter)
    
    # Búsqueda
    busqueda = request.GET.get('q')
    if busqueda:
        propuestas = propuestas.filter(
            Q(solicitud__folio__icontains=busqueda) |
            Q(solicitud__institucion_solicitante__nombre__icontains=busqueda)
        )
    
    # Contar items por propuesta
    propuestas_con_items = []
    for prop in propuestas:
        total_items = prop.items.count()
        propuestas_con_items.append({
            'propuesta': prop,
            'total_items': total_items,
            'items_pendientes': prop.items.filter(estado__in=['DISPONIBLE', 'PARCIAL']).count()
        })
    
    # Obtener almacenes para filtro
    almacenes = Almacen.objects.all()
    
    context = {
        'propuestas': propuestas_con_items,
        'almacenes': almacenes,
        'almacen_filter': almacen_filter,
        'estado_filter': estado_filter,
        'busqueda': busqueda,
    }
    
    return render(request, 'inventario/picking/dashboard_picking.html', context)


# ============================================================
# VISTA DE PICKING OPTIMIZADA
# ============================================================

@requiere_rol('Almacenista', 'Administrador', 'Gestor de Inventario')
def picking_propuesta(request, propuesta_id):
    """
    Vista optimizada de picking para tablet/pantalla
    Muestra los items ordenados por ubicación
    """
    
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    
    # Validar que la propuesta esté en estado correcto
    if propuesta.estado not in ['REVISADA', 'EN_SURTIMIENTO']:
        messages.error(request, 'La propuesta no está lista para picking.')
        return redirect('detalle_propuesta', pk=propuesta_id)
    
    # Obtener orden de picking
    orden_picking = request.GET.get('orden', 'ubicacion')  # ubicacion, producto, cantidad
    
    # Obtener items de la propuesta con lotes asignados
    items_picking = []
    
    for item in propuesta.items.all():
        for lote_asignado in item.lotes_asignados.filter(surtido=False):
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            items_picking.append({
                'item_id': item.id,
                'lote_asignado_id': lote_asignado.id,
                'producto': lote.producto.descripcion,
                'cantidad': lote_asignado.cantidad_asignada,
                'lote_numero': lote.numero_lote,
                'almacen': lote_ubicacion.ubicacion.almacen.nombre,
                'almacen_id': lote_ubicacion.ubicacion.almacen_id,
                'ubicacion': lote_ubicacion.ubicacion.codigo,
                'ubicacion_id': lote_ubicacion.ubicacion_id,
                'clave_cnis': lote.producto.clave_cnis,
            })
    
    # Ordenar según parámetro
    if orden_picking == 'producto':
        items_picking.sort(key=lambda x: x['producto'])
    elif orden_picking == 'cantidad':
        items_picking.sort(key=lambda x: x['cantidad'], reverse=True)
    else:  # ubicacion (predeterminado)
        items_picking.sort(key=lambda x: (x['almacen_id'], x['ubicacion_id']))
    
    # Agrupar por ubicación para vista
    ubicaciones_agrupadas = {}
    for item in items_picking:
        key = f"{item['almacen']} - {item['ubicacion']}"
        if key not in ubicaciones_agrupadas:
            ubicaciones_agrupadas[key] = []
        ubicaciones_agrupadas[key].append(item)
    
    context = {
        'propuesta': propuesta,
        'items_picking': items_picking,
        'ubicaciones_agrupadas': ubicaciones_agrupadas,
        'orden_picking': orden_picking,
        'total_items': len(items_picking),
    }
    
    return render(request, 'inventario/picking/picking_propuesta.html', context)



# ============================================================
# MARCAR ITEM COMO RECOGIDO (AJAX)
# ============================================================

@login_required
@csrf_exempt
@require_http_methods(['POST'])
def marcar_item_recogido(request, lote_asignado_id):
    """
    Marca un item como recogido en la vista de picking
    Verifica si todos los items están recogidos y completa la propuesta
    """
    
    try:
        lote_asignado = LoteAsignado.objects.get(id=lote_asignado_id)
        propuesta = lote_asignado.item_propuesta.propuesta
        
        lote_asignado.surtido = True
        lote_asignado.save()
        
        # Verificar si todos los items de la propuesta están recogidos
        total_lotes = LoteAsignado.objects.filter(
            item_propuesta__propuesta=propuesta
        ).count()
        
        lotes_recogidos = LoteAsignado.objects.filter(
            item_propuesta__propuesta=propuesta,
            surtido=True
        ).count()
        
        propuesta_completada = False
        
        if total_lotes == lotes_recogidos and total_lotes > 0:
            # Todos los items han sido recogidos
            propuesta.estado = 'SURTIDA'
            propuesta.fecha_surtimiento = timezone.now()
            propuesta.usuario_surtimiento = request.user
            propuesta.save()
            
            # Generar movimientos de inventario
            resultado = generar_movimientos_suministro(propuesta.id, request.user)
            propuesta_completada = True
        
        return JsonResponse({
            'exito': True,
            'mensaje': 'Item marcado como recogido',
            'propuesta_completada': propuesta_completada,
            'lotes_recogidos': lotes_recogidos,
            'total_lotes': total_lotes
        })
    
    except LoteAsignado.DoesNotExist:
        return JsonResponse({
            'exito': False,
            'mensaje': 'Item no encontrado'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'exito': False,
            'mensaje': f'Error: {str(e)}'
        }, status=500)


# ============================================================
# IMPRIMIR HOJA DE SURTIDO
# ============================================================

@login_required
def imprimir_hoja_surtido(request, propuesta_id):
    """
    Genera un PDF con la hoja de surtido
    """
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    template_path = 'inventario/picking/hoja_surtido_pdf.html'
    context = {'propuesta': propuesta}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=hoja_surtido_{propuesta.solicitud.folio}.pdf'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
