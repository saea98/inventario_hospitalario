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
            # Verificar si existe una configuración de menú para esta URL
            try:
                menu_item = MenuItemRol.objects.get(url_name=url_name, activo=True)
                
                # Si el usuario no es superusuario, verificar roles
                if not request.user.is_superuser:
                    if not menu_item.puede_ver_usuario(request.user):
                        # Usuario no tiene permiso
                        mensaje = (
                            f"No tienes permiso para acceder a '{menu_item.nombre_mostrado}'. "
                            f"Contacta con el administrador si crees que es un error."
                        )
                        messages.error(request, mensaje)
                        return redirect('dashboard')
            except MenuItemRol.DoesNotExist:
                # No hay configuración de menú para esta URL, permitir acceso
                pass
        
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
