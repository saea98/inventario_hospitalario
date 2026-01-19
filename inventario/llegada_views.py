"""
Vistas para la Fase 2.2.2: Llegada de Proveedores
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .access_control import requiere_rol

from .llegada_models import LlegadaProveedor, ItemLlegada, DocumentoLlegada
from .models import Almacen
from .llegada_forms import (
    LlegadaProveedorForm,
    ItemLlegadaFormSet,
    ControlCalidadForm,
    FacturacionForm,
    ItemFacturacionFormSet,
    SupervisionForm,
    UbicacionFormSet,
    DocumentoLlegadaForm,
)


class ListaLlegadasView(LoginRequiredMixin, View):
    """Muestra la lista de llegadas de proveedores"""
    
    def get(self, request):
        llegadas = LlegadaProveedor.objects.select_related('proveedor').all()
        return render(request, "inventario/llegadas/lista_llegadas.html", {"llegadas": llegadas})


class CrearLlegadaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Crea una nueva llegada de proveedor"""
    permission_required = 'inventario.add_llegadaproveedor'
    
    def get(self, request):
        form = LlegadaProveedorForm()
        formset = ItemLlegadaFormSet(prefix="items")
        return render(request, "inventario/llegadas/crear_llegada.html", {"form": form, "formset": formset})
    
    def post(self, request):
        form = LlegadaProveedorForm(request.POST)
        formset = ItemLlegadaFormSet(request.POST, prefix="items")
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                llegada = form.save(commit=False)
                llegada.creado_por = request.user
                llegada.save()
                
                formset.instance = llegada
                formset.save()
                
                messages.success(request, f"Llegada {llegada.folio} creada exitosamente")
                return redirect('logistica:llegadas:detalle_llegada', pk=llegada.pk)
        
        return render(request, "inventario/llegadas/crear_llegada.html", {"form": form, "formset": formset})


class DetalleLlegadaView(LoginRequiredMixin, View):
    """Muestra el detalle de una llegada"""
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        return render(request, "inventario/llegadas/detalle_llegada.html", {"llegada": llegada})


class ControlCalidadView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Control de calidad de la llegada"""
    permission_required = 'inventario.change_llegadaproveedor'
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = ControlCalidadForm(instance=llegada)
        return render(request, "inventario/llegadas/control_calidad.html", {"llegada": llegada, "form": form})
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = ControlCalidadForm(request.POST, instance=llegada)
        
        if form.is_valid():
            llegada = form.save(commit=False)
            llegada.usuario_calidad = request.user
            llegada.fecha_validacion_calidad = timezone.now()
            llegada.save()
            messages.success(request, "Control de calidad registrado")
            return redirect('logistica:llegadas:detalle_llegada', pk=llegada.pk)
        
        return render(request, "inventario/llegadas/control_calidad.html", {"llegada": llegada, "form": form})


class FacturacionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Captura de datos de facturación"""
    permission_required = 'inventario.change_llegadaproveedor'
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = FacturacionForm(instance=llegada)
        formset = ItemFacturacionFormSet(instance=llegada)
        return render(request, "inventario/llegadas/facturacion.html", {
            "llegada": llegada,
            "form": form,
            "formset": formset
        })
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = FacturacionForm(request.POST, instance=llegada)
        formset = ItemFacturacionFormSet(request.POST, instance=llegada)
        
        if form.is_valid() and formset.is_valid():
            llegada = form.save(commit=False)
            llegada.usuario_facturacion = request.user
            llegada.save()
            formset.save()
            messages.success(request, "Datos de facturación guardados")
            return redirect('logistica:llegadas:detalle_llegada', pk=llegada.pk)
        
        return render(request, "inventario/llegadas/facturacion.html", {
            "llegada": llegada,
            "form": form,
            "formset": formset
        })


class SupervisionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Supervisión de la llegada"""
    permission_required = 'inventario.change_llegadaproveedor'
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = SupervisionForm(instance=llegada)
        return render(request, "inventario/llegadas/supervision.html", {"llegada": llegada, "form": form})
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = SupervisionForm(request.POST, instance=llegada)
        
        if form.is_valid():
            llegada = form.save(commit=False)
            llegada.usuario_supervision = request.user
            llegada.fecha_supervision = timezone.now()
            llegada.save()
            messages.success(request, "Supervisión registrada")
            return redirect('logistica:llegadas:detalle_llegada', pk=llegada.pk)
        
        return render(request, "inventario/llegadas/supervision.html", {"llegada": llegada, "form": form})


class UbicacionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Asignación de ubicación de lotes"""
    permission_required = 'inventario.change_llegadaproveedor'
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        return render(request, "inventario/llegadas/ubicacion.html", {"llegada": llegada})
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        llegada.usuario_ubicacion = request.user
        llegada.fecha_ubicacion = timezone.now()
        llegada.save()
        messages.success(request, "Ubicación registrada")
        return redirect('logistica:llegadas:detalle_llegada', pk=llegada.pk)


class SubirDocumentoView(LoginRequiredMixin, View):
    """Subir documentos adjuntos"""
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = DocumentoLlegadaForm(request.POST, request.FILES)
        
        if form.is_valid():
            documento = form.save(commit=False)
            documento.llegada = llegada
            documento.save()
            messages.success(request, "Documento subido exitosamente")
        
        return redirect('logistica:llegadas:detalle_llegada', pk=llegada.pk)


# API para obtener productos en formato JSON
@require_GET
def api_productos(request):
    """API que devuelve los productos disponibles en formato JSON"""
    from django.apps import apps
    Producto = apps.get_model('inventario', 'Producto')
    
    productos = Producto.objects.all().order_by('descripcion')
    data = []
    for producto in productos:
        data.append({
            'id': producto.id,
            'clave_cnis': producto.clave_cnis,
            'descripcion': f"{producto.clave_cnis} - {producto.descripcion[:50]}...",
            'iva': float(producto.iva)
        })
    return JsonResponse(data, safe=False)


@require_GET
def api_ubicaciones_por_almacen(request):
    """
    API que devuelve las ubicaciones disponibles para un almacén específico.
    Parámetro GET: almacen_id
    """
    from django.apps import apps
    UbicacionAlmacen = apps.get_model('inventario', 'UbicacionAlmacen')
    
    almacen_id = request.GET.get('almacen_id')
    
    if not almacen_id:
        return JsonResponse({'error': 'almacen_id es requerido'}, status=400)
    
    try:
        almacen_id = int(almacen_id)
    except ValueError:
        return JsonResponse({'error': 'almacen_id debe ser un número'}, status=400)
    
    ubicaciones = UbicacionAlmacen.objects.filter(
        almacen_id=almacen_id
    ).values('id', 'codigo', 'descripcion').order_by('codigo')
    
    return JsonResponse({
        'ubicaciones': list(ubicaciones)
    })


@require_GET
def api_cita_folio(request, cita_id):
    """
    API que devuelve los datos de una cita específica.
    URL: /logistica/llegadas/api/cita/<cita_id>/folio/
    Devuelve: folio, remisión, orden de suministro, almacén
    """
    try:
        from django.apps import apps
        CitaProveedor = apps.get_model('inventario', 'CitaProveedor')
        
        cita = CitaProveedor.objects.get(id=cita_id)
        
        return JsonResponse({
            'folio': cita.folio or f"TEMP-{cita_id}",
            'remision': cita.numero_orden_remision or '',
            'orden_suministro': cita.numero_orden_suministro or '',
            'contrato': cita.numero_contrato or '',
            'almacen_id': cita.almacen_id or '',
            'proveedor_id': cita.proveedor_id or '',
            'clave_medicamento': cita.clave_medicamento or '',
            'cita_id': cita_id
        })
    except Exception as e:
        return JsonResponse({'error': 'Cita no encontrada'}, status=404)
