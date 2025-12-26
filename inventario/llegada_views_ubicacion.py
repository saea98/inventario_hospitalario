# Vista UbicacionView actualizada

class UbicacionView(LoginRequiredMixin, View):
    """Asignación de ubicación en Almacén"""
    
    def get(self, request, pk):
        from .models import Almacen
        
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        items = list(llegada.items.all())
        
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
        
        return render(request, "inventario/llegadas/ubicacion.html", {
            "llegada": llegada,
            "items_with_ubicaciones": items_with_ubicaciones,
            "almacenes": almacenes
        })
    
    def post(self, request, pk):
        from .models import Almacen, Lote, LoteUbicacion, UbicacionAlmacen
        
        llegada = get_object_or_404(LlegadaProveedor, pk=pk)
        items = list(llegada.items.all())
        
        try:
            with transaction.atomic():
                for i, item in enumerate(items):
                    almacen_id = request.POST.get(f'ubicacion-detalle-{i}-0-almacen')
                    
                    if not almacen_id:
                        messages.error(request, f"Debe seleccionar un almacén para {item.producto.nombre}")
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
                        messages.error(request, f"Debe asignar al menos una ubicación para {item.producto.nombre}")
                        return redirect("logistica:llegadas:ubicacion", pk=llegada.pk)
                    
                    # Validar que la suma de cantidades sea igual a la cantidad recibida
                    total_cantidad = sum(u['cantidad'] for u in ubicacion_data)
                    if total_cantidad != item.cantidad_recibida:
                        messages.error(
                            request,
                            f"Para {item.producto.nombre}: La suma de cantidades ({total_cantidad}) "
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
                        LoteUbicacion.objects.create(
                            lote=lote,
                            ubicacion=ubicacion,
                            cantidad=ubi_data['cantidad'],
                            asignado_por=request.user,
                            fecha_asignacion=timezone.now()
                        )
                
                # Marcar llegada como completada
                llegada.estado = 'ubicacion_asignada'
                llegada.save()
                
                messages.success(request, "Ubicaciones asignadas correctamente")
                return redirect("logistica:llegadas:detalle_llegada", pk=llegada.pk)
        
        except Exception as e:
            messages.error(request, f"Error al asignar ubicaciones: {str(e)}")
            return redirect("logistica:llegadas:ubicacion", pk=llegada.pk)
