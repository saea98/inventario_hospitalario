"""
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


@requiere_rol('Almacenero', 'Administrador', 'Gestor de Inventario', 'Supervisión')
def buscar_lote_conteo(request):
    """
    Vista para buscar un lote por CLAVE (CNIS).
    
    GET: Mostrar formulario de búsqueda
    POST: Buscar lote y redirigir a captura de conteos
    """
    
    institucion = request.user.institucion if hasattr(request.user, 'institucion') else None
    almacen_defecto = request.user.almacen if hasattr(request.user, 'almacen') else None
    
    # Si es GET, pre-cargar el almacén del usuario
    if request.method == 'GET':
        form = BuscarLoteForm(institucion=institucion)
        if almacen_defecto:
            form.fields['almacen'].initial = almacen_defecto
    else:
        form = BuscarLoteForm(institucion=institucion)
    
    lote_encontrado = None
    error = None
    
    if request.method == 'POST':
        form = BuscarLoteForm(request.POST, institucion=institucion)
        
        if form.is_valid():
            tipo_busqueda = form.cleaned_data['tipo_busqueda']
            criterio_busqueda = form.cleaned_data['criterio_busqueda'].strip()
            almacen = form.cleaned_data['almacen']
            
            # Buscar lote según el tipo de búsqueda
            try:
                if tipo_busqueda == 'clave':
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
                    'logistica:capturar_conteo_lote',
                    lote_id=lote.id
                )
                
            except Lote.DoesNotExist:
                # Lote no encontrado - Ofrecer opción de crear
                tipo_busqueda_label = 'CLAVE' if tipo_busqueda == 'clave' else 'LOTE'
                error = f"No se encontró lote con {tipo_busqueda_label}: {criterio_busqueda}"
                
                # Guardar datos en sesión para crear nuevo lote
                if tipo_busqueda == 'clave':
                    request.session['clave_cnis_busqueda'] = criterio_busqueda
                else:
                    request.session['numero_lote_busqueda'] = criterio_busqueda
                request.session['almacen_id_busqueda'] = almacen.id
                
                return redirect('logistica:crear_lote_conteo')
            
            except Lote.MultipleObjectsReturned:
                # Múltiples lotes encontrados - Mostrar lista para seleccionar
                if tipo_busqueda == 'clave':
                    lotes = Lote.objects.filter(
                        producto__clave_cnis=criterio_busqueda,
                        almacen=almacen
                    ).select_related("producto").prefetch_related("ubicaciones").order_by("numero_lote")
                    request.session['clave_cnis_busqueda'] = criterio_busqueda
                else:
                    lotes = Lote.objects.filter(
                        numero_lote=criterio_busqueda,
                        almacen=almacen
                    ).select_related('producto').order_by('numero_lote')
                    request.session['numero_lote_busqueda'] = criterio_busqueda
                
                if lotes.exists():
                    # Guardar datos en sesión y redirigir a selección de lote
                    request.session['almacen_id_busqueda'] = almacen.id
                    return redirect('logistica:seleccionar_lote_conteo')
                else:
                    tipo_busqueda_label = 'CLAVE' if tipo_busqueda == 'clave' else 'LOTE'
                    error = f"No se encontró lote con {tipo_busqueda_label}: {criterio_busqueda}"
                    if tipo_busqueda == 'clave':
                        request.session['clave_cnis_busqueda'] = criterio_busqueda
                    else:
                        request.session['numero_lote_busqueda'] = criterio_busqueda
                    request.session['almacen_id_busqueda'] = almacen.id
                    return redirect('logistica:crear_lote_conteo')
    
    return render(request, 'inventario/conteo_fisico/buscar_lote.html', {
        'form': form,
        'error': error
    })


@login_required
def capturar_conteo_lote(request, lote_id=None, lote_ubicacion_id=None):
    """
    Vista para capturar los tres conteos de un lote específico.
    
    Muestra:
    - Datos del lote (cantidad sistema, precio, etc.)
    - Campos para los tres conteos
    - Cálculos automáticos de diferencias
    
    POST: Guardar conteos y crear MovimientoInventario
    """
    
    # Determinar si se viene de seleccionar_lote_conteo (con lote_ubicacion_id) o directamente (con lote_id)
    if lote_ubicacion_id:
        lote_ubicacion = get_object_or_404(LoteUbicacion, id=lote_ubicacion_id)
        lote = lote_ubicacion.lote
        ubicaciones = [lote_ubicacion]  # Solo la ubicación seleccionada
    else:
        lote = get_object_or_404(Lote.objects.prefetch_related("ubicaciones_detalle__ubicacion__almacen"), id=lote_id)
        ubicaciones = lote.ubicaciones_detalle.all()
    
    producto = lote.producto
    
    if request.method == 'POST':
        if 'update_locations' in request.POST:
            formset = LoteUbicacionFormSet(request.POST, queryset=LoteUbicacion.objects.filter(lote=lote), prefix='ubicaciones')
            if formset.is_valid():
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.lote = lote
                    instance.save()
                formset.save_m2m()
                messages.success(request, 'Ubicaciones actualizadas exitosamente.')
                return redirect('logistica:capturar_conteo_lote', lote_id=lote.id)
        
        form = CapturarConteosForm(request.POST)
        if form.is_valid():
            cifra_primer_conteo = form.cleaned_data['cifra_primer_conteo']
            cifra_segundo_conteo = form.cleaned_data.get('cifra_segundo_conteo') or 0
            tercer_conteo = form.cleaned_data['tercer_conteo']  # VALOR DEFINITIVO
            observaciones = form.cleaned_data.get('observaciones', '')
            
            try:
                with transaction.atomic():
                    # Calcular diferencia usando TERCER CONTEO
                    cantidad_anterior = lote.cantidad_disponible
                    cantidad_nueva = tercer_conteo
                    diferencia = cantidad_nueva - cantidad_anterior
                    
                    # Crear MovimientoInventario
                    # Determinar tipo de movimiento según la diferencia
                    if diferencia > 0:
                        tipo_mov = 'AJUSTE_POSITIVO'
                    elif diferencia < 0:
                        tipo_mov = 'AJUSTE_NEGATIVO'
                    else:
                        tipo_mov = 'AJUSTE_POSITIVO'
                    
                    motivo_conteo = f"""Conteo Físico IMSS-Bienestar:
