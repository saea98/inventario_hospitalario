from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json

from .models import Lote, UbicacionAlmacen, LoteUbicacion, Almacen


@login_required
def asignacion_rapida(request):
    """Vista simplificada para asignación rápida de ubicaciones"""
    
    almacenes = Almacen.objects.all()
    
    context = {
        'almacenes': almacenes,
    }
    
    return render(request, 'inventario/asignacion_rapida/formulario.html', context)


@login_required
@require_http_methods(["POST"])
def api_buscar_lote(request):
    """API para buscar lotes por número de lote Y/O clave CNIS"""
    
    try:
        data = json.loads(request.body)
        lote_busqueda = data.get('lote', '').strip()
        cnis_busqueda = data.get('cnis', '').strip()
        
        # Compatibilidad con búsqueda antigua (campo 'busqueda')
        busqueda_antigua = data.get('busqueda', '').strip()
        if busqueda_antigua and not lote_busqueda and not cnis_busqueda:
            lote_busqueda = busqueda_antigua
        
        # Necesita al menos 2 caracteres en alguno de los campos
        if len(lote_busqueda) < 2 and len(cnis_busqueda) < 2:
            return JsonResponse({'error': 'Ingresa al menos 2 caracteres en Lote o CNIS'}, status=400)
        
        # Construir filtro dinámico
        filtro = Q()
        
        if len(lote_busqueda) >= 2:
            filtro |= Q(numero_lote__icontains=lote_busqueda)
        
        if len(cnis_busqueda) >= 2:
            filtro |= Q(producto__clave_cnis__icontains=cnis_busqueda)
        
        # Si ambos campos tienen búsqueda, hacer AND en lugar de OR
        if len(lote_busqueda) >= 2 and len(cnis_busqueda) >= 2:
            filtro = Q(numero_lote__icontains=lote_busqueda) & Q(producto__clave_cnis__icontains=cnis_busqueda)
        
        lotes = Lote.objects.filter(filtro).select_related('producto').values(
            'id', 'numero_lote', 'producto__clave_cnis', 'producto__descripcion', 'cantidad_disponible'
        ).order_by('-id')[:15]
        
        return JsonResponse({
            'success': True,
            'lotes': list(lotes)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_obtener_ubicaciones(request):
    """API para obtener ubicaciones disponibles de un almacén"""
    
    try:
        data = json.loads(request.body)
        almacen_id = data.get('almacen_id')
        
        if not almacen_id:
            return JsonResponse({'error': 'Almacén requerido'}, status=400)
        
        ubicaciones = UbicacionAlmacen.objects.filter(
            almacen_id=almacen_id
        ).values('id', 'codigo', 'descripcion', 'nivel', 'pasillo', 'rack', 'seccion').order_by('codigo')
        
        return JsonResponse({
            'success': True,
            'ubicaciones': list(ubicaciones)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_asignar_ubicacion(request):
    """API para asignar ubicación a un lote"""
    
    try:
        data = json.loads(request.body)
        lote_id = data.get('lote_id')
        ubicacion_id = data.get('ubicacion_id')
        cantidad = data.get('cantidad', 0)
        
        # Validaciones
        if not lote_id or not ubicacion_id:
            return JsonResponse({'error': 'Lote y ubicación requeridos'}, status=400)
        
        lote = Lote.objects.get(id=lote_id)
        ubicacion = UbicacionAlmacen.objects.get(id=ubicacion_id)
        
        # Validar cantidad
        cantidad = int(cantidad) if cantidad else lote.cantidad_disponible
        if cantidad <= 0 or cantidad > lote.cantidad_disponible:
            return JsonResponse({
                'error': f'Cantidad inválida. Disponible: {lote.cantidad_disponible}'
            }, status=400)
        
        # Crear o actualizar asignación
        lote_ubicacion, created = LoteUbicacion.objects.get_or_create(
            lote=lote,
            ubicacion=ubicacion,
            defaults={'cantidad': cantidad}
        )
        
        if not created:
            lote_ubicacion.cantidad += cantidad
            lote_ubicacion.save()
        
        return JsonResponse({
            'success': True,
            'message': f'✓ {lote.numero_lote} ({lote.producto.clave_cnis}) asignado a {ubicacion.codigo}',
            'lote_ubicacion': {
                'id': lote_ubicacion.id,
                'lote': lote.numero_lote,
                'clave_cnis': lote.producto.clave_cnis,
                'ubicacion': ubicacion.codigo,
                'cantidad': lote_ubicacion.cantidad
            }
        })
    
    except Lote.DoesNotExist:
        return JsonResponse({'error': 'Lote no encontrado'}, status=404)
    except UbicacionAlmacen.DoesNotExist:
        return JsonResponse({'error': 'Ubicación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
