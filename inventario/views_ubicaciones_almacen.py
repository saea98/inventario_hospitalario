"""
Vistas para gestionar Ubicaciones de Almacén (UbicacionAlmacen).
Permite listar, crear y editar ubicaciones sin requerir acceso al admin de Django.
Control de acceso por roles (no solo superusuario).
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import UbicacionAlmacen, Almacen
from .forms import UbicacionAlmacenForm
from .access_control import requiere_rol


@requiere_rol('Administrador', 'Gestor de Inventario', 'Almacenero', 'Supervisión')
def lista_ubicaciones_almacen(request):
    """
    Lista de ubicaciones de almacén con filtros por almacén y búsqueda por código.
    """
    qs = UbicacionAlmacen.objects.select_related('almacen').order_by('almacen__nombre', 'codigo')

    almacen_id = request.GET.get('almacen')
    search = request.GET.get('search')
    activo = request.GET.get('activo')

    if almacen_id:
        qs = qs.filter(almacen_id=almacen_id)
    if search:
        qs = qs.filter(
            Q(codigo__icontains=search) |
            Q(descripcion__icontains=search) |
            Q(nivel__icontains=search) |
            Q(pasillo__icontains=search) |
            Q(rack__icontains=search)
        )
    if activo is not None:
        if activo == '1':
            qs = qs.filter(activo=True)
        elif activo == '0':
            qs = qs.filter(activo=False)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'almacenes': Almacen.objects.filter(activo=True).order_by('nombre'),
        'almacen_selected': almacen_id,
        'search': search,
        'activo_selected': activo,
    }
    return render(request, 'inventario/ubicaciones_almacen/lista.html', context)


@requiere_rol('Administrador', 'Gestor de Inventario', 'Almacenero', 'Supervisión')
def crear_ubicacion_almacen(request):
    """Crear una nueva ubicación de almacén."""
    form = UbicacionAlmacenForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Ubicación de almacén creada correctamente.')
        return redirect('lista_ubicaciones_almacen')
    return render(request, 'inventario/ubicaciones_almacen/form.html', {
        'form': form,
        'titulo': 'Nueva Ubicación de Almacén',
    })


@requiere_rol('Administrador', 'Gestor de Inventario', 'Almacenero', 'Supervisión')
def editar_ubicacion_almacen(request, pk):
    """Editar una ubicación de almacén existente."""
    ubicacion = get_object_or_404(UbicacionAlmacen, pk=pk)
    form = UbicacionAlmacenForm(request.POST or None, instance=ubicacion)
    if form.is_valid():
        form.save()
        messages.success(request, 'Ubicación actualizada correctamente.')
        return redirect('lista_ubicaciones_almacen')
    return render(request, 'inventario/ubicaciones_almacen/form.html', {
        'form': form,
        'titulo': f'Editar ubicación {ubicacion.codigo}',
        'ubicacion': ubicacion,
    })
