"""
Decoradores y utilidades para control de acceso basado en roles
para los módulos de ENTRADA AL ALMACÉN y PROVEEDURÍA
"""

from functools import wraps
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied


def require_role(*roles):
    """
    Decorador que requiere que el usuario pertenezca a uno de los roles especificados.
    
    IMPORTANTE: Usar SOLO este decorador, sin @login_required adicional.
    Este decorador ya incluye la validación de autenticación.
    
    Uso:
        @require_role('almacenero', 'administrador')
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
            
            # Obtener grupos del usuario
            user_groups = set(request.user.groups.values_list('name', flat=True))
            roles_requeridos = set(roles)
            
            # Verificar si el usuario pertenece a alguno de los roles requeridos
            if not user_groups.intersection(roles_requeridos):
                messages.error(
                    request,
                    f"No tienes permiso para acceder a esta sección. "
                    f"Se requiere uno de los siguientes roles: {', '.join(roles)}"
                )
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(*permissions):
    """
    Decorador que requiere que el usuario tenga los permisos especificados.
    
    Uso:
        @require_permission('inventario.add_lote', 'inventario.add_movimientoinventario')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar permisos
            for perm in permissions:
                if not request.user.has_perm(perm):
                    messages.error(
                        request,
                        f"No tienes permiso para realizar esta acción. "
                        f"Se requiere: {perm}"
                    )
                    return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_role_or_permission(roles=None, permissions=None):
    """
    Decorador que requiere que el usuario tenga uno de los roles O uno de los permisos.
    
    Uso:
        @require_role_or_permission(
            roles=['almacenero', 'administrador'],
            permissions=['inventario.add_lote']
        )
        def mi_vista(request):
            ...
    """
    roles = roles or []
    permissions = permissions or []
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Verificar roles
            user_groups = request.user.groups.values_list('name', flat=True)
            has_role = any(group in user_groups for group in roles)
            
            # Verificar permisos
            has_permission = any(request.user.has_perm(perm) for perm in permissions)
            
            if not (has_role or has_permission):
                messages.error(
                    request,
                    "No tienes permiso para acceder a esta sección."
                )
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


class RoleRequiredMixin:
    """
    Mixin para vistas basadas en clases que requiere un rol específico.
    
    Uso:
        class MiVista(RoleRequiredMixin, View):
            required_roles = ['almacenero', 'administrador']
            
            def get(self, request):
                ...
    """
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user_groups = request.user.groups.values_list('name', flat=True)
        
        if not any(group in user_groups for group in self.required_roles):
            messages.error(
                request,
                f"No tienes permiso para acceder a esta sección. "
                f"Se requiere uno de los siguientes roles: {', '.join(self.required_roles)}"
            )
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class PermissionRequiredMixin:
    """
    Mixin para vistas basadas en clases que requiere permisos específicos.
    
    Uso:
        class MiVista(PermissionRequiredMixin, View):
            required_permissions = ['inventario.add_lote']
            
            def get(self, request):
                ...
    """
    required_permissions = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        for perm in self.required_permissions:
            if not request.user.has_perm(perm):
                messages.error(
                    request,
                    f"No tienes permiso para realizar esta acción. "
                    f"Se requiere: {perm}"
                )
                return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


# Alias para compatibilidad
requiere_rol = require_role


# ============================================================
# FUNCIONES AUXILIARES PARA VERIFICAR ROLES
# ============================================================

def es_almacenero(user):
    """Verifica si el usuario es almacenero"""
    return user.groups.filter(name='almacenero').exists()


def es_responsable_proveeduria(user):
    """Verifica si el usuario es responsable de proveeduría"""
    return user.groups.filter(name='responsable_proveeduria').exists()


def es_validador(user):
    """Verifica si el usuario es validador"""
    return user.groups.filter(name='validador').exists()


def es_administrador(user):
    """Verifica si el usuario es administrador"""
    return user.groups.filter(name='administrador').exists() or user.is_staff


def puede_crear_entrada(user):
    """Verifica si el usuario puede crear entradas al almacén"""
    return (
        es_almacenero(user) or
        es_administrador(user) or
        user.has_perm('inventario.add_lote')
    )


def puede_crear_salida(user):
    """Verifica si el usuario puede crear salidas de inventario"""
    return (
        es_responsable_proveeduria(user) or
        es_administrador(user) or
        user.has_perm('inventario.add_movimientoinventario')
    )


def puede_validar(user):
    """Verifica si el usuario puede validar operaciones"""
    return (
        es_validador(user) or
        es_administrador(user) or
        user.has_perm('inventario.change_lote')
    )


# ============================================================
# CONTEXTO PARA TEMPLATES
# ============================================================

def obtener_contexto_permisos(request):
    """
    Retorna un diccionario con los permisos del usuario para usar en templates.
    
    Uso en template:
        {% if permisos.puede_crear_entrada %}
            <a href="...">Crear Entrada</a>
        {% endif %}
    """
    return {
        'puede_crear_entrada': puede_crear_entrada(request.user),
        'puede_crear_salida': puede_crear_salida(request.user),
        'puede_validar': puede_validar(request.user),
        'es_almacenero': es_almacenero(request.user),
        'es_responsable_proveeduria': es_responsable_proveeduria(request.user),
        'es_validador': es_validador(request.user),
        'es_administrador': es_administrador(request.user),
    }
