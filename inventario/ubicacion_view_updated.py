"""
Vista actualizada para manejar el split de lotes en múltiples ubicaciones.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils import timezone
from django.apps import apps

from .llegada_models import LlegadaProveedor


class UbicacionView(LoginRequiredMixin, View):
    """Asignación de ubicación en Almacén con soporte para split de lotes"""
    
    def get(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        from .llegada_forms_updated import UbicacionFormSet
        formset = UbicacionFormSet(llegada=llegada, user=request.user)
        items = list(llegada.items.all())
        
        # Preparar datos para el template
        items_data = []
        for item_idx, item in enumerate(items):
            ubicacion_forms = formset.get_ubicacion_forms(item_idx)
            items_data.append({
                'item': item,
                'almacen_form': formset.forms[item_idx] if item_idx < len(formset.forms) else None,
                'ubicacion_forms': ubicacion_forms,
            })
        
        return render(request, "inventario/llegadas/ubicacion_split.html", {
            "llegada": llegada,
            "formset": formset,
            "items_data": items_data,
        })
    
    def post(self, request, pk):
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        from .llegada_forms_updated import UbicacionFormSet
        formset = UbicacionFormSet(request.POST, llegada=llegada, user=request.user)
        
        if formset.is_valid():
            with transaction.atomic():
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
        
        # Si hay errores, volver a renderizar el formulario
        items = list(llegada.items.all())
        items_data = []
        for item_idx, item in enumerate(items):
            ubicacion_forms = formset.get_ubicacion_forms(item_idx)
            items_data.append({
                'item': item,
                'almacen_form': formset.forms[item_idx] if item_idx < len(formset.forms) else None,
                'ubicacion_forms': ubicacion_forms,
            })
        
        return render(request, "inventario/llegadas/ubicacion_split.html", {
            "llegada": llegada,
            "formset": formset,
            "items_data": items_data,
        })
