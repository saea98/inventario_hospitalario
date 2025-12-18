"""
Vistas para la Fase 2.2.2: Llegada de Proveedores
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.utils import timezone

from .llegada_models import LlegadaProveedor, ItemLlegada, DocumentoLlegada
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
        llegadas = LlegadaProveedor.objects.select_related('cita__proveedor').all()
        return render(request, "inventario/llegadas/lista_llegadas.html", {"llegadas": llegadas})


class CrearLlegadaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Crea una nueva llegada de proveedor"""
    permission_required = "inventario.add_llegadaproveedor"
    
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
                llegada.proveedor = llegada.cita.proveedor
                timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
                llegada.folio = f"LLEG-{timestamp}"
                llegada.save()
                
                formset.instance = llegada
                formset.save()
                
                messages.success(request, f"Llegada {llegada.folio} creada con éxito.")
                return redirect("logistica:llegadas:detalle_llegada", pk=llegada.pk)
        
        return render(request, "inventario/llegadas/crear_llegada.html", {"form": form, "formset": formset})


class DetalleLlegadaView(LoginRequiredMixin, View):
    """Muestra el detalle de una llegada"""
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor.objects.select_related('cita__proveedor'), pk=pk)
        return render(request, "inventario/llegadas/detalle_llegada.html", {"llegada": llegada})


class ControlCalidadView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Validación de Control de Calidad"""
    permission_required = "inventario.change_llegadaproveedor"
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = ControlCalidadForm(instance=llegada)
        return render(request, "inventario/llegadas/control_calidad.html", {"llegada": llegada, "form": form})
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = ControlCalidadForm(request.POST, instance=llegada)
        
        if form.is_valid():
            with transaction.atomic():
                llegada = form.save(commit=False)
                llegada.usuario_calidad = request.user
                llegada.fecha_validacion_calidad = timezone.now()
                llegada.estado = "FACTURACION" if llegada.estado_calidad == "APROBADO" else "RECHAZADA"
                llegada.save()
                
                messages.success(request, f"Control de calidad para {llegada.folio} completado.")
                return redirect("logistica:llegadas:detalle_llegada", pk=llegada.pk)
        
        return render(request, "inventario/llegadas/control_calidad.html", {"llegada": llegada, "form": form})


class FacturacionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Captura de datos de Facturación"""
    permission_required = "inventario.change_llegadaproveedor"
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = FacturacionForm(instance=llegada)
        formset = ItemFacturacionFormSet(instance=llegada, prefix="items")
        return render(request, "inventario/llegadas/facturacion.html", {"llegada": llegada, "form": form, "formset": formset})
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = FacturacionForm(request.POST, instance=llegada)
        formset = ItemFacturacionFormSet(request.POST, instance=llegada, prefix="items")
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                llegada = form.save(commit=False)
                llegada.usuario_facturacion = request.user
                llegada.fecha_facturacion = timezone.now()
                llegada.estado = "VALIDACION"
                llegada.save()
                
                formset.save()
                
                messages.success(request, f"Datos de facturación para {llegada.folio} guardados.")
                return redirect("logistica:llegadas:detalle_llegada", pk=llegada.pk)
        
        return render(request, "inventario/llegadas/facturacion.html", {"llegada": llegada, "form": form, "formset": formset})


class SupervisionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Validación de Supervisión"""
    permission_required = "inventario.change_llegadaproveedor"
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = SupervisionForm(instance=llegada)
        return render(request, "inventario/llegadas/supervision.html", {"llegada": llegada, "form": form})
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = SupervisionForm(request.POST, instance=llegada)
        
        if form.is_valid():
            with transaction.atomic():
                llegada = form.save(commit=False)
                llegada.usuario_supervision = request.user
                llegada.fecha_supervision = timezone.now()
                llegada.estado = "UBICACION" if llegada.estado_supervision == "VALIDADO" else "RECHAZADA"
                llegada.save()
                
                messages.success(request, f"Supervisión para {llegada.folio} completada.")
                return redirect("logistica:llegadas:detalle_llegada", pk=llegada.pk)
        
        return render(request, "inventario/llegadas/supervision.html", {"llegada": llegada, "form": form})


class UbicacionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Asignación de ubicación en Almacén"""
    permission_required = "inventario.add_lote"
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        formset = UbicacionFormSet(llegada=llegada)
        items = list(llegada.items.all())
        # Emparejar items con formularios
        items_forms = list(zip(items, formset.forms))
        return render(request, "inventario/llegadas/ubicacion.html", {"llegada": llegada, "formset": formset, "items": items, "items_forms": items_forms})
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        formset = UbicacionFormSet(request.POST, llegada=llegada)
        
        if formset.is_valid():
            with transaction.atomic():
                from django.apps import apps
                Lote = apps.get_model('inventario', 'Lote')
                
                items = list(llegada.items.all())
                for i, form in enumerate(formset.forms):
                    if i < len(items) and form.is_valid():
                        item = items[i]
                        almacen = form.cleaned_data.get('almacen')
                        ubicacion = form.cleaned_data.get('ubicacion')
                        
                        # Si el lote ya existe, actualizar; si no, crear
                        if item.lote_creado:
                            # Actualizar lote existente
                            lote = item.lote_creado
                            lote.almacen = almacen
                            lote.ubicacion = ubicacion
                            lote.save()
                        else:
                            # Crear nuevo lote
                            lote = Lote.objects.create(
                                producto=item.producto,
                                numero_lote=item.numero_lote,
                                fecha_caducidad=item.fecha_caducidad,
                                cantidad_inicial=item.cantidad_recibida,
                                cantidad_disponible=item.cantidad_recibida,
                                almacen=almacen,
                                ubicacion=ubicacion,
                                estado=1,  # 1 = Disponible
                                institucion=llegada.cita.almacen.institucion,  # Obtener institución del almacén de la cita
                                fecha_recepcion=llegada.fecha_llegada_real.date(),
                                precio_unitario=item.precio_unitario_sin_iva or 0,
                                valor_total=(item.precio_unitario_sin_iva or 0) * item.cantidad_recibida,
                                remision=llegada.remision,
                            )
                            item.lote_creado = lote
                            item.save()
                
                llegada.usuario_ubicacion = request.user
                llegada.fecha_ubicacion = timezone.now()
                llegada.estado = "APROBADA"
                llegada.save()
                
                messages.success(request, f"Ubicación para {llegada.folio} asignada con éxito.")
                return redirect("logistica:llegadas:detalle_llegada", pk=llegada.pk)
        
        items = list(llegada.items.all())
        # Emparejar items con formularios
        items_forms = list(zip(items, formset.forms))
        return render(request, "inventario/llegadas/ubicacion.html", {"llegada": llegada, "formset": formset, "items": items, "items_forms": items_forms})


class SubirDocumentoView(LoginRequiredMixin, View):
    """Sube un documento adjunto a la llegada"""
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = DocumentoLlegadaForm(request.POST, request.FILES)
        
        if form.is_valid():
            documento = form.save(commit=False)
            documento.llegada = llegada
            documento.save()
            messages.success(request, f"Documento {documento.get_tipo_documento_display()} subido con éxito.")
        else:
            messages.error(request, "Error al subir el documento.")
            
        return redirect("logistica:llegadas:detalle_llegada", pk=llegada.pk)


# API para obtener productos en formato JSON
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def api_productos(request):
    """API que devuelve los productos disponibles en formato JSON"""
    from django.apps import apps
    Producto = apps.get_model('inventario', 'Producto')
    
    productos = Producto.objects.all().values('id', 'descripcion', 'cns').order_by('descripcion')
    return JsonResponse(list(productos), safe=False)
