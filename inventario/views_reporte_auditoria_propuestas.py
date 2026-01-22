"""
Reporte de Auditoría de Propuestas
Identifica propuestas no aplicadas, huérfanas y valida reservas y movimientos de inventario.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, Exists, OuterRef
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

from .pedidos_models import PropuestaPedido, LoteAsignado
from .models import MovimientoInventario, Lote, LoteUbicacion


@login_required
def reporte_auditoria_propuestas(request):
    """
    Reporte de auditoría de propuestas que identifica:
    1. Propuestas no aplicadas (GENERADA que no se han surtido)
    2. Propuestas huérfanas (sin solicitud asociada o estados inconsistentes)
    3. Propuestas surtidas o canceladas con reservas (no deberían tener)
    4. Propuestas surtidas sin movimientos de inventario
    """
    
    # 1. Propuestas no aplicadas (GENERADA que no se han surtido y tienen más de X días)
    dias_limite = 7  # Propuestas GENERADA con más de 7 días sin surtir
    fecha_limite = timezone.now() - timedelta(days=dias_limite)
    
    propuestas_no_aplicadas = PropuestaPedido.objects.filter(
        estado='GENERADA',
        fecha_generacion__lt=fecha_limite
    ).select_related(
        'solicitud__institucion_solicitante',
        'usuario_generacion'
    ).prefetch_related('items').order_by('fecha_generacion')
    
    # Agregar información adicional
    propuestas_no_aplicadas_info = []
    for propuesta in propuestas_no_aplicadas:
        total_items = propuesta.items.count()
        total_lotes_asignados = LoteAsignado.objects.filter(
            item_propuesta__propuesta=propuesta
        ).count()
        total_reservado = sum(
            la.cantidad_asignada for la in 
            LoteAsignado.objects.filter(item_propuesta__propuesta=propuesta)
        )
        
        propuestas_no_aplicadas_info.append({
            'propuesta': propuesta,
            'dias_sin_aplicar': (timezone.now() - propuesta.fecha_generacion).days,
            'total_items': total_items,
            'total_lotes_asignados': total_lotes_asignados,
            'total_reservado': total_reservado,
        })
    
    # 2. Propuestas huérfanas (sin solicitud asociada o estados inconsistentes)
    propuestas_huerfanas = []
    
    # Propuestas sin solicitud asociada (no debería pasar, pero por si acaso)
    propuestas_sin_solicitud = PropuestaPedido.objects.filter(
        solicitud__isnull=True
    ).select_related('usuario_generacion')
    
    for propuesta in propuestas_sin_solicitud:
        propuestas_huerfanas.append({
            'propuesta': propuesta,
            'problema': 'Sin solicitud asociada',
            'severidad': 'ALTA'
        })
    
    # Propuestas con estados inconsistentes
    # Ejemplo: SURTIDA pero sin lotes asignados surtidos
    propuestas_surtidas_todas_check = PropuestaPedido.objects.filter(
        estado='SURTIDA'
    ).select_related('solicitud__institucion_solicitante', 'usuario_generacion')
    
    for propuesta in propuestas_surtidas_todas_check:
        lotes_surtidos_count = LoteAsignado.objects.filter(
            item_propuesta__propuesta=propuesta,
            surtido=True
        ).count()
        
        if lotes_surtidos_count == 0:
            propuestas_huerfanas.append({
                'propuesta': propuesta,
                'problema': 'Estado SURTIDA pero sin lotes asignados surtidos',
                'severidad': 'ALTA'
            })
    
    # Propuestas CANCELADA que aún tienen lotes asignados (deberían haberse liberado)
    propuestas_canceladas_con_lotes = PropuestaPedido.objects.filter(
        estado='CANCELADA'
    ).select_related('solicitud__institucion_solicitante', 'usuario_generacion')
    
    for propuesta in propuestas_canceladas_con_lotes:
        lotes_asignados_count = LoteAsignado.objects.filter(
            item_propuesta__propuesta=propuesta
        ).count()
        
        if lotes_asignados_count > 0:
            propuestas_huerfanas.append({
                'propuesta': propuesta,
                'problema': f'Estado CANCELADA pero aún tiene {lotes_asignados_count} lotes asignados (deberían haberse liberado)',
                'severidad': 'MEDIA'
            })
    
    # 3. Propuestas surtidas o canceladas con reservas (no deberían tener)
    propuestas_con_reservas_invalidas = []
    
    # Propuestas SURTIDA con reservas
    propuestas_surtidas = PropuestaPedido.objects.filter(
        estado='SURTIDA'
    ).select_related('solicitud__institucion_solicitante')
    
    for propuesta in propuestas_surtidas:
        # Verificar si tiene lotes asignados con cantidad_reservada > 0
        lotes_con_reserva = LoteAsignado.objects.filter(
            item_propuesta__propuesta=propuesta,
            surtido=True
        ).select_related('lote_ubicacion__lote', 'lote_ubicacion')
        
        total_reservado = 0
        detalles_reservas = []
        
        for lote_asignado in lotes_con_reserva:
            lote = lote_asignado.lote_ubicacion.lote
            lote_ubicacion = lote_asignado.lote_ubicacion
            
            # Verificar reservas a nivel de lote
            if lote.cantidad_reservada > 0:
                total_reservado += lote.cantidad_reservada
                detalles_reservas.append(
                    f"Lote {lote.numero_lote}: {lote.cantidad_reservada} unidades reservadas a nivel de lote"
                )
            
            # Verificar reservas a nivel de ubicación
            if lote_ubicacion.cantidad_reservada > 0:
                total_reservado += lote_ubicacion.cantidad_reservada
                detalles_reservas.append(
                    f"Lote {lote.numero_lote} Ubicación {lote_ubicacion.ubicacion.codigo if lote_ubicacion.ubicacion else 'N/A'}: {lote_ubicacion.cantidad_reservada} unidades reservadas en ubicación"
                )
        
        if total_reservado > 0:
            propuestas_con_reservas_invalidas.append({
                'propuesta': propuesta,
                'estado': 'SURTIDA',
                'total_reservado': total_reservado,
                'detalles': detalles_reservas
            })
    
    # Propuestas CANCELADA con reservas
    propuestas_canceladas = PropuestaPedido.objects.filter(
        estado='CANCELADA'
    ).select_related('solicitud__institucion_solicitante')
    
    for propuesta in propuestas_canceladas:
        # Verificar si tiene lotes asignados con cantidad_reservada > 0
        lotes_con_reserva = LoteAsignado.objects.filter(
            item_propuesta__propuesta=propuesta
        ).select_related('lote_ubicacion__lote', 'lote_ubicacion')
        
        total_reservado = 0
        detalles_reservas = []
        
        for lote_asignado in lotes_con_reserva:
            lote = lote_asignado.lote_ubicacion.lote
            lote_ubicacion = lote_asignado.lote_ubicacion
            
            # Verificar reservas a nivel de lote
            if lote.cantidad_reservada > 0:
                total_reservado += lote.cantidad_reservada
                detalles_reservas.append(
                    f"Lote {lote.numero_lote}: {lote.cantidad_reservada} unidades reservadas a nivel de lote"
                )
            
            # Verificar reservas a nivel de ubicación
            if lote_ubicacion.cantidad_reservada > 0:
                total_reservado += lote_ubicacion.cantidad_reservada
                detalles_reservas.append(
                    f"Lote {lote.numero_lote} Ubicación {lote_ubicacion.ubicacion.codigo if lote_ubicacion.ubicacion else 'N/A'}: {lote_ubicacion.cantidad_reservada} unidades reservadas en ubicación"
                )
        
        if total_reservado > 0:
            propuestas_con_reservas_invalidas.append({
                'propuesta': propuesta,
                'estado': 'CANCELADA',
                'total_reservado': total_reservado,
                'detalles': detalles_reservas
            })
    
    # 4. Propuestas surtidas sin movimientos de inventario
    propuestas_sin_movimientos = []
    
    # Obtener todas las propuestas surtidas
    propuestas_surtidas_todas = PropuestaPedido.objects.filter(
        estado='SURTIDA'
    ).select_related('solicitud__institucion_solicitante')
    
    for propuesta in propuestas_surtidas_todas:
        # Verificar si tiene movimientos de inventario asociados
        # Los movimientos tienen el folio de la propuesta en el campo 'folio'
        # o el folio de la solicitud en 'documento_referencia' o 'pedido'
        movimientos = MovimientoInventario.objects.filter(
            Q(folio=str(propuesta.id)) |
            Q(documento_referencia=propuesta.solicitud.folio) |
            Q(pedido=propuesta.solicitud.folio),
            tipo_movimiento='SALIDA',
            anulado=False
        )
        
        if movimientos.count() == 0:
            # Contar lotes asignados surtidos
            lotes_surtidos = LoteAsignado.objects.filter(
                item_propuesta__propuesta=propuesta,
                surtido=True
            ).count()
            
            # Solo incluir si tiene lotes surtidos (si no tiene, puede ser una propuesta vacía)
            if lotes_surtidos > 0:
                propuestas_sin_movimientos.append({
                    'propuesta': propuesta,
                    'lotes_surtidos': lotes_surtidos,
                    'total_items': propuesta.items.count()
                })
    
    # Resumen
    resumen = {
        'total_no_aplicadas': len(propuestas_no_aplicadas_info),
        'total_huerfanas': len(propuestas_huerfanas),
        'total_con_reservas_invalidas': len(propuestas_con_reservas_invalidas),
        'total_sin_movimientos': len(propuestas_sin_movimientos),
    }
    
    context = {
        'page_title': 'Auditoría de Propuestas',
        'propuestas_no_aplicadas': propuestas_no_aplicadas_info,
        'propuestas_huerfanas': propuestas_huerfanas,
        'propuestas_con_reservas_invalidas': propuestas_con_reservas_invalidas,
        'propuestas_sin_movimientos': propuestas_sin_movimientos,
        'resumen': resumen,
        'dias_limite': dias_limite,
    }
    
    return render(request, 'inventario/reportes/reporte_auditoria_propuestas.html', context)
