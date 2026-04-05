"""
Middleware para control de acceso basado en roles
Verifica permisos de acceso a vistas protegidas
"""

from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve
from django.http import HttpResponseForbidden
from inventario.models import MenuItemRol


class ControlAccesoRolesMiddleware:
    """
    Middleware que verifica si el usuario tiene acceso a la vista solicitada
    basado en los roles configurados en MenuItemRol.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs que no requieren verificación de roles
        self.urls_excluidas = [
            'login',
            'logout',
            'dashboard',
            'admin:login',
            'admin:logout',
            'admin:index',
        ]
    
    def __call__(self, request):
        # Obtener el nombre de la URL actual
        try:
            url_name = resolve(request.path_info).url_name
        except:
            url_name = None
        
        # Si está autenticado y la URL no está excluida, verificar acceso
        if request.user.is_authenticated and url_name and url_name not in self.urls_excluidas:
            # Verificar si existe una configuración de menú para esta URL (first() evita MultipleObjectsReturned si hay duplicados)
            menu_item = MenuItemRol.objects.filter(url_name=url_name, activo=True).first()
            if menu_item and not request.user.is_superuser:
                if not menu_item.puede_ver_usuario(request.user):
                    mensaje = (
                        f"No tienes permiso para acceder a '{menu_item.nombre_mostrado}'. "
                        f"Contacta con el administrador si crees que es un error."
                    )
                    messages.error(request, mensaje)
                    return redirect('dashboard')
        
        response = self.get_response(request)
        return response


class AgregarContextoAccesoMiddleware:
    """
    Middleware que agrega información de acceso al contexto de las peticiones.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Agregar información de acceso al request
        if request.user.is_authenticated:
            request.roles_usuario = list(request.user.groups.values_list('name', flat=True))
            request.es_admin = request.user.is_superuser or request.user.groups.filter(name='Administrador').exists()
        else:
            request.roles_usuario = []
            request.es_admin = False
        
        response = self.get_response(request)
        return response


import logging
import traceback
from django.utils import timezone
from django.http import JsonResponse
from .models import LogSistema

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Obtener la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class LoggingMiddleware:
    """Middleware para registrar todas las solicitudes y errores"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        logger.debug("LoggingMiddleware inicializado")
    
    def __call__(self, request):
        # Log de solicitud
        logger.debug(f"📨 {request.method} {request.path}")
        
        try:
            response = self.get_response(request)
            
            # Log de respuesta exitosa
            if response.status_code >= 400:
                if response.status_code == 404:
                    logger.debug(
                        "%s %s - 404 (omitido en consola INFO; típico bots/rutas inexistentes)",
                        request.method,
                        request.path,
                    )
                else:
                    logger.warning(
                        "⚠️ %s %s - Status: %s",
                        request.method,
                        request.path,
                        response.status_code,
                    )
            else:
                logger.debug(f"✅ {request.method} {request.path} - Status: {response.status_code}")
            
            return response
        
        except Exception as e:
            # Registrar el error en logs
            logger.error(f"❌ Error en {request.method} {request.path}")
            logger.error(f"Error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Intentar registrar en la base de datos
            try:
                LogSistema.crear_log(
                    nivel='ERROR',
                    tipo='SISTEMA',
                    titulo=f'Error no manejado en {request.path}',
                    mensaje=str(e),
                    usuario=request.user if request.user.is_authenticated else None,
                    url=request.path,
                    ip_cliente=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    detalles={
                        'metodo': request.method,
                        'path': request.path,
                        'traceback': traceback.format_exc()
                    }
                )
            except Exception as db_error:
                logger.error(f"No se pudo registrar el error en BD: {db_error}")
            
            # Re-lanzar la excepción para que Django la maneje
            raise


class HealthCheckMiddleware:
    """Middleware para health checks sin logging excesivo"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Health check endpoint
        if request.path == '/health/':
            return JsonResponse({
                'status': 'ok',
                'timestamp': timezone.now().isoformat()
            })
        
        return self.get_response(request)


class RequestLoggingMiddleware:
    """Middleware para registrar detalles de solicitudes en producción"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Rutas que no queremos loguear (para evitar ruido)
        rutas_ignoradas = [
            '/static/',
            '/media/',
            '/health/',
            '/favicon.ico',
        ]
        prefijos_ruido = (
            '/wp-', '/wordpress', '/wp/', '/xmlrpc', 'wp-login', 'wlwmanifest',
            '/.env', '/.git', '/phpmyadmin', '/administrator',
        )
        path = request.path or ''
        path_lower = path.lower()

        debe_loguear = not any(path.startswith(ruta) for ruta in rutas_ignoradas)
        if debe_loguear and any(p in path_lower for p in prefijos_ruido):
            debe_loguear = False

        if debe_loguear:
            logger.debug("%s %s - IP: %s", request.method, path, get_client_ip(request))
        
        response = self.get_response(request)
        
        return response
