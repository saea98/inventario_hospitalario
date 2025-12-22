"""
Sistema completo de control de acceso basado en roles
Incluye decoradores, middleware y utilidades para verificar permisos
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods


# ============================================================
# DECORADORES PARA CONTROL DE ACCESO
# ============================================================

def requiere_rol(*roles):
    """
    Decorador que requiere que el usuario pertenezca a uno de los roles especificados.
    
    IMPORTANTE: Usar SOLO este decorador, sin @login_required adicional.
    Este decorador ya incluye la validación de autenticación.
    
    Soporta tanto nombres de roles como objetos Group.
    
    Uso:
        @requiere_rol('Almacenero', 'Supervisión')
        def mi_vista(request):
            ...
    
    O con múltiples roles:
        @requiere_rol('Almacenero')
        @requiere_rol('Supervisión')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación primero
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Si es superusuario, permitir acceso
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Obtener nombres de grupos del usuario
            user_groups = set(request.user.groups.values_list('name', flat=True))
            roles_requeridos = set(roles)
            
            # Verificar si el usuario pertenece a alguno de los roles requeridos
            if not user_groups.intersection(roles_requeridos):
                mensaje = (
                    f"No tienes permiso para acceder a esta sección. "
                    f"Se requiere uno de los siguientes roles: {', '.join(roles)}"
                )
                messages.error(request, mensaje)
                
                # Si es una petición AJAX, retornar JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': mensaje}, status=403)
                
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def requiere_roles_todos(*roles):
    """
    Decorador que requiere que el usuario pertenezca a TODOS los roles especificados.
    
    Uso:
        @requiere_roles_todos('Almacenero', 'Supervisión')
        def mi_vista(request):
            # El usuario debe tener ambos roles
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            # Si es superusuario, permitir acceso
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Obtener nombres de grupos del usuario
            user_groups = set(request.user.groups.values_list('name', flat=True))
            roles_requeridos = set(roles)
            
            # Verificar si el usuario tiene TODOS los roles requeridos
            if not roles_requeridos.issubset(user_groups):
                mensaje = (
                    f"No tienes permiso para acceder a esta sección. "
                    f"Se requieren los siguientes roles: {', '.join(roles)}"
                )
                messages.error(request, mensaje)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': mensaje}, status=403)
                
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def requiere_permiso(*permisos):
    """
    Decorador que requiere que el usuario tenga los permisos especificados.
    
    Uso:
        @requiere_permiso('inventario.add_lote', 'inventario.change_lote')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            # Si es superusuario, permitir acceso
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar permisos
            for permiso in permisos:
                if not request.user.has_perm(permiso):
                    mensaje = f"No tienes permiso para realizar esta acción: {permiso}"
                    messages.error(request, mensaje)
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': mensaje}, status=403)
                    
                    return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def requiere_rol_o_permiso(roles=None, permisos=None):
    """
    Decorador que requiere que el usuario tenga uno de los roles O uno de los permisos.
    
    Uso:
        @requiere_rol_o_permiso(
            roles=['Almacenero', 'Administrador'],
            permisos=['inventario.add_lote']
        )
        def mi_vista(request):
            ...
    """
    roles = roles or []
    permisos = permisos or []
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            # Si es superusuario, permitir acceso
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar roles
            user_groups = set(request.user.groups.values_list('name', flat=True))
            tiene_rol = bool(user_groups.intersection(set(roles)))
            
            # Verificar permisos
            tiene_permiso = any(request.user.has_perm(perm) for perm in permisos)
            
            if not (tiene_rol or tiene_permiso):
                mensaje = "No tienes permiso para acceder a esta sección."
                messages.error(request, mensaje)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': mensaje}, status=403)
                
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def usuario_tiene_rol(usuario, *roles):
    """
    Verifica si un usuario tiene uno de los roles especificados.
    
    Uso:
        if usuario_tiene_rol(request.user, 'Almacenero', 'Supervisión'):
            # hacer algo
    """
    if usuario.is_superuser:
        return True
    
    user_groups = set(usuario.groups.values_list('name', flat=True))
    return bool(user_groups.intersection(set(roles)))


def usuario_tiene_todos_roles(usuario, *roles):
    """
    Verifica si un usuario tiene TODOS los roles especificados.
    """
    if usuario.is_superuser:
        return True
    
    user_groups = set(usuario.groups.values_list('name', flat=True))
    return set(roles).issubset(user_groups)


def obtener_roles_usuario(usuario):
    """
    Retorna una lista con los nombres de los roles del usuario.
    """
    return list(usuario.groups.values_list('name', flat=True))


def obtener_permisos_usuario(usuario):
    """
    Retorna una lista con todos los permisos del usuario.
    """
    return list(usuario.get_all_permissions())


# ============================================================
# MIXINS PARA VISTAS BASADAS EN CLASES
# ============================================================

class RequiereRolMixin:
    """
    Mixin para vistas basadas en clases que requiere un rol específico.
    
    Uso:
        class MiVista(RequiereRolMixin, View):
            roles_requeridos = ['Almacenero', 'Administrador']
            
            def get(self, request):
                ...
    """
    roles_requeridos = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        user_groups = set(request.user.groups.values_list('name', flat=True))
        
        if not user_groups.intersection(set(self.roles_requeridos)):
            mensaje = (
                f"No tienes permiso para acceder a esta sección. "
                f"Se requiere uno de los siguientes roles: {', '.join(self.roles_requeridos)}"
            )
            messages.error(request, mensaje)
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class RequierePermisoMixin:
    """
    Mixin para vistas basadas en clases que requiere permisos específicos.
    
    Uso:
        class MiVista(RequierePermisoMixin, View):
            permisos_requeridos = ['inventario.add_lote']
            
            def get(self, request):
                ...
    """
    permisos_requeridos = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        for permiso in self.permisos_requeridos:
            if not request.user.has_perm(permiso):
                mensaje = f"No tienes permiso para realizar esta acción: {permiso}"
                messages.error(request, mensaje)
                return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


# ============================================================
# CONTEXTO PARA TEMPLATES
# ============================================================

def obtener_contexto_acceso(request):
    """
    Retorna un diccionario con información de acceso del usuario para usar en templates.
    
    Uso en template:
        {% if permisos.puede_crear_entrada %}
            <a href="...">Crear Entrada</a>
        {% endif %}
    """
    usuario = request.user
    
    return {
        'es_almacenero': usuario_tiene_rol(usuario, 'Almacenero'),
        'es_supervisión': usuario_tiene_rol(usuario, 'Supervisión'),
        'es_control_calidad': usuario_tiene_rol(usuario, 'Control Calidad'),
        'es_facturación': usuario_tiene_rol(usuario, 'Facturación'),
        'es_revisión': usuario_tiene_rol(usuario, 'Revisión'),
        'es_logística': usuario_tiene_rol(usuario, 'Logística'),
        'es_recepción': usuario_tiene_rol(usuario, 'Recepción'),
        'es_conteo': usuario_tiene_rol(usuario, 'Conteo'),
        'es_gestor_inventario': usuario_tiene_rol(usuario, 'Gestor de Inventario'),
        'es_administrador': usuario_tiene_rol(usuario, 'Administrador') or usuario.is_superuser,
        'roles_usuario': obtener_roles_usuario(usuario),
    }
