from django.http import JsonResponse
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint para monitoreo
    Accesible sin autenticación
    """
    try:
        # Verificar conexión a base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"❌ Health check - BD error: {e}")
    
    return JsonResponse({
        'status': 'ok' if db_status == 'ok' else 'degraded',
        'timestamp': timezone.now().isoformat(),
        'database': db_status,
    })


@login_required
def diagnostico_sistema(request):
    """
    Vista de diagnóstico para administradores
    Muestra el estado del sistema
    """
    
    # Verificar que sea admin
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({
            'error': 'No tienes permisos para acceder a este recurso'
        }, status=403)
    
    diagnostico = {
        'timestamp': timezone.now().isoformat(),
        'usuario': request.user.username,
        'es_superuser': request.user.is_superuser,
        'es_staff': request.user.is_staff,
        'database': {},
        'sistema': {},
    }
    
    # Verificar base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        diagnostico['database']['status'] = 'ok'
        diagnostico['database']['message'] = 'Conexión a BD exitosa'
    except Exception as e:
        diagnostico['database']['status'] = 'error'
        diagnostico['database']['message'] = str(e)
        logger.error(f"❌ Diagnóstico - BD error: {e}")
    
    # Verificar tablas importantes
    try:
        from .models import LogSistema, Lote, MovimientoInventario
        
        logs_count = LogSistema.objects.count()
        lotes_count = Lote.objects.count()
        movimientos_count = MovimientoInventario.objects.count()
        
        diagnostico['sistema']['logs_count'] = logs_count
        diagnostico['sistema']['lotes_count'] = lotes_count
        diagnostico['sistema']['movimientos_count'] = movimientos_count
        diagnostico['sistema']['status'] = 'ok'
    except Exception as e:
        diagnostico['sistema']['status'] = 'error'
        diagnostico['sistema']['message'] = str(e)
        logger.error(f"❌ Diagnóstico - Error al contar registros: {e}")
    
    logger.info(f"📊 Diagnóstico solicitado por {request.user.username}")
    
    return JsonResponse(diagnostico)