- Primer Conteo: {cifra_primer_conteo}
- Segundo Conteo: {cifra_segundo_conteo if cifra_segundo_conteo > 0 else 'No capturado'}
- Tercer Conteo (Definitivo): {tercer_conteo}
- Diferencia: {diferencia:+d}
{f'- Observaciones: {observaciones}' if observaciones else ''}"""
                    
                    movimiento = MovimientoInventario.objects.create(
                        lote=lote,
                        tipo_movimiento=tipo_mov,
                        cantidad=abs(diferencia),
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=cantidad_nueva,
                        motivo=motivo_conteo,
                        usuario=request.user,
                        folio=f"CONTEO-{timezone.now().strftime('%Y%m%d%H%M%S')}"
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
                        f'✓ Conteo registrado exitosamente. '
                        f'Diferencia: {diferencia:+d} unidades. '
                        f'Folio: {movimiento.folio}'
                    )
                    
                    return redirect(
                        'logistica:detalle_movimiento_conteo',
                        movimiento_id=movimiento.id
                    )
                    
            except Exception as e:
                messages.error(request, f'Error al guardar conteo: {str(e)}')
    else:
        form = CapturarConteosForm()
        formset = LoteUbicacionFormSet(queryset=LoteUbicacion.objects.filter(lote=lote), prefix='ubicaciones')
    
    # Calcular valores para mostrar
    contexto = {
        'lote': lote,
        'producto': producto,
        'ubicaciones': ubicaciones,
        'form': form,
        'formset': formset,
        'cantidad_sistema': lote.cantidad_disponible,
    }
    
    return render(request, 'inventario/conteo_fisico/capturar_conteo.html', contexto)


@login_required
def seleccionar_lote_conteo(request):
    """
    Vista para seleccionar un lote específico cuando hay múltiples lotes
    para la misma CLAVE en el almacén.
    
    GET: Mostrar lista de lotes disponibles
    POST: Seleccionar lote y ubicación, redirigir a captura de conteos
    """
    
    clave_cnis = request.session.get('clave_cnis_busqueda')
    almacen_id = request.session.get('almacen_id_busqueda')
    
    if not clave_cnis or not almacen_id:
        messages.error(request, 'Sesión expirada. Por favor, realice la búsqueda nuevamente.')
        return redirect('logistica:buscar_lote_conteo')
    
    # Obtener todos los lotes para esta CLAVE y almacén
    lotes = Lote.objects.filter(
        producto__clave_cnis=clave_cnis,
        almacen_id=almacen_id
    ).select_related('producto', 'almacen').prefetch_related('ubicaciones_detalle__ubicacion').order_by('numero_lote')
    
    if not lotes.exists():
        messages.error(request, f'No se encontraron lotes con CLAVE: {clave_cnis}')
        return redirect('logistica:buscar_lote_conteo')
    
    if request.method == 'POST':
        lote_ubicacion_id = request.POST.get('lote_ubicacion_id')
        
        if not lote_ubicacion_id:
            messages.error(request, 'Por favor, seleccione un lote y su ubicación.')
            # Re-render the page with context
            producto_descripcion = lotes.first().producto.descripcion if lotes.exists() else ''
            contexto = {
                'lotes': lotes,
                'clave_cnis': clave_cnis,
                'almacen': Almacen.objects.get(id=almacen_id),
                'producto_descripcion': producto_descripcion,
                'producto': lotes.first().producto if lotes.exists() else None
            }
            return render(request, 'inventario/conteo_fisico/seleccionar_lote.html', contexto)
        
        try:
            lote_ubicacion = LoteUbicacion.objects.get(id=lote_ubicacion_id)
            # Limpiar sesión
            if 'clave_cnis_busqueda' in request.session:
                del request.session['clave_cnis_busqueda']
            if 'almacen_id_busqueda' in request.session:
                del request.session['almacen_id_busqueda']
            
            return redirect(
                'logistica:capturar_conteo_lote',
                lote_ubicacion_id=lote_ubicacion.id
            )
        except LoteUbicacion.DoesNotExist:
            messages.error(request, 'Ubicación del lote no encontrada.')
            # Re-render the page with context
            producto_descripcion = lotes.first().producto.descripcion if lotes.exists() else ''
            contexto = {
                'lotes': lotes,
                'clave_cnis': clave_cnis,
                'almacen': Almacen.objects.get(id=almacen_id),
                'producto_descripcion': producto_descripcion,
                'producto': lotes.first().producto if lotes.exists() else None
            }
            return render(request, 'inventario/conteo_fisico/seleccionar_lote.html', contexto)
    
    # Obtener la descripción del producto del primer lote
    producto_descripcion = lotes.first().producto.descripcion if lotes.exists() else ''
    
    contexto = {
        'lotes': lotes,
        'clave_cnis': clave_cnis,
        'almacen': Almacen.objects.get(id=almacen_id),
        'producto_descripcion': producto_descripcion,
        'producto': lotes.first().producto if lotes.exists() else None
    }
    
    return render(request, 'inventario/conteo_fisico/seleccionar_lote.html', contexto)


@login_required
def detalle_movimiento_conteo(request, movimiento_id):
    """
    Vista para mostrar el detalle de un movimiento de conteo.
    """
    movimiento = get_object_or_404(MovimientoInventario, id=movimiento_id)
    
    contexto = {
        'movimiento': movimiento,
        'lote': movimiento.lote,
    }
    
    return render(request, 'inventario/conteo_fisico/detalle_movimiento.html', contexto)


@login_required
def crear_lote_conteo(request):
    """
    Vista para crear un nuevo lote cuando no se encuentra en la búsqueda.
    """
    clave_cnis = request.session.get('clave_cnis_busqueda')
    numero_lote = request.session.get('numero_lote_busqueda')
    almacen_id = request.session.get('almacen_id_busqueda')
    
    if not almacen_id:
        messages.error(request, 'Sesión expirada. Por favor, realice la búsqueda nuevamente.')
        return redirect('logistica:buscar_lote_conteo')
    
    almacen = get_object_or_404(Almacen, id=almacen_id)
    
    if request.method == 'POST':
        form = CrearLoteManualForm(request.POST, almacen=almacen)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.almacen = almacen
            lote.save()
            
            # Limpiar sesión
            if 'clave_cnis_busqueda' in request.session:
                del request.session['clave_cnis_busqueda']
            if 'numero_lote_busqueda' in request.session:
                del request.session['numero_lote_busqueda']
            if 'almacen_id_busqueda' in request.session:
                del request.session['almacen_id_busqueda']
            
            messages.success(request, f'Lote {lote.numero_lote} creado exitosamente.')
            return redirect('logistica:capturar_conteo_lote', lote_id=lote.id)
    else:
        form = CrearLoteManualForm(almacen=almacen)
        if clave_cnis:
            form.fields['producto'].queryset = Producto.objects.filter(clave_cnis=clave_cnis)
    
    contexto = {
        'form': form,
        'almacen': almacen,
        'clave_cnis': clave_cnis,
        'numero_lote': numero_lote,
    }
    
    return render(request, 'inventario/conteo_fisico/crear_lote.html', contexto)


@login_required
def listar_conteos(request):
    """
    Vista para listar todos los conteos realizados.
    """
    movimientos = MovimientoInventario.objects.filter(
        tipo_movimiento__in=['AJUSTE_POSITIVO', 'AJUSTE_NEGATIVO']
    ).select_related('lote__producto', 'usuario').order_by('-fecha_creacion')
    
    contexto = {
        'movimientos': movimientos,
    }
    
    return render(request, 'inventario/conteo_fisico/listar_conteos.html', contexto)
