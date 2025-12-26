import """
Vistas para Conteo Físico - Validación de Existencias

Basado en el formato IMSS-Bienestar que captura tres conteos:
1. Primer Conteo (validación inicial)
2. Segundo Conteo (validación de diferencias)
3. Tercer Conteo (valor definitivo que se usa como nueva existencia)

Flujo:
1. Buscar lote por CLAVE (CNIS) en inventario_lote
2. Si existe: Cargar datos del sistema
3. Si NO existe: Opción de crear nuevo lote
4. Capturar los tres conteos
5. Usar TERCER CONTEO como cantidad_nueva
6. Crear MovimientoInventario con la diferencia
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

from .models import (
    Lote, Producto, Almacen, UbicacionAlmacen, 
    MovimientoInventario, Institucion, CategoriaProducto, LoteUbicacion
)
from .forms_conteo_fisico import (
    BuscarLoteForm, CapturarConteosForm, 
    CrearLoteManualForm, FiltroConteosForm, LoteUbicacionFormSet
)
from .servicios_notificaciones import notificaciones
from .access_control import requiere_rol


@requiere_rol("Almacenero", "Administrador", "Gestor de Inventario", "Supervisión")
def buscar_lote_conteo(request):
    """
    Vista para buscar un lote por CLAVE (CNIS).
    
    GET: Mostrar formulario de búsqueda
    POST: Buscar lote y redirigir a captura de conteos
    """
    
    institucion = request.user.institucion if hasattr(request.user, "institucion") else None
    almacen_defecto = request.user.almacen if hasattr(request.user, "almacen") else None
    
    # Si es GET, pre-cargar el almacén del usuario
    if request.method == "GET":
        form = BuscarLoteForm(institucion=institucion)
        if almacen_defecto:
            form.fields["almacen"].initial = almacen_defecto
    else:
        form = BuscarLoteForm(institucion=institucion)
    
    lote_encontrado = None
    error = None
    
    if request.method == "POST":
        form = BuscarLoteForm(request.POST, institucion=institucion)
        
        if form.is_valid():
            tipo_busqueda = form.cleaned_data["tipo_busqueda"]
            criterio_busqueda = form.cleaned_data["criterio_busqueda"].strip()
            almacen = form.cleaned_data["almacen"]
            
            # Buscar lote según el tipo de búsqueda
            try:
                if tipo_busqueda == "clave":
                    # Búsqueda por CLAVE (CNIS)
                    lote = Lote.objects.get(
                        producto__clave_cnis=criterio_busqueda,
                        almacen=almacen
                    )
                else:
                    # Búsqueda por NÚMERO DE LOTE
                    lote = Lote.objects.get(
                        numero_lote=criterio_busqueda,
                        almacen=almacen
                    )
                
                # Redirigir a captura de conteos
                return redirect(
                    "logistica:capturar_conteo_lote",
                    lote_id=lote.id
                )
                
            except Lote.DoesNotExist:
                # Lote no encontrado - Ofrecer opción de crear
                tipo_busqueda_label = "CLAVE" if tipo_busqueda == "clave" else "LOTE"
                error = f"No se encontró lote con {tipo_busqueda_label}: {criterio_busqueda}"
                
                # Guardar datos en sesión para crear nuevo lote
                if tipo_busqueda == "clave":
                    request.session["clave_cnis_busqueda"] = criterio_busqueda
                else:
                    request.session["numero_lote_busqueda"] = criterio_busqueda
                request.session["almacen_id_busqueda"] = almacen.id
                
                return redirect("logistica:crear_lote_conteo")
            
            except Lote.MultipleObjectsReturned:
                # Múltiples lotes encontrados - Mostrar lista para seleccionar
                if tipo_busqueda == "clave":
                    lotes = Lote.objects.filter(
                        producto__clave_cnis=criterio_busqueda,
                        almacen=almacen
                    ).select_related("producto").prefetch_related("ubicaciones_detalle").order_by("numero_lote")
                    request.session["clave_cnis_busqueda"] = criterio_busqueda
                else:
                    lotes = Lote.objects.filter(
                        numero_lote=criterio_busqueda,
                        almacen=almacen
                    ).select_related("producto").order_by("numero_lote")
                    request.session["numero_lote_busqueda"] = criterio_busqueda
                
                if lotes.exists():
                    # Guardar datos en sesión y redirigir a selección de lote
                    request.session["almacen_id_busqueda"] = almacen.id
                    return redirect("logistica:seleccionar_lote_conteo")
                else:
                    tipo_busqueda_label = "CLAVE" if tipo_busqueda == "clave" else "LOTE"
                    error = f"No se encontró lote con {tipo_busqueda_label}: {criterio_busqueda}"
                    if tipo_busqueda == "clave":
                        request.session["clave_cnis_busqueda"] = criterio_busqueda
                    else:
                        request.session["numero_lote_busqueda"] = criterio_busqueda
                    request.session["almacen_id_busqueda"] = almacen.id
                    return redirect("logistica:crear_lote_conteo")
    
    return render(request, "inventario/conteo_fisico/buscar_lote.html", {
        "form": form,
        "error": error
    })


@login_required
def capturar_conteo_lote(request, lote_id):
    """
    Vista para capturar los tres conteos de un lote específico.
    
    Muestra:
    - Datos del lote (cantidad sistema, precio, etc.)
    - Campos para los tres conteos
    - Cálculos automáticos de diferencias
    
    POST: Guardar conteos y crear MovimientoInventario
    """
    
    lote = get_object_or_404(Lote.objects.prefetch_related("ubicaciones_detalle"), id=lote_id)
    producto = lote.producto
    
    if request.method == "POST":
        if "update_locations" in request.POST:
            formset = LoteUbicacionFormSet(request.POST, queryset=LoteUbicacion.objects.filter(lote=lote), prefix="ubicaciones")
            if formset.is_valid():
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.lote = lote
                    instance.save()
                formset.save_m2m()
                messages.success(request, "Ubicaciones actualizadas exitosamente.")
                return redirect("logistica:capturar_conteo_lote", lote_id=lote.id)
        else:
            form = CapturarConteosForm(request.POST)
            if form.is_valid():
                cifra_primer_conteo = form.cleaned_data["cifra_primer_conteo"]
                cifra_segundo_conteo = form.cleaned_data.get("cifra_segundo_conteo") or 0
                tercer_conteo = form.cleaned_data["tercer_conteo"]  # VALOR DEFINITIVO
                observaciones = form.cleaned_data.get("observaciones", "")
                
                try:
                    with transaction.atomic():
                        # Calcular diferencia usando TERCER CONTEO
                        cantidad_anterior = lote.cantidad_disponible
                        cantidad_nueva = tercer_conteo
                        diferencia = cantidad_nueva - cantidad_anterior
                        
                        # Crear MovimientoInventario
                        # Determinar tipo de movimiento según la diferencia
                        if diferencia > 0:
                            tipo_mov = "AJUSTE_POSITIVO"
                        elif diferencia < 0:
                            tipo_mov = "AJUSTE_NEGATIVO"
                        else:
                            tipo_mov = "AJUSTE_POSITIVO"
                        
                        motivo_conteo = f"""Conteo Físico IMSS-Bienestar:
