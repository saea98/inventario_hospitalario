"""
Vistas para el dashboard de administración de roles
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import Group
from inventario.models import User, MenuItemRol
from inventario.access_control import requiere_rol


@login_required
@requiere_rol('Administrador')
def dashboard_admin_roles(request):
    """
    Dashboard principal de administración de roles
    """
    contexto = {
        'total_usuarios': User.objects.count(),
        'total_roles': Group.objects.count(),
        'total_opciones_menu': MenuItemRol.objects.count(),
        'usuarios_sin_rol': User.objects.filter(groups__isnull=True).count(),
        'usuarios_activos': User.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'admin_roles/dashboard.html', contexto)


@login_required
@requiere_rol('Administrador')
def lista_usuarios_roles(request):
    """
    Lista de usuarios con sus roles asignados
    """
    usuarios = User.objects.prefetch_related('groups').all().order_by('username')
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '')
    if busqueda:
        usuarios = usuarios.filter(
            username__icontains=busqueda
        ) | usuarios.filter(
            email__icontains=busqueda
        ) | usuarios.filter(
            first_name__icontains=busqueda
        )
    
    # Filtro por rol
    rol_filtro = request.GET.get('rol', '')
    if rol_filtro:
        usuarios = usuarios.filter(groups__name=rol_filtro)
    
    roles = Group.objects.all().order_by('name')
    
    contexto = {
        'usuarios': usuarios,
        'roles': roles,
        'busqueda': busqueda,
        'rol_filtro': rol_filtro,
    }
    
    return render(request, 'admin_roles/lista_usuarios.html', contexto)


@login_required
@requiere_rol('Administrador')
def editar_usuario_roles(request, usuario_id):
    """
    Editar roles de un usuario
    """
    usuario = get_object_or_404(User, id=usuario_id)
    roles = Group.objects.all().order_by('name')
    roles_usuario = usuario.groups.all()
    
    if request.method == 'POST':
        # Obtener roles seleccionados
        roles_seleccionados = request.POST.getlist('roles')
        
        # Limpiar roles actuales
        usuario.groups.clear()
        
        # Asignar nuevos roles
        for rol_id in roles_seleccionados:
            try:
                rol = Group.objects.get(id=rol_id)
                usuario.groups.add(rol)
            except Group.DoesNotExist:
                pass
        
        messages.success(request, f'Roles del usuario "{usuario.username}" actualizados correctamente')
        return redirect('admin_roles:lista_usuarios')
    
    contexto = {
        'usuario': usuario,
        'roles': roles,
        'roles_usuario': roles_usuario,
    }
    
    return render(request, 'admin_roles/editar_usuario_roles.html', contexto)


@login_required
@requiere_rol('Administrador')
def lista_roles(request):
    """
    Lista de roles del sistema
    """
    roles = Group.objects.prefetch_related('user_set').all().order_by('name')
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '')
    if busqueda:
        roles = roles.filter(name__icontains=busqueda)
    
    contexto = {
        'roles': roles,
        'busqueda': busqueda,
    }
    
    return render(request, 'admin_roles/lista_roles.html', contexto)


@login_required
@requiere_rol('Administrador')
def detalle_rol(request, rol_id):
    """
    Detalle de un rol con usuarios asignados
    """
    rol = get_object_or_404(Group, id=rol_id)
    usuarios = rol.user_set.all().order_by('username')
    opciones_menu = MenuItemRol.objects.filter(roles_permitidos=rol).order_by('orden')
    
    contexto = {
        'rol': rol,
        'usuarios': usuarios,
        'opciones_menu': opciones_menu,
        'total_usuarios': usuarios.count(),
        'total_opciones': opciones_menu.count(),
    }
    
    return render(request, 'admin_roles/detalle_rol.html', contexto)


@login_required
@requiere_rol('Administrador')
def lista_opciones_menu(request):
    """
    Lista de opciones de menú y sus roles permitidos
    """
    opciones = MenuItemRol.objects.prefetch_related('roles_permitidos').all().order_by('orden')
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '')
    if busqueda:
        opciones = opciones.filter(nombre_mostrado__icontains=busqueda)
    
    # Filtro por estado
    estado = request.GET.get('estado', '')
    if estado == 'activo':
        opciones = opciones.filter(activo=True)
    elif estado == 'inactivo':
        opciones = opciones.filter(activo=False)
    
    contexto = {
        'opciones': opciones,
        'busqueda': busqueda,
        'estado': estado,
    }
    
    return render(request, 'admin_roles/lista_opciones_menu.html', contexto)


@login_required
@requiere_rol('Administrador')
def editar_opcion_menu(request, opcion_id):
    """
    Editar roles permitidos para una opción de menú
    """
    opcion = get_object_or_404(MenuItemRol, id=opcion_id)
    roles = Group.objects.all().order_by('name')
    roles_opcion = opcion.roles_permitidos.all()
    
    if request.method == 'POST':
        # Obtener roles seleccionados
        roles_seleccionados = request.POST.getlist('roles')
        
        # Limpiar roles actuales
        opcion.roles_permitidos.clear()
        
        # Asignar nuevos roles
        for rol_id in roles_seleccionados:
            try:
                rol = Group.objects.get(id=rol_id)
                opcion.roles_permitidos.add(rol)
            except Group.DoesNotExist:
                pass
        
        # Actualizar estado activo
        opcion.activo = request.POST.get('activo') == 'on'
        opcion.save()
        
        messages.success(request, f'Opción de menú "{opcion.nombre_mostrado}" actualizada correctamente')
        return redirect('admin_roles:lista_opciones_menu')
    
    contexto = {
        'opcion': opcion,
        'roles': roles,
        'roles_opcion': roles_opcion,
    }
    
    return render(request, 'admin_roles/editar_opcion_menu.html', contexto)


@login_required
@requiere_rol('Administrador')
@require_http_methods(['POST'])
def asignar_rol_usuario_ajax(request):
    """
    AJAX para asignar/remover rol a usuario
    """
    usuario_id = request.POST.get('usuario_id')
    rol_id = request.POST.get('rol_id')
    accion = request.POST.get('accion')  # 'asignar' o 'remover'
    
    try:
        usuario = User.objects.get(id=usuario_id)
        rol = Group.objects.get(id=rol_id)
        
        if accion == 'asignar':
            usuario.groups.add(rol)
            mensaje = f'Rol "{rol.name}" asignado a "{usuario.username}"'
        elif accion == 'remover':
            usuario.groups.remove(rol)
            mensaje = f'Rol "{rol.name}" removido de "{usuario.username}"'
        else:
            return JsonResponse({'error': 'Acción inválida'}, status=400)
        
        return JsonResponse({
            'success': True,
            'mensaje': mensaje,
            'roles_usuario': list(usuario.groups.values_list('name', flat=True))
        })
    
    except (User.DoesNotExist, Group.DoesNotExist) as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@requiere_rol('Administrador')
def reporte_acceso(request):
    """
    Reporte de acceso: qué usuarios pueden ver qué opciones
    """
    usuarios = User.objects.prefetch_related('groups').all().order_by('username')
    opciones = MenuItemRol.objects.filter(activo=True).order_by('orden')
    
    # Construir matriz de acceso
    matriz_acceso = []
    for usuario in usuarios:
        acceso_usuario = {
            'usuario': usuario,
            'opciones': []
        }
        for opcion in opciones:
            puede_ver = opcion.puede_ver_usuario(usuario)
            acceso_usuario['opciones'].append({
                'opcion': opcion,
                'puede_ver': puede_ver
            })
        matriz_acceso.append(acceso_usuario)
    
    contexto = {
        'matriz_acceso': matriz_acceso,
        'total_usuarios': usuarios.count(),
        'total_opciones': opciones.count(),
    }
    
    return render(request, 'admin_roles/reporte_acceso.html', contexto)


@login_required
@requiere_rol('Administrador')
def estadisticas_roles(request):
    """
    Estadísticas de roles y acceso
    """
    roles = Group.objects.all()
    
    estadisticas = []
    for rol in roles:
        usuarios_count = rol.user_set.count()
        opciones_count = MenuItemRol.objects.filter(roles_permitidos=rol).count()
        
        estadisticas.append({
            'rol': rol,
            'usuarios': usuarios_count,
            'opciones': opciones_count,
        })
    
    contexto = {
        'estadisticas': estadisticas,
        'total_roles': roles.count(),
        'total_usuarios': User.objects.count(),
        'usuarios_sin_rol': User.objects.filter(groups__isnull=True).count(),
    }
    
    return render(request, 'admin_roles/estadisticas.html', contexto)
