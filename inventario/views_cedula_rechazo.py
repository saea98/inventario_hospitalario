"""
Vistas para generar cédulas de rechazo
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime

from .models import CitaProveedor, ListaRevision


@login_required
def generar_cedula_rechazo(request, pk):
    """
    Generar cédula de rechazo en HTML imprimible.
    Solo disponible para citas canceladas.
    """
    cita = get_object_or_404(CitaProveedor, pk=pk)
    
    # Verificar que la cita esté cancelada
    if cita.estado != 'cancelada':
        messages.warning(request, 'Solo se pueden generar cédulas para citas canceladas.')
        return redirect('logistica:detalle_cita', pk=pk)
    
    # Obtener lista de revisión
    try:
        lista_revision = ListaRevision.objects.get(cita=cita)
    except ListaRevision.DoesNotExist:
        messages.error(request, 'No se encontró la lista de revisión para esta cita.')
        return redirect('logistica:detalle_cita', pk=pk)
    
    # Preparar datos para la cédula
    context = {
        'cita': cita,
        'lista_revision': lista_revision,
        'fecha': datetime.now().strftime('%d/%m/%y'),
        'almacen': cita.almacen,
        'proveedor': cita.proveedor,
        'folio': cita.folio,
        'motivo': lista_revision.justificacion_rechazo or 'No especificado',
    }
    
    return render(request, 'inventario/citas/cedula_rechazo.html', context)


@login_required
def imprimir_cedula_rechazo(request, pk):
    """
    Generar cédula de rechazo optimizada para impresión PDF.
    """
    cita = get_object_or_404(CitaProveedor, pk=pk)
    
    # Verificar que la cita esté cancelada
    if cita.estado != 'cancelada':
        return HttpResponse('Solo se pueden imprimir cédulas para citas canceladas.', status=400)
    
    # Obtener lista de revisión
    try:
        lista_revision = ListaRevision.objects.get(cita=cita)
    except ListaRevision.DoesNotExist:
        return HttpResponse('No se encontró la lista de revisión.', status=404)
    
    # Preparar datos
    context = {
        'cita': cita,
        'lista_revision': lista_revision,
        'fecha': datetime.now().strftime('%d/%m/%y'),
        'almacen': cita.almacen,
        'proveedor': cita.proveedor,
        'folio': cita.folio,
        'motivo': lista_revision.justificacion_rechazo or 'No especificado',
    }
    
    return render(request, 'inventario/citas/cedula_rechazo_print.html', context)