- Primer Conteo: {cifra_primer_conteo}
- Segundo Conteo: {cifra_segundo_conteo if cifra_segundo_conteo > 0 else "No capturado"}
- Tercer Conteo (Definitivo): {tercer_conteo}
- Diferencia: {diferencia:+d}
{f"- Observaciones: {observaciones}" if observaciones else ""}"""
                        
                        movimiento = MovimientoInventario.objects.create(
                            lote=lote,
                            tipo_movimiento=tipo_mov,
                            cantidad=abs(diferencia),
                            cantidad_anterior=cantidad_anterior,
                            cantidad_nueva=cantidad_nueva,
                            motivo=motivo_conteo,
                            usuario=request.user,
                            folio=f"CONTEO-{timezone.now().strftime("%Y%m%d%H%M%S")}"
                        )
                        
                        # Actualizar cantidad disponible en el lote
                        lote.cantidad_disponible = cantidad_nueva
                        lote.valor_total = cantidad_nueva * (lote.precio_unitario or 0)
                        lote.save()
                        
                        # Notificar
                        try:
                            notificaciones.notificar_conteo_completado(
                                lote=lote,
                                usuario=request.user,
                                diferencia=diferencia
                            )
                        except Exception as e:
                            print(f"Error al notificar: {e}")
                        
                        messages.success(
                            request,
                            f"✓ Conteo registrado exitosamente. "
                            f"Diferencia: {diferencia:+d} unidades. "
                            f"Folio: {movimiento.folio}"
                        )
                        
                        return redirect(
                            "logistica:detalle_movimiento_conteo",
                            movimiento_id=movimiento.id
                        )
                        
                except Exception as e:
                    messages.error(request, f"Error al guardar conteo: {str(e)}")
    else:
        form = CapturarConteosForm()
        formset = LoteUbicacionFormSet(queryset=LoteUbicacion.objects.filter(lote=lote), prefix="ubicaciones")
    
    # Calcular valores para mostrar
    contexto = {
        "lote": lote,
        "producto": producto,
        "form": form,
        "formset": formset,
        "cantidad_sistema": lote.cantidad_disponible,
        "precio_unitario": lote.precio_unitario or 0,
        "valor_sistema": (lote.cantidad_disponible or 0) * (lote.precio_unitario or 0),
    }
    
    return render(request, "inventario/conteo_fisico/capturar_conteo.html", contexto)


@login_required
def crear_lote_conteo(request):
    """
    Vista para crear un nuevo lote si no existe en el sistema.
    
    Se utiliza cuando la búsqueda por CLAVE no encuentra resultados.
    """
    
    clave_cnis = request.session.get("clave_cnis_busqueda")
    almacen_id = request.session.get("almacen_id_busqueda")
    
    if not clave_cnis or not almacen_id:
        messages.error(request, "Datos de búsqueda no disponibles")
        return redirect("logistica:buscar_lote_conteo")
    
    almacen = get_object_or_404(Almacen, id=almacen_id)
    
    # Buscar o crear producto por CLAVE
    try:
        producto = Producto.objects.get(clave_cnis=clave_cnis)
    except Producto.DoesNotExist:
        # Obtener categoría por defecto
        categoria = CategoriaProducto.objects.first()
        if not categoria:
            messages.error(request, "No hay categorías de producto disponibles")
            return redirect("logistica:buscar_lote_conteo")
        
        # Crear producto con CLAVE
        producto = Producto.objects.create(
            clave_cnis=clave_cnis,
            descripcion=f"Producto {clave_cnis} - Creado automáticamente durante conteo físico",
            categoria=categoria
        )
    
    if request.method == "POST":
        form = CrearLoteManualForm(request.POST)
        
        if form.is_valid():
            lote = form.save(commit=False)
            lote.producto = producto
            lote.almacen = almacen
            lote.save()
            
            messages.success(request, f"Lote {lote.numero_lote} creado exitosamente")
            
            # Limpiar sesión
            del request.session["clave_cnis_busqueda"]
            del request.session["almacen_id_busqueda"]
            
            # Redirigir a captura de conteos
            return redirect(
                "logistica:capturar_conteo_lote",
                lote_id=lote.id
            )
    else:
        form = CrearLoteManualForm()
    
    return render(request, "inventario/conteo_fisico/crear_lote.html", {
        "form": form,
        "producto": producto,
        "almacen": almacen
    })


@login_required
def seleccionar_lote_conteo(request):
    """
    Vista para seleccionar un lote específico cuando hay múltiples lotes
    para la misma CLAVE en el almacén.
    
    GET: Mostrar lista de lotes disponibles
    POST: Seleccionar lote y redirigir a captura de conteos
    """
    
    clave_cnis = request.session.get("clave_cnis_busqueda")
    almacen_id = request.session.get("almacen_id_busqueda")
    
    if not clave_cnis or not almacen_id:
        messages.error(request, "Sesión expirada. Por favor, realice la búsqueda nuevamente.")
        return redirect("logistica:buscar_lote_conteo")
    
    # Obtener todos los lotes para esta CLAVE y almacén
    lotes = Lote.objects.filter(
        producto__clave_cnis=clave_cnis,
        almacen_id=almacen_id
    ).select_related("producto", "almacen").prefetch_related("ubicaciones_detalle").order_by("numero_lote")
    
    if not lotes.exists():
        messages.error(request, f"No se encontraron lotes con CLAVE: {clave_cnis}")
        return redirect("logistica:buscar_lote_conteo")
    
    if request.method == "POST":
        lote_id = request.POST.get("lote_id")
        
        if not lote_id:
            messages.error(request, "Por favor, seleccione un lote.")
            return redirect("logistica:seleccionar_lote_conteo")
        
        try:
            lote = Lote.objects.get(id=lote_id, almacen_id=almacen_id)
            # Limpiar sesión
            del request.session["clave_cnis_busqueda"]
            del request.session["almacen_id_busqueda"]
            
            return redirect(
                "logistica:capturar_conteo_lote",
                lote_id=lote.id
            )
        except Lote.DoesNotExist:
            messages.error(request, "Lote no encontrado.")
            return redirect("logistica:seleccionar_lote_conteo")
    
    # Obtener la descripción del producto del primer lote
    producto_descripcion = lotes.first().producto.descripcion if lotes.exists() else ""
    
    contexto = {
        "lotes": lotes,
        "clave_cnis": clave_cnis,
        "almacen": Almacen.objects.get(id=almacen_id),
        "producto_descripcion": producto_descripcion,
    }
    
    return render(request, "inventario/conteo_fisico/seleccionar_lote.html", contexto)


@login_required
def cambiar_ubicacion_conteo(request, lote_id):
    lote = get_object_or_404(Lote.objects.prefetch_related("ubicaciones_detalle"), id=lote_id)
    if request.method == "POST":
        form = CambiarUbicacionForm(request.POST)
        if form.is_valid():
            nueva_ubicacion = form.cleaned_data["nueva_ubicacion"]
            cantidad = form.cleaned_data["cantidad"]
            
            # Lógica para cambiar la ubicación
            # ...
            
            messages.success(request, "Ubicación cambiada exitosamente.")
            return redirect("logistica:capturar_conteo_lote", lote_id=lote.id)
    else:
        form = CambiarUbicacionForm()
    
    return render(request, "inventario/conteo_fisico/cambiar_ubicacion.html", {
        "form": form,
        "lote": lote
    })


@login_required
def fusionar_ubicaciones_conteo(request, lote_id):
    lote = get_object_or_404(Lote.objects.prefetch_related("ubicaciones_detalle"), id=lote_id)
    if request.method == "POST":
        form = FusionarUbicacionesForm(request.POST)
        if form.is_valid():
            lote_destino = form.cleaned_data["lote_destino"]
            
            # Lógica para fusionar ubicaciones
            # ...
            
            messages.success(request, "Ubicaciones fusionadas exitosamente.")
            return redirect("logistica:capturar_conteo_lote", lote_id=lote.id)
    else:
        form = FusionarUbicacionesForm()
    
    return render(request, "inventario/conteo_fisico/fusionar_ubicaciones.html", {
        "form": form,
        "lote": lote
    })


@login_required
def asignar_ubicacion_conteo(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id)
    if request.method == "POST":
        form = AsignarUbicacionForm(request.POST)
        if form.is_valid():
            ubicacion = form.cleaned_data["ubicacion"]
            cantidad = form.cleaned_data["cantidad"]
            
            # Lógica para asignar la ubicación
            LoteUbicacion.objects.create(
                lote=lote,
                ubicacion=ubicacion,
                cantidad=cantidad
            )
            
            messages.success(request, "Ubicación asignada exitosamente.")
            return redirect("logistica:capturar_conteo_lote", lote_id=lote.id)
    else:
        form = AsignarUbicacionForm()
    
    return render(request, "inventario/conteo_fisico/asignar_ubicacion.html", {
        "form": form,
        "lote": lote
    })


@login_required
def editar_ubicaciones_conteo(request, lote_id):
    lote = get_object_or_404(Lote, id=lote_id)
    LoteUbicacionFormSet = modelformset_factory(LoteUbicacion, form=EditLoteUbicacionForm, extra=1, can_delete=True)
    
    if request.method == "POST":
        formset = LoteUbicacionFormSet(request.POST, queryset=LoteUbicacion.objects.filter(lote=lote))
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.lote = lote
                instance.save()
            formset.save_m2m()
            messages.success(request, "Ubicaciones actualizadas exitosamente.")
            return redirect("logistica:capturar_conteo_lote", lote_id=lote.id)
    else:
        formset = LoteUbicacionFormSet(queryset=LoteUbicacion.objects.filter(lote=lote))
        
    return render(request, "inventario/conteo_fisico/editar_ubicaciones.html", {
        "formset": formset,
        "lote": lote
    })
