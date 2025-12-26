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
from .access_control import requiere_rol

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
        llegadas = LlegadaProveedor.objects.select_related('proveedor').all()
        return render(request, "inventario/llegadas/lista_llegadas.html", {"llegadas": llegadas})


class CrearLlegadaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Crea una nueva llegada de proveedor"""
    
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
                # Asignar proveedor desde la cita
                if llegada.cita and llegada.cita.proveedor:
                    llegada.proveedor_id = llegada.cita.proveedor_id
                timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
                llegada.folio = f"LLEG-{timestamp}"
                llegada.save()
                
                # Cambiar estado de la cita a Completada
                if llegada.cita:
                    llegada.cita.estado = 'completada'
                    llegada.cita.save()
                
                formset.instance = llegada
                formset.save()
                
                messages.success(request, f"Llegada {llegada.folio} creada con éxito.")
                return redirect("logistica:llegadas:detalle_llegada", pk=llegada.pk)
        
        return render(request, "inventario/llegadas/crear_llegada.html", {"form": form, "formset": formset})


class DetalleLlegadaView(LoginRequiredMixin, View):
    """Muestra el detalle de una llegada"""
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor.objects.select_related('proveedor'), pk=pk)
        return render(request, "inventario/llegadas/detalle_llegada.html", {"llegada": llegada})


@method_decorator(requiere_rol('Control de Calidad'), name='dispatch')
class ControlCalidadView(LoginRequiredMixin, View):
    """Validación de Control de Calidad"""
    
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


@method_decorator(requiere_rol('Facturacion'), name='dispatch')
class FacturacionView(LoginRequiredMixin, View):
    """Captura de datos de Facturación"""
    
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


@method_decorator(requiere_rol('Supervisor'), name='dispatch')
class SupervisionView(LoginRequiredMixin, View):
    """Validación de Supervisión"""
    
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


@method_decorator(requiere_rol('Almacen'), name='dispatch')
class UbicacionView(LoginRequiredMixin, View):
    """Asignación de ubicación en Almacén"""
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        formset = UbicacionFormSet(llegada=llegada, user=request.user)
        items = list(llegada.items.all())
        # Emparejar items con formularios
        items_forms = list(zip(items, formset.forms))
        return render(request, "inventario/llegadas/ubicacion.html", {"llegada": llegada, "formset": formset, "items": items, "items_forms": items_forms})
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        formset = UbicacionFormSet(request.POST, llegada=llegada, user=request.user)
        
        if formset.is_valid():
            with transaction.atomic():
                from django.apps import apps
                Lote = apps.get_model('inventario', 'Lote')
                LoteUbicacion = apps.get_model('inventario', 'LoteUbicacion')
                
                items = list(llegada.items.all())
                
                for i, form in enumerate(formset.forms):
                    if i < len(items) and form.is_valid():
                        item = items[i]
                        almacen = form.cleaned_data.get('almacen')
                        
                        # Obtener los formularios de ubicación para este item
                        ubicacion_forms = formset.get_ubicacion_forms(i)
                        
                        # Validar que la suma de cantidades sea igual a la cantidad recibida
                        total_cantidad = sum(
                            int(uf.cleaned_data.get('cantidad', 0))
                            for uf in ubicacion_forms
                            if uf.is_valid()
                        )
                        
                        if total_cantidad != item.cantidad_recibida:
                            messages.error(
                                request,
                                f"Para el item {item.producto.clave_cnis}: "
                                f"La suma de cantidades ({total_cantidad}) debe ser igual "
                                f"a la cantidad recibida ({item.cantidad_recibida})"
                            )
                            return redirect("logistica:llegadas:ubicacion", pk=llegada.pk)
                        
                        # Si el lote ya existe, actualizar; si no, crear
                        if item.lote_creado:
                            lote = item.lote_creado
                            lote.almacen = almacen
                            lote.save()
                            
                            # Eliminar ubicaciones anteriores y crear las nuevas
                            lote.ubicaciones_detalle.all().delete()
                        else:
                            # Crear nuevo lote
                            lote = Lote.objects.create(
                                producto=item.producto,
                                numero_lote=item.numero_lote,
                                fecha_caducidad=item.fecha_caducidad,
                                cantidad_inicial=item.cantidad_recibida,
                                cantidad_disponible=item.cantidad_recibida,
                                almacen=almacen,
                                estado=1,  # 1 = Disponible
                                institucion=llegada.cita.almacen.institucion,
                                fecha_recepcion=llegada.fecha_llegada_real.date(),
                                precio_unitario=item.precio_unitario_sin_iva or 0,
                                valor_total=(item.precio_unitario_sin_iva or 0) * item.cantidad_recibida,
                                remision=llegada.remision,
                            )
                            item.lote_creado = lote
                            item.save()
                        
                        # Crear registros de LoteUbicacion para cada ubicación
                        for ubicacion_form in ubicacion_forms:
                            if ubicacion_form.is_valid():
                                ubicacion = ubicacion_form.cleaned_data.get('ubicacion')
                                cantidad = ubicacion_form.cleaned_data.get('cantidad')
                                
                                # Crear o actualizar LoteUbicacion
                                lote_ubicacion, created = LoteUbicacion.objects.update_or_create(
                                    lote=lote,
                                    ubicacion=ubicacion,
                                    defaults={
                                        'cantidad': cantidad,
                                        'usuario_asignacion': request.user,
                                    }
                                )
                
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
