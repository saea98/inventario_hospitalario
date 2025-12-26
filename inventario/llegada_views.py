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
        import logging
        logger = logging.getLogger(__name__)
        
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        items = list(llegada.items.all())
        
        # Obtener almacenes disponibles
        almacenes = Almacen.objects.all()
        logger.warning(f'DEBUG: Total almacenes: {almacenes.count()}')
        for a in almacenes:
            logger.warning(f'DEBUG: Almacén - {a.nombre} ({a.id})')
        
        # Preparar datos para el template
        from .models import LoteUbicacion
        items_with_ubicaciones = []
        for idx, item in enumerate(items):
            # Obtener ubicaciones previamente asignadas para este lote
            ubicaciones_asignadas = []
            if item.lote_creado:
                ubicaciones_asignadas = list(LoteUbicacion.objects.filter(lote=item.lote_creado).values(
                    'id', 'ubicacion_id', 'ubicacion__almacen_id', 'cantidad'
                ))
            
            items_with_ubicaciones.append({
                'producto': item.producto,
                'lote': item.lote_creado,
                'cantidad_recibida': item.cantidad_recibida,
                'index': idx,
                'ubicaciones_asignadas': ubicaciones_asignadas
            })
        
        return render(request, "inventario/llegadas/ubicacion.html", {
            "llegada": llegada,
            "items_with_ubicaciones": items_with_ubicaciones,
            "almacenes": almacenes
        })
    
    def post(self, request, pk):
        import logging
        logger = logging.getLogger(__name__)
        from .models import Almacen, Lote, LoteUbicacion, UbicacionAlmacen

        logger.warning('--- INICIO PROCESO DE UBICACIÓN ---')
        logger.warning(f'POST data: {request.POST}')
        
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        items = list(llegada.items.all())
        
        try:
            with transaction.atomic():
                for i, item in enumerate(items):
                    logger.warning(f'Procesando item #{i}: {item.producto.descripcion}')
                    almacen_id = request.POST.get(f'ubicacion-detalle-{i}-0-almacen')
                    
                    if not almacen_id:
                        messages.error(request, f"Debe seleccionar un almacén para {item.producto.descripcion}")
                        return redirect("logistica:llegadas:ubicacion", pk=llegada.pk)
                    
                    almacen = get_object_or_404(Almacen, pk=almacen_id)
                    
                    # Procesar ubicaciones desde POST
                    ubicacion_data = []
                    j = 0
                    logger.warning(f'POST keys para item {i}: {[k for k in request.POST.keys() if f"ubicacion-detalle-{i}" in k]}')
                    while True:
                        ubicacion_id_key = f'ubicacion-detalle-{i}-{j}-ubicacion'
                        cantidad_key = f'ubicacion-detalle-{i}-{j}-cantidad'
                        
                        logger.warning(f'Buscando clave de ubicación: {ubicacion_id_key}')
                        if ubicacion_id_key not in request.POST:
                            logger.warning(f'Clave no encontrada, deteniendo búsqueda en j={j}')
                            break
                        
                        ubicacion_id = request.POST.get(ubicacion_id_key)
                        cantidad_str = request.POST.get(cantidad_key, '0')
                        
                        if ubicacion_id and cantidad_str:
                            try:
                                cantidad = int(cantidad_str)
                                if cantidad > 0:
                                    logger.warning(f'Agregando ubicación {ubicacion_id} con cantidad {cantidad}')
                                    ubicacion_data.append({
                                        'ubicacion_id': ubicacion_id,
                                        'cantidad': cantidad
                                    })
                                else:
                                    logger.warning(f'Cantidad {cantidad_str} no es mayor a 0')
                            except ValueError as e:
                                logger.warning(f'Error al convertir cantidad {cantidad_str}: {e}')
                        else:
                            logger.warning(f'ubicacion_id={ubicacion_id}, cantidad_str={cantidad_str}')
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
                        # Crear nuevo lote
                        lote = Lote.objects.create(
                            producto=item.producto,
                            numero_lote=item.numero_lote,
                            fecha_caducidad=item.fecha_caducidad,
                            cantidad_inicial=item.cantidad_recibida,
                            cantidad_disponible=item.cantidad_recibida,
                            almacen=almacen,
                            estado=1,
                            institucion=llegada.cita.almacen.institucion,
                            fecha_recepcion=llegada.fecha_llegada_real.date() if llegada.fecha_llegada_real else timezone.now().date(),
                            precio_unitario=item.precio_unitario_sin_iva or 0,
                            valor_total=(item.precio_unitario_sin_iva or 0) * item.cantidad_recibida,
                            remision=llegada.remision,
                        )
                        item.lote_creado = lote
                        item.save()
                    
                    # Crear registros de LoteUbicacion para cada ubicación
                    for ubi_data in ubicacion_data:
                        ubicacion = get_object_or_404(UbicacionAlmacen, pk=ubi_data['ubicacion_id'])
                        logger.warning(f'Creando LoteUbicacion para lote {lote.id}, ubicacion {ubicacion.id}, cantidad {ubi_data["cantidad"]}')
                        LoteUbicacion.objects.create(
                            lote=lote,
                            ubicacion=ubicacion,
                            cantidad=ubi_data['cantidad'],
                            usuario_asignacion=request.user,
                            fecha_asignacion=timezone.now()
                        )
                
                # Marcar llegada como completada
                llegada.estado = 'ubicacion_asignada'
                llegada.save()
                
                logger.warning('--- FIN PROCESO DE UBICACIÓN: ÉXITO ---')
                messages.success(request, "Ubicaciones asignadas correctamente")
                return redirect("logistica:llegadas:detalle_llegada", pk=llegada.pk)
        
        except Exception as e:
            logger.error(f'Error en la vista de ubicación: {str(e)}', exc_info=True)
            messages.error(request, f"Error al asignar ubicaciones: {str(e)}")
            return redirect("logistica:llegadas:ubicacion", pk=llegada.pk)


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
