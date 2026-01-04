from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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
    """API para buscar lotes por número o clave"""
    
    try:
        data = json.loads(request.body)
        busqueda = data.get('busqueda', '').strip()
        
        if len(busqueda) < 2:
            return JsonResponse({'error': 'Ingresa al menos 2 caracteres'}, status=400)
        
        # Buscar en número de lote o clave del producto
        lotes = Lote.objects.filter(
            numero_lote__icontains=busqueda
        ).values('id', 'numero_lote', 'producto__descripcion', 'cantidad_disponible')[:10]
        
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
        ).values('id', 'codigo', 'descripcion', 'nivel', 'fila', 'columna').order_by('codigo')
        
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
            'message': f'✓ {lote.numero_lote} asignado a {ubicacion.codigo}',
            'lote_ubicacion': {
                'id': lote_ubicacion.id,
                'lote': lote.numero_lote,
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
