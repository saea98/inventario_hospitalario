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


class EditarLlegadaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Edita una llegada existente"""
    permission_required = 'inventario.change_llegadaproveedor'
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        if not llegada.puede_editar_recepcion():
            messages.error(request, "No se puede editar esta llegada en su estado actual")
            return redirect('logistica:llegadas:detalle_llegada', pk=pk)
        
        form = LlegadaProveedorForm(instance=llegada)
        formset = ItemLlegadaFormSet(instance=llegada, prefix="items")
        return render(request, "inventario/llegadas/editar_llegada.html", {"form": form, "formset": formset, "llegada": llegada})
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        if not llegada.puede_editar_recepcion():
            messages.error(request, "No se puede editar esta llegada en su estado actual")
            return redirect('logistica:llegadas:detalle_llegada', pk=pk)
        
        form = LlegadaProveedorForm(request.POST, instance=llegada)
        formset = ItemLlegadaFormSet(request.POST, instance=llegada, prefix="items")
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
                messages.success(request, f"Llegada {llegada.folio} actualizada exitosamente")
                return redirect('logistica:llegadas:detalle_llegada', pk=llegada.pk)
        
        return render(request, "inventario/llegadas/editar_llegada.html", {"form": form, "formset": formset, "llegada": llegada})


class AprobarEntradaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Aprueba la entrada de una llegada"""
    permission_required = 'inventario.change_llegadaproveedor'
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        if not llegada.puede_editar_recepcion():
            messages.error(request, "No se puede aprobar esta llegada en su estado actual")
            return redirect('logistica:llegadas:detalle_llegada', pk=pk)
        
        llegada.estado = 'CONTROL_CALIDAD'
        llegada.save()
        messages.success(request, f"Llegada {llegada.folio} aprobada. Pendiente de validacion de calidad")
        return redirect('logistica:llegadas:detalle_llegada', pk=pk)


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
        from django.db import transaction
        from .models import Lote
        
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        form = ControlCalidadForm(request.POST, instance=llegada)
        
        if form.is_valid():
            with transaction.atomic():
                llegada = form.save(commit=False)
                llegada.usuario_calidad = request.user
                llegada.fecha_validacion_calidad = timezone.now()
                
                # Si se aprueba la inspeccion visual, cambiar estado a UBICACION y crear lotes
                if llegada.estado_calidad == 'APROBADO':
                    llegada.estado = 'UBICACION'
                    llegada.save()
                    
                    # Crear lotes para cada item si no existen
                    for item in llegada.items.all():
                        if not item.lote_creado:
                            from .models import Institucion
                            # Obtener la institucion (usar la primera disponible)
                            institucion = Institucion.objects.first()
                            
                            lote = Lote.objects.create(
                                producto=item.producto,
                                numero_lote=item.numero_lote,
                                fecha_caducidad=item.fecha_caducidad,
                                fecha_fabricacion=item.fecha_elaboracion,
                                cantidad_inicial=item.cantidad_recibida,
                                cantidad_disponible=item.cantidad_recibida,
                                cantidad_reservada=0,
                                almacen=llegada.almacen,
                                institucion=institucion,
                                precio_unitario=item.precio_unitario_sin_iva or 0,
                                valor_total=(item.precio_unitario_sin_iva or 0) * item.cantidad_recibida,
                                fecha_recepcion=llegada.fecha_llegada_real.date(),
                                estado=1
                            )
                            item.lote_creado = lote
                            item.save()
                    
                    messages.success(request, "Inspeccion visual aprobada. Lotes creados. Pendiente de asignacion de ubicacion")
                else:
                    llegada.save()
                    messages.warning(request, "Inspeccion visual rechazada")
            
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
        from .models import Almacen
        import logging
        logger = logging.getLogger(__name__)
        
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        items = list(llegada.items.all())
        
        logger.info(f"DEBUG: Llegada {llegada.pk} - Estado: {llegada.estado}")
        logger.info(f"DEBUG: Total de items: {len(items)}")
        for idx, item in enumerate(items):
            logger.info(f"DEBUG: Item {idx} - Lote creado: {item.lote_creado}")
        
        # Obtener almacenes disponibles
        almacenes = Almacen.objects.all()
        
        # Preparar datos para el template
        items_with_ubicaciones = []
        for idx, item in enumerate(items):
            items_with_ubicaciones.append({
                'producto': item.producto,
                'lote': item.lote_creado,
                'cantidad_recibida': item.cantidad_recibida,
                'index': idx
            })
        
        logger.info(f"DEBUG: Items con ubicaciones preparados: {len(items_with_ubicaciones)}")
        
        return render(request, "inventario/llegadas/ubicacion.html", {
            "llegada": llegada,
            "items_with_ubicaciones": items_with_ubicaciones,
            "almacenes": almacenes
        })
    
    def post(self, request, pk):
        from .models import Almacen, Lote, LoteUbicacion, UbicacionAlmacen, MovimientoInventario
        
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        items = list(llegada.items.all())
        
        try:
            with transaction.atomic():
                for i, item in enumerate(items):
                    almacen_id = request.POST.get(f'ubicacion-detalle-{i}-0-almacen')
                    
                    if not almacen_id:
                        messages.error(request, f"Debe seleccionar un almacén para {item.producto.descripcion}")
                        return redirect("logistica:llegadas:ubicacion", pk=llegada.pk)
                    
                    almacen = get_object_or_404(Almacen, pk=almacen_id)
                    
                    # Procesar ubicaciones desde POST
                    ubicacion_data = []
                    j = 0
                    while True:
                        ubicacion_id_key = f'ubicacion-detalle-{i}-{j}-ubicacion'
                        cantidad_key = f'ubicacion-detalle-{i}-{j}-cantidad'
                        
                        if ubicacion_id_key not in request.POST:
                            break
                        
                        ubicacion_id = request.POST.get(ubicacion_id_key)
                        cantidad_str = request.POST.get(cantidad_key, '0')
                        
                        if ubicacion_id and cantidad_str:
                            try:
                                cantidad = int(cantidad_str)
                                if cantidad > 0:
                                    ubicacion_data.append({
                                        'ubicacion_id': ubicacion_id,
                                        'cantidad': cantidad
                                    })
                            except ValueError:
                                pass
                        j += 1
                    
                    # Validar que hay al menos una ubicación
                    if not ubicacion_data:
                        messages.error(request, f"Debe asignar al menos una ubicación para {item.producto.descripcion}")
                        return redirect("logistica:llegadas:ubicacion", pk=llegada.pk)
                    
                    # Validar que la suma de cantidades sea igual a la cantidad recibida
                    total_cantidad = sum(u['cantidad'] for u in ubicacion_data)
                    if total_cantidad != item.cantidad_recibida:
                        messages.error(
                            request,
                            f"Para {item.producto.descripcion}: La suma de cantidades ({total_cantidad}) "
                            f"debe ser igual a la cantidad recibida ({item.cantidad_recibida})"
                        )
                        return redirect("logistica:llegadas:ubicacion", pk=llegada.pk)
                    
                    # Si el lote ya existe, actualizar; si no, crear
                    if item.lote_creado:
                        lote = item.lote_creado
                        lote.almacen = almacen
                        lote.save()
                        # Eliminar ubicaciones anteriores
                        lote.ubicaciones_detalle.all().delete()
                    else:
                        # Crear nuevo lote (fallback si no se creó en Control de Calidad)
                        from .models import Institucion
                        institucion = Institucion.objects.first()
                        lote = Lote.objects.create(
                            producto=item.producto,
                            numero_lote=item.numero_lote,
                            fecha_caducidad=item.fecha_caducidad,
                            fecha_fabricacion=item.fecha_elaboracion,
                            cantidad_inicial=item.cantidad_recibida,
                            cantidad_disponible=item.cantidad_recibida,
                            cantidad_reservada=0,
                            almacen=almacen,
                            institucion=institucion,
                            precio_unitario=item.precio_unitario_sin_iva or 0,
                            valor_total=(item.precio_unitario_sin_iva or 0) * item.cantidad_recibida,
                            fecha_recepcion=llegada.fecha_llegada_real.date(),
                            estado=1
                        )
                        item.lote_creado = lote
                        item.save()
                    
                    # Crear registros de LoteUbicacion para cada ubicación
                    for ubi_data in ubicacion_data:
                        ubicacion = get_object_or_404(UbicacionAlmacen, pk=ubi_data['ubicacion_id'])
                        LoteUbicacion.objects.create(
                            lote=lote,
                            ubicacion=ubicacion,
                            cantidad=ubi_data['cantidad'],
                            usuario_asignacion=request.user
                        )
                    
                    # Crear movimiento de entrada en inventario
                    MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento='ENTRADA',
                        cantidad=item.cantidad_recibida,
                        cantidad_anterior=0,
                        cantidad_nueva=item.cantidad_recibida,
                        motivo=f'Entrada de proveedor - Folio: {llegada.folio}',
                        documento_referencia=llegada.remision,
                        contrato=llegada.numero_contrato,
                        remision=llegada.remision,
                        folio=llegada.folio,
                        usuario=request.user
                    )
                
                # Marcar llegada como completada
                llegada.estado = 'APROBADA'
                llegada.usuario_ubicacion = request.user
                llegada.fecha_ubicacion = timezone.now()
                llegada.save()
                
                messages.success(request, "Ubicaciones asignadas correctamente")
                return redirect('logistica:llegadas:detalle_llegada', pk=llegada.pk)
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al asignar ubicaciones: {str(e)}", exc_info=True)
            messages.error(request, f"Error al asignar ubicaciones: {str(e)}")
            return redirect("logistica:llegadas:ubicacion", pk=llegada.pk)


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
