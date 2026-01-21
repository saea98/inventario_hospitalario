"""
Vistas para Fase 2.3: Gestión de Inventario
Dashboard, consulta de lotes, movimientos y reportes
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, F
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import pandas as pd

from .models import Lote, MovimientoInventario, Producto, LoteUbicacion, Almacen, Institucion, UbicacionAlmacen
from .forms_entrada_salida import ItemEntradaForm, ItemSalidaForm


# ============================================================
# DASHBOARD DE INVENTARIO
# ============================================================

@login_required
def dashboard_inventario(request):
    """Dashboard principal de inventario con resumen y alertas"""
    
    # Obtener institución del usuario (si aplica)
    institucion = request.user.institucion if hasattr(request.user, 'institucion') else None
    
    # Filtrar por institución si el usuario tiene una asignada
    if institucion:
        lotes = Lote.objects.filter(institucion=institucion)
    else:
        lotes = Lote.objects.all()
    
    # Resumen de stock
    total_lotes = lotes.count()
    total_cantidad = lotes.aggregate(Sum('cantidad_disponible'))['cantidad_disponible__sum'] or 0
    
    # Lotes por estado
    lotes_disponibles = lotes.filter(estado=1).count()
    lotes_suspendidos = lotes.filter(estado=4).count()
    lotes_deteriorados = lotes.filter(estado=5).count()
    lotes_caducados = lotes.filter(estado=6).count()
    
    # Alertas de caducidad
    hoy = timezone.now().date()
    fecha_alerta = hoy + timedelta(days=90)
    
    lotes_proximos_caducar = lotes.filter(
        fecha_caducidad__lte=fecha_alerta,
        fecha_caducidad__gt=hoy,
        estado=1
    ).order_by('fecha_caducidad')[:10]
    
    lotes_caducados_alert = lotes.filter(
        fecha_caducidad__lt=hoy,
        estado__in=[1, 4, 5]
    ).order_by('fecha_caducidad')[:10]
    
    # Movimientos recientes
    movimientos_recientes = MovimientoInventario.objects.select_related('lote').order_by('-fecha_movimiento')[:10]
    
    # Productos con bajo stock
    productos_bajo_stock = []
    for producto in Producto.objects.filter(activo=True):
        stock_total = lotes.filter(producto=producto, estado=1).aggregate(
            Sum('cantidad_disponible')
        )['cantidad_disponible__sum'] or 0
        
        if stock_total < 10:  # Umbral de bajo stock
            productos_bajo_stock.append({
                'producto': producto,
                'stock': stock_total
            })
    
    # Stock por almacén
    almacenes = Almacen.objects.filter(activo=True)
    stock_almacenes = []
    for almacen in almacenes:
        cantidad = lotes.filter(almacen=almacen, estado=1).aggregate(
            Sum('cantidad_disponible')
        )['cantidad_disponible__sum'] or 0
        stock_almacenes.append({
            'almacen': almacen,
            'cantidad': cantidad
        })
    
    context = {
        'total_lotes': total_lotes,
        'total_cantidad': total_cantidad,
        'lotes_disponibles': lotes_disponibles,
        'lotes_suspendidos': lotes_suspendidos,
        'lotes_deteriorados': lotes_deteriorados,
        'lotes_caducados': lotes_caducados,
        'lotes_proximos_caducar': lotes_proximos_caducar,
        'lotes_caducados_alert': lotes_caducados_alert,
        'movimientos_recientes': movimientos_recientes,
        'productos_bajo_stock': productos_bajo_stock,
        'stock_almacenes': stock_almacenes,
    }
    
    return render(request, 'inventario/dashboard_inventario.html', context)


# ============================================================
# CONSULTA DE LOTES
# ============================================================

@login_required
def lista_lotes(request):
    """Lista de lotes con filtros y búsqueda"""
    
    # Obtener institución del usuario
    institucion = request.user.institucion if hasattr(request.user, 'institucion') else None
    
    # Filtro base
    if institucion:
        lotes = Lote.objects.filter(institucion=institucion).select_related(
            'producto', 'almacen', 'ubicacion'
        )
    else:
        lotes = Lote.objects.all().select_related(
            'producto', 'almacen', 'ubicacion'
        )
    
    # Filtros
    filtro_estado = request.GET.get('estado', '')
    filtro_almacen = request.GET.get('almacen', '')
    filtro_producto = request.GET.get('producto', '')
    filtro_caducidad = request.GET.get('caducidad', '')
    busqueda_lote = request.GET.get('busqueda_lote', '')
    busqueda_cnis = request.GET.get('busqueda_cnis', '')
    busqueda_producto = request.GET.get("busqueda_producto", "")
    filtro_partida = request.GET.get("partida", "")
    
    # Aplicar filtros
    if filtro_estado:
        lotes = lotes.filter(estado=int(filtro_estado))
    
    if filtro_almacen:
        lotes = lotes.filter(almacen_id=int(filtro_almacen))
    
    if filtro_producto:
        lotes = lotes.filter(producto_id=int(filtro_producto))
    
    # Filtro de caducidad
    hoy = timezone.now().date()
    if filtro_caducidad:
        if filtro_caducidad == 'caducados':
            lotes = lotes.filter(fecha_caducidad__lt=hoy)
        elif filtro_caducidad == 'menos_30':
            lotes = lotes.filter(fecha_caducidad__gte=hoy, fecha_caducidad__lte=hoy + timedelta(days=30))
        elif filtro_caducidad == 'menos_60':
            lotes = lotes.filter(fecha_caducidad__gte=hoy, fecha_caducidad__lte=hoy + timedelta(days=60))
        elif filtro_caducidad == 'menos_90':
            lotes = lotes.filter(fecha_caducidad__gte=hoy, fecha_caducidad__lte=hoy + timedelta(days=90))
    
    # Búsquedas separadas
    if busqueda_lote:
        lotes = lotes.filter(numero_lote__icontains=busqueda_lote)
    
    if busqueda_cnis:
        lotes = lotes.filter(producto__clave_cnis__icontains=busqueda_cnis)
    
    if busqueda_producto:
        lotes = lotes.filter(producto__descripcion__icontains=busqueda_producto)

    if filtro_partida:
        lotes = lotes.filter(partida__icontains=filtro_partida)
    
    # Ordenar
    lotes = lotes.order_by('-fecha_recepcion')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(lotes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Opciones para filtros
    almacenes = Almacen.objects.filter(activo=True)
    productos = Producto.objects.filter(activo=True)
    estados = Lote.ESTADOS_CHOICES
    
    # Columnas disponibles para exportación
    columnas_disponibles = [
        {'value': 'numero_lote', 'label': 'Número de Lote'},
        {'value': 'producto__descripcion', 'label': 'Producto'},
        {'value': 'institucion__denominacion', 'label': 'Institución'},
        {'value': 'cantidad_inicial', 'label': 'Cantidad Inicial'},
        {'value': 'cantidad_disponible', 'label': 'Cantidad Disponible'},
        {'value': 'precio_unitario', 'label': 'Precio Unitario'},
        {'value': 'valor_total', 'label': 'Valor Total'},
        {'value': 'fecha_fabricacion', 'label': 'Fecha de Fabricación'},
        {'value': 'fecha_caducidad', 'label': 'Fecha de Caducidad'},
        {'value': 'fecha_recepcion', 'label': 'Fecha de Recepción'},
        {'value': 'estado', 'label': 'Estado'},
        {'value': 'observaciones', 'label': 'Observaciones'},
        {'value': 'rfc_proveedor', 'label': 'RFC Proveedor'},
        {'value': 'proveedor', 'label': 'Proveedor'},
        {'value': 'partida', 'label': 'Partida'},
        {'value': 'clave_saica', 'label': 'Clave SAICA'},
        {'value': 'descripcion_saica', 'label': 'Descripción SAICA'},
        {'value': 'unidad_saica', 'label': 'Unidad SAICA'},
        {'value': 'fuente_datos', 'label': 'Fuente de Datos'},
        {'value': 'contrato', 'label': 'Contrato'},
        {'value': 'folio', 'label': 'Folio'},
        {'value': 'subtotal', 'label': 'Subtotal'},
        {'value': 'iva', 'label': 'IVA'},
        {'value': 'importe_total', 'label': 'Importe Total'},
        {'value': 'licitacion', 'label': 'Licitación / Procedimiento'},
        {'value': 'pedido', 'label': 'Pedido'},
        {'value': 'remision', 'label': 'Remisión'},
        {'value': 'responsable', 'label': 'Responsable'},
        {'value': 'reviso', 'label': 'Revisó'},
        {'value': 'tipo_entrega', 'label': 'Tipo de Entrega'},
        {'value': 'tipo_red', 'label': 'Tipo de Red'},
        {'value': 'epa', 'label': 'EPA'},
        {'value': 'producto__clave_cnis', 'label': 'Clave CNIS'},
        {'value': 'almacen__nombre', 'label': 'Almacén'},
        {'value': 'ubicacion__codigo', 'label': 'Ubicación'},
    ]
    
    context = {
        'page_obj': page_obj,
        'almacenes': almacenes,
        'productos': productos,
        'estados': estados,
        'filtro_estado': filtro_estado,
        'filtro_almacen': filtro_almacen,
        'filtro_producto': filtro_producto,
        'filtro_caducidad': filtro_caducidad,
        'busqueda_lote': busqueda_lote,
        'busqueda_cnis': busqueda_cnis,
        "busqueda_producto": busqueda_producto,
        "filtro_partida": filtro_partida,
        'columnas_disponibles': columnas_disponibles,
    }
    
    return render(request, 'inventario/lista_lotes.html', context)


@login_required
def detalle_lote(request, lote_id):
    """Detalle de un lote específico"""
    
    lote = get_object_or_404(
        Lote.objects.select_related('producto', 'almacen', 'ubicacion', 'institucion'),
        id=lote_id
    )
    
    # Ubicaciones del lote
    ubicaciones = LoteUbicacion.objects.filter(lote=lote).select_related('ubicacion', 'ubicacion__almacen')

    # Movimientos del lote
    movimientos = lote.movimientos.all().order_by('-fecha_movimiento')
    
    # Información adicional
    dias_para_caducidad = lote.dias_para_caducidad
    esta_proximo_caducar = lote.esta_proximo_a_caducar
    esta_caducado = lote.esta_caducado
    
    context = {
        'lote': lote,
        'ubicaciones': ubicaciones,
        'movimientos': movimientos,
        'dias_para_caducidad': dias_para_caducidad,
        'esta_proximo_caducar': esta_proximo_caducar,
        'esta_caducado': esta_caducado,
    }
    
    return render(request, 'inventario/detalle_lote.html', context)


# ============================================================
# MOVIMIENTOS DE INVENTARIO
# ============================================================

@login_required
def registrar_salida(request):
    """Registrar salida de inventario"""
    
    if request.method == 'POST':
        form = ItemSalidaForm(request.POST)
        if form.is_valid():
            try:
                lote = Lote.objects.get(id=form.cleaned_data['lote_id'])
                cantidad_salida = form.cleaned_data['cantidad_salida']
                
                # Validar cantidad disponible
                if cantidad_salida > lote.cantidad_disponible:
                    messages.error(
                        request,
                        f'Cantidad solicitada ({cantidad_salida}) mayor que disponible ({lote.cantidad_disponible})'
                    )
                    return redirect('registrar_salida')
                
                # Crear movimiento
                movimiento = MovimientoInventario.objects.create(
                    lote=lote,
                    tipo_movimiento='SALIDA',
                    cantidad=cantidad_salida,
                    cantidad_anterior=lote.cantidad_disponible,
                    cantidad_nueva=lote.cantidad_disponible - cantidad_salida,
                    motivo=form.cleaned_data['motivo_salida'],
                    observaciones=form.cleaned_data.get('observaciones', ''),
                    usuario=request.user,
                    institucion=lote.institucion,
                )
                
                # Actualizar lote
                lote.cantidad_disponible -= cantidad_salida
                lote.save()
                
                messages.success(request, f'Salida registrada correctamente. Movimiento ID: {movimiento.id}')
                return redirect('lista_lotes')
                
            except Lote.DoesNotExist:
                messages.error(request, 'Lote no encontrado')
            except Exception as e:
                messages.error(request, f'Error al registrar salida: {str(e)}')
    else:
        form = ItemSalidaForm()
    
    # Obtener lotes disponibles
    lotes = Lote.objects.filter(estado=1, cantidad_disponible__gt=0).select_related('producto')
    
    context = {
        'form': form,
        'lotes': lotes,
        'titulo': 'Registrar Salida de Inventario'
    }
    
    return render(request, 'inventario/registrar_salida.html', context)


@login_required
def registrar_ajuste(request):
    """Registrar ajuste de inventario"""
    
    if request.method == 'POST':
        lote_id = request.POST.get('lote_id')
        tipo_ajuste = request.POST.get('tipo_ajuste')  # AJUSTE_POSITIVO o AJUSTE_NEGATIVO
        cantidad = int(request.POST.get('cantidad', 0))
        motivo = request.POST.get('motivo', '')
        observaciones = request.POST.get('observaciones', '')
        
        try:
            lote = Lote.objects.get(id=lote_id)
            
            # Validar cantidad para ajuste negativo
            if tipo_ajuste == 'AJUSTE_NEGATIVO' and cantidad > lote.cantidad_disponible:
                messages.error(
                    request,
                    f'Cantidad a restar ({cantidad}) mayor que disponible ({lote.cantidad_disponible})'
                )
                return redirect('registrar_ajuste')
            
            # Calcular nueva cantidad
            if tipo_ajuste == 'AJUSTE_POSITIVO':
                cantidad_nueva = lote.cantidad_disponible + cantidad
            else:
                cantidad_nueva = lote.cantidad_disponible - cantidad
            
            # Crear movimiento
            movimiento = MovimientoInventario.objects.create(
                lote=lote,
                tipo_movimiento=tipo_ajuste,
                cantidad=cantidad,
                cantidad_anterior=lote.cantidad_disponible,
                cantidad_nueva=cantidad_nueva,
                motivo=motivo,
                observaciones=observaciones,
                usuario=request.user,
                institucion=lote.institucion,
            )
            
            # Actualizar lote
            lote.cantidad_disponible = cantidad_nueva
            lote.save()
            
            messages.success(request, f'Ajuste registrado correctamente. Movimiento ID: {movimiento.id}')
            return redirect('lista_lotes')
            
        except Lote.DoesNotExist:
            messages.error(request, 'Lote no encontrado')
        except Exception as e:
            messages.error(request, f'Error al registrar ajuste: {str(e)}')
    
    # Obtener lotes
    lotes = Lote.objects.filter(estado=1).select_related('producto')
    
    context = {
        'lotes': lotes,
        'titulo': 'Registrar Ajuste de Inventario'
    }
    
    return render(request, 'inventario/registrar_ajuste.html', context)


@login_required
def lista_movimientos(request):
    """Lista de movimientos de inventario"""
    
    # Obtener institución del usuario
    institucion = request.user.institucion if hasattr(request.user, 'institucion') else None
    
    # Filtro base
    if institucion:
        movimientos = MovimientoInventario.objects.filter(
            institucion_destino=institucion
        ).select_related('lote', 'usuario')
    else:
        movimientos = MovimientoInventario.objects.all().select_related('lote', 'usuario')
    
    # Filtros
    filtro_tipo = request.GET.get('tipo', '')
    filtro_fecha_desde = request.GET.get('fecha_desde', '')
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '')
    busqueda_lote = request.GET.get('busqueda_lote', '')
    busqueda_producto = request.GET.get('busqueda_producto', '')
    busqueda_motivo = request.GET.get('busqueda_motivo', '')
    
    # Aplicar filtros
    if filtro_tipo:
        movimientos = movimientos.filter(tipo_movimiento=filtro_tipo)
    
    if filtro_fecha_desde:
        try:
            fecha = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d').date()
            movimientos = movimientos.filter(fecha_movimiento__date__gte=fecha)
        except ValueError:
            pass
    
    if filtro_fecha_hasta:
        try:
            fecha = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d').date()
            movimientos = movimientos.filter(fecha_movimiento__date__lte=fecha)
        except ValueError:
            pass
    
    # Búsquedas separadas
    if busqueda_lote:
        movimientos = movimientos.filter(lote__numero_lote__icontains=busqueda_lote)
    
    if busqueda_producto:
        movimientos = movimientos.filter(lote__producto__descripcion__icontains=busqueda_producto)
    
    if busqueda_motivo:
        movimientos = movimientos.filter(motivo__icontains=busqueda_motivo)
    
    # Ordenar
    movimientos = movimientos.order_by('-fecha_movimiento')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(movimientos, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Opciones para filtros
    tipos_movimiento = MovimientoInventario.TIPOS_MOVIMIENTO
    
    context = {
        'page_obj': page_obj,
        'tipos_movimiento': tipos_movimiento,
        'filtro_tipo': filtro_tipo,
        'filtro_fecha_desde': filtro_fecha_desde,
        'filtro_fecha_hasta': filtro_fecha_hasta,
        'busqueda_lote': busqueda_lote,
        'busqueda_producto': busqueda_producto,
        'busqueda_motivo': busqueda_motivo,
    }
    
    return render(request, 'inventario/lista_movimientos.html', context)


# ============================================================
# CAMBIO DE ESTADO DE LOTE
# ============================================================

@login_required
@require_http_methods(["POST"])
def cambiar_estado_lote(request, lote_id):
    """Cambiar estado de un lote"""
    
    lote = get_object_or_404(Lote, id=lote_id)
    nuevo_estado = request.POST.get('nuevo_estado')
    motivo = request.POST.get('motivo', '')
    
    try:
        nuevo_estado = int(nuevo_estado)
        
        # Validar que el estado sea válido
        estados_validos = [choice[0] for choice in Lote.ESTADOS_CHOICES]
        if nuevo_estado not in estados_validos:
            messages.error(request, 'Estado no válido')
            return redirect('detalle_lote', lote_id=lote_id)
        
        # Actualizar lote
        lote.estado = nuevo_estado
        lote.motivo_cambio_estado = motivo
        lote.fecha_cambio_estado = timezone.now()
        lote.usuario_cambio_estado = request.user
        lote.save()
        
        # Crear movimiento de auditoría
        tipo_movimiento_map = {
            4: 'SUSPENSIÓN',
            5: 'DETERIORO',
            6: 'CADUCIDAD'
        }
        
        if nuevo_estado in tipo_movimiento_map:
            MovimientoInventario.objects.create(
                lote=lote,
                tipo_movimiento=tipo_movimiento_map[nuevo_estado],
                cantidad=0,
                cantidad_anterior=lote.cantidad_disponible,
                cantidad_nueva=lote.cantidad_disponible,
                motivo=motivo,
                usuario=request.user,
                institucion=lote.institucion,
            )
        
        estado_nombre = dict(Lote.ESTADOS_CHOICES)[nuevo_estado]
        messages.success(request, f'Estado del lote actualizado a: {estado_nombre}')
        
    except Exception as e:
        messages.error(request, f'Error al cambiar estado: {str(e)}')
    
    return redirect('detalle_lote', lote_id=lote_id)



# ============================================================
# EXPORTACIÓN PERSONALIZADA DE LOTES
# ============================================================

@login_required
def exportar_lotes_personalizado(request):
    """
    Vista para exportar lotes a Excel con campos personalizados.
    Respeta los filtros aplicados en la lista.
    """
    if request.method == "POST":
        try:
            # 1️⃣ Recuperar campos seleccionados y ordenados
            campos = request.POST.getlist("columnas")  # checkboxes seleccionados
            orden_columnas = request.POST.get("orden_columnas", "")
            
            # Si hay un orden personalizado, lo respetamos
            if orden_columnas:
                orden = [c for c in orden_columnas.split(",") if c in campos]
                if orden:
                    campos = orden

            if not campos:
                return JsonResponse({"error": "No se seleccionaron columnas válidas"}, status=400)

            # 2️⃣ Obtener institución del usuario
            institucion = request.user.institucion if hasattr(request.user, 'institucion') else None
            
            # 3️⃣ Filtro base
            if institucion:
                lotes = Lote.objects.filter(institucion=institucion).select_related(
                    'producto', 'almacen', 'ubicacion', 'institucion'
                ).prefetch_related('ubicaciones_detalle__ubicacion')
            else:
                lotes = Lote.objects.all().select_related(
                    'producto', 'almacen', 'ubicacion', 'institucion'
                ).prefetch_related('ubicaciones_detalle__ubicacion')
            
            # 4✍⃣ Aplicar filtros (si vienen en la petición)
            filtro_estado = request.POST.get('filtro_estado', '')
            filtro_almacen = request.POST.get('filtro_almacen', '')
            filtro_producto = request.POST.get('filtro_producto', '')
            filtro_caducidad = request.POST.get('filtro_caducidad', '')
            busqueda_lote = request.POST.get('busqueda_lote', '')
            busqueda_cnis = request.POST.get('busqueda_cnis', '')
            busqueda_producto = request.POST.get('busqueda_producto', '')
            filtro_partida = request.POST.get('filtro_partida', '')
            
            if filtro_estado:
                lotes = lotes.filter(estado=int(filtro_estado))
            
            if filtro_almacen:
                lotes = lotes.filter(almacen_id=int(filtro_almacen))
            
            if filtro_producto:
                lotes = lotes.filter(producto_id=int(filtro_producto))
            
            # Filtro de caducidad
            hoy = timezone.now().date()
            if filtro_caducidad:
                if filtro_caducidad == 'caducados':
                    lotes = lotes.filter(fecha_caducidad__lt=hoy)
                elif filtro_caducidad == 'menos_30':
                    lotes = lotes.filter(fecha_caducidad__gte=hoy, fecha_caducidad__lte=hoy + timedelta(days=30))
                elif filtro_caducidad == 'menos_60':
                    lotes = lotes.filter(fecha_caducidad__gte=hoy, fecha_caducidad__lte=hoy + timedelta(days=60))
                elif filtro_caducidad == 'menos_90':
                    lotes = lotes.filter(fecha_caducidad__gte=hoy, fecha_caducidad__lte=hoy + timedelta(days=90))
            
            if busqueda_lote:
                lotes = lotes.filter(numero_lote__icontains=busqueda_lote)
            
            if busqueda_cnis:
                lotes = lotes.filter(producto__clave_cnis__icontains=busqueda_cnis)
            
            if busqueda_producto:
                lotes = lotes.filter(producto__descripcion__icontains=busqueda_producto)

            if filtro_partida:
                lotes = lotes.filter(partida__icontains=filtro_partida)
            
            # 5️⃣ Procesar datos manualmente para manejar ubicaciones correctamente
            datos_lista = []
            estado_map = dict(Lote.ESTADOS_CHOICES)
            
            for lote in lotes.order_by('-fecha_recepcion'):
                # Obtener ubicaciones del lote
                ubicaciones = lote.ubicaciones_detalle.all()
                
                if ubicaciones.exists():
                    # Si hay ubicaciones, crear un registro por cada ubicación
                    for ubi in ubicaciones:
                        registro = {}
                        for campo in campos:
                            if campo == 'ubicacion__codigo':
                                # Obtener el código de la ubicación desde LoteUbicacion
                                registro[campo] = ubi.ubicacion.codigo if ubi.ubicacion else ""
                            elif campo == 'almacen__nombre':
                                registro[campo] = lote.almacen.nombre if lote.almacen else ""
                            elif campo == 'producto__clave_cnis':
                                registro[campo] = lote.producto.clave_cnis if lote.producto else ""
                            elif campo == 'institucion__denominacion':
                                registro[campo] = lote.institucion.denominacion if lote.institucion else ""
                            elif campo == 'producto__descripcion':
                                registro[campo] = lote.producto.descripcion if lote.producto else ""
                            elif campo == 'estado':
                                registro[campo] = estado_map.get(lote.estado, str(lote.estado))
                            else:
                                # Obtener el valor del campo del lote
                                valor = getattr(lote, campo.replace('__', '_'), None)
                                if valor is None and '__' in campo:
                                    # Intentar acceso por relación
                                    partes = campo.split('__')
                                    obj = lote
                                    for parte in partes:
                                        obj = getattr(obj, parte, None)
                                        if obj is None:
                                            break
                                    valor = obj
                                registro[campo] = valor
                        datos_lista.append(registro)
                else:
                    # Si no hay ubicaciones, crear un registro sin ubicación
                    registro = {}
                    for campo in campos:
                        if campo == 'ubicacion__codigo':
                            registro[campo] = ""
                        elif campo == 'almacen__nombre':
                            registro[campo] = lote.almacen.nombre if lote.almacen else ""
                        elif campo == 'producto__clave_cnis':
                            registro[campo] = lote.producto.clave_cnis if lote.producto else ""
                        elif campo == 'institucion__denominacion':
                            registro[campo] = lote.institucion.denominacion if lote.institucion else ""
                        elif campo == 'producto__descripcion':
                            registro[campo] = lote.producto.descripcion if lote.producto else ""
                        elif campo == 'estado':
                            registro[campo] = estado_map.get(lote.estado, str(lote.estado))
                        else:
                            # Obtener el valor del campo del lote
                            valor = getattr(lote, campo.replace('__', '_'), None)
                            if valor is None and '__' in campo:
                                # Intentar acceso por relación
                                partes = campo.split('__')
                                obj = lote
                                for parte in partes:
                                    obj = getattr(obj, parte, None)
                                    if obj is None:
                                        break
                                valor = obj
                            registro[campo] = valor
                    datos_lista.append(registro)
            
            if not datos_lista:
                return JsonResponse({"error": "No hay datos para exportar"}, status=404)

            # 6️⃣ Procesar campos legibles
            for registro in datos_lista:
                # Fechas legibles
                for k, v in registro.items():
                    if isinstance(v, Decimal):
                        registro[k] = float(v)
                    elif isinstance(v, (date, datetime)):
                        registro[k] = v.strftime("%Y-%m-%d %H:%M") if isinstance(v, datetime) else v.strftime("%Y-%m-%d")
                    elif v is None:
                        registro[k] = ""

            # 7️⃣ Exportar a Excel respetando el orden de columnas
            df = pd.DataFrame(datos_lista)

            # Si hay orden definido, reordenamos las columnas
            columnas_finales = [col for col in campos if col in df.columns]
            df = df[columnas_finales]

            # Generar Excel
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; filename="lotes.xlsx"'
            df.to_excel(response, index=False, sheet_name='Lotes')

            return response

        except Exception as e:
            return JsonResponse({"error": f"Error generando el reporte: {str(e)}"}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)
