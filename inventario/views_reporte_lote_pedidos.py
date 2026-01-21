"""
Vistas para reporte de lotes y pedidos asociados.
Permite buscar un lote específico y ver todos los pedidos donde está asignado.

Relaciones:
- Lote -> LoteUbicacion -> LoteAsignado -> ItemPropuesta -> PropuestaPedido -> SolicitudPedido
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q, Sum, F, DecimalField, Case, When, Value
from django.db.models.functions import Coalesce
from datetime import date
import logging

from .models import Lote, Producto, LoteUbicacion
from .pedidos_models import ItemPropuesta, LoteAsignado, PropuestaPedido, ItemSolicitud

logger = logging.getLogger(__name__)


@login_required
def reporte_lote_pedidos(request):
    """
    Reporte de lote y pedidos asociados.
    Permite buscar un lote específico y ver todos los pedidos donde está asignado.
    """
    
    # Obtener parámetros de búsqueda
    filtro_clave = request.GET.get('clave', '').strip()
    filtro_lote = request.GET.get('lote', '').strip()
    
    datos_lote = None
    datos_pedidos = []
    total_reservado = 0
    total_surtido = 0
    mensaje_debug = ""
    
    print(f"\n[DEBUG] Búsqueda: clave={filtro_clave}, lote={filtro_lote}")
    
    # Si hay filtros, buscar el lote
    if filtro_clave or filtro_lote:
        # Buscar el lote
        query_lote = Lote.objects.select_related(
            'producto',
            'institucion',
            'almacen'
        ).filter(
            estado=1  # Solo lotes disponibles
        )
        
        if filtro_clave:
            query_lote = query_lote.filter(
                Q(producto__clave_cnis__icontains=filtro_clave) |
                Q(producto__descripcion__icontains=filtro_clave)
            )
        
        if filtro_lote:
            query_lote = query_lote.filter(numero_lote__icontains=filtro_lote)
        
        print(f"[DEBUG] Lotes encontrados: {query_lote.count()}")
        mensaje_debug += f"✓ Lotes encontrados: {query_lote.count()}\n"
        
        # Si hay un único lote, mostrar sus pedidos
        if query_lote.exists():
            if query_lote.count() == 1:
                lote = query_lote.first()
                print(f"[DEBUG] Procesando lote: {lote.numero_lote} (ID: {lote.id})")
                mensaje_debug += f"✓ Procesando lote: {lote.numero_lote} (ID: {lote.id})\n"
                
                # Preparar datos del lote
                datos_lote = {
                    'lote_id': lote.id,
                    'clave': lote.producto.clave_cnis,
                    'descripcion': lote.producto.descripcion,
                    'numero_lote': lote.numero_lote,
                    'institucion': lote.institucion.denominacion if lote.institucion else 'N/A',
                    'cantidad_disponible': lote.cantidad_disponible,
                    'cantidad_reservada': lote.cantidad_reservada,
                    'cantidad_neta': max(0, lote.cantidad_disponible - lote.cantidad_reservada),
                    'fecha_caducidad': lote.fecha_caducidad,
                    'precio_unitario': lote.precio_unitario,
                    'valor_total': lote.valor_total,
                }
                
                # NUEVA LÓGICA: Buscar desde LoteAsignado hacia el lote
                # Paso 1: Buscar LoteUbicacion para este lote
                lotes_ubicacion = LoteUbicacion.objects.filter(lote=lote)
                print(f"[DEBUG] LoteUbicacion encontrados: {lotes_ubicacion.count()}")
                mensaje_debug += f"✓ LoteUbicacion encontrados: {lotes_ubicacion.count()}\n"
                
                if lotes_ubicacion.exists():
                    # Paso 2: Buscar LoteAsignado que usan esos LoteUbicacion
                    lotes_asignados = LoteAsignado.objects.filter(
                        lote_ubicacion__in=lotes_ubicacion
                    ).select_related(
                        'item_propuesta',
                        'lote_ubicacion'
                    ).prefetch_related(
                        'item_propuesta__propuesta__solicitud',
                        'item_propuesta__producto'
                    )
                    
                    print(f"[DEBUG] LoteAsignado encontrados: {lotes_asignados.count()}")
                    mensaje_debug += f"✓ LoteAsignado encontrados: {lotes_asignados.count()}\n"
                    
                    if lotes_asignados.exists():
                        # Agrupar por propuesta para obtener información de pedidos
                        pedidos_dict = {}
                        
                        for lote_asignado in lotes_asignados:
                            try:
                                item_prop = lote_asignado.item_propuesta
                                propuesta = item_prop.propuesta
                                solicitud = propuesta.solicitud
                                
                                print(f"[DEBUG] Procesando: Propuesta {propuesta.id}, Item {item_prop.id}")
                                
                                # Clave única del pedido
                                pedido_key = propuesta.id
                                
                                if pedido_key not in pedidos_dict:
                                    pedidos_dict[pedido_key] = {
                                        'propuesta_id': propuesta.id,
                                        'solicitud_folio': solicitud.folio,
                                        'institucion_solicitante': solicitud.institucion_solicitante.denominacion,
                                        'estado_propuesta': propuesta.get_estado_display(),
                                        'fecha_generacion': propuesta.fecha_generacion,
                                        'items': {}
                                    }
                                
                                # Usar diccionario para items para evitar duplicados
                                item_key = item_prop.id
                                
                                if item_key not in pedidos_dict[pedido_key]['items']:
                                    item_info = {
                                        'item_propuesta_id': item_prop.id,
                                        'producto_clave': item_prop.producto.clave_cnis,
                                        'producto_descripcion': item_prop.producto.descripcion,
                                        'cantidad_solicitada': item_prop.cantidad_solicitada,
                                        'cantidad_disponible': item_prop.cantidad_disponible,
                                        'cantidad_propuesta': item_prop.cantidad_propuesta,
                                        'cantidad_surtida': item_prop.cantidad_surtida,
                                        'estado_item': item_prop.estado,
                                        'lotes_asignados': []
                                    }
                                    pedidos_dict[pedido_key]['items'][item_key] = item_info
                                
                                # Agregar información del lote asignado
                                lote_info = {
                                    'cantidad_asignada': lote_asignado.cantidad_asignada,
                                    'fecha_asignacion': lote_asignado.fecha_asignacion,
                                    'fecha_surtimiento': lote_asignado.fecha_surtimiento,
                                    'surtido': lote_asignado.surtido,
                                    'numero_lote': lote_asignado.lote_ubicacion.lote.numero_lote,
                                }
                                
                                pedidos_dict[pedido_key]['items'][item_key]['lotes_asignados'].append(lote_info)
                                
                                # Acumular totales
                                total_reservado += item_prop.cantidad_propuesta
                                total_surtido += item_prop.cantidad_surtida
                                
                            except Exception as e:
                                print(f"[DEBUG] Error procesando lote asignado: {str(e)}")
                                mensaje_debug += f"✗ Error procesando lote asignado: {str(e)}\n"
                                import traceback
                                traceback.print_exc()
                        
                        # Convertir dict a lista
                        for pedido_key in pedidos_dict:
                            # Convertir items dict a lista
                            pedidos_dict[pedido_key]['items'] = list(pedidos_dict[pedido_key]['items'].values())
                        
                        datos_pedidos = list(pedidos_dict.values())
                        print(f"[DEBUG] Pedidos procesados: {len(datos_pedidos)}")
                        mensaje_debug += f"✓ Pedidos procesados: {len(datos_pedidos)}\n"
                    else:
                        print(f"[DEBUG] No hay LoteAsignado para estos LoteUbicacion")
                        mensaje_debug += "✗ No hay LoteAsignado para estos LoteUbicacion\n"
                else:
                    print(f"[DEBUG] No hay LoteUbicacion para este lote")
                    mensaje_debug += "✗ No hay LoteUbicacion para este lote\n"
            else:
                # Si hay múltiples lotes, mostrar lista para seleccionar
                print(f"[DEBUG] Múltiples lotes encontrados: {query_lote.count()}")
                mensaje_debug += f"⚠ Múltiples lotes encontrados: {query_lote.count()}\n"
                mensaje_debug += "Por favor, sé más específico en la búsqueda.\n"
    
    # Contexto
    context = {
        'page_title': 'Reporte de Lote y Pedidos',
        'filtro_clave': filtro_clave,
        'filtro_lote': filtro_lote,
        'datos_lote': datos_lote,
        'datos_pedidos': datos_pedidos,
        'total_reservado': total_reservado,
        'total_surtido': total_surtido,
        'total_pendiente': max(0, datos_lote['cantidad_neta'] - total_surtido) if datos_lote else 0,
        'mensaje_debug': mensaje_debug,
    }
    
    return render(request, 'inventario/reportes/reporte_lote_pedidos.html', context)
