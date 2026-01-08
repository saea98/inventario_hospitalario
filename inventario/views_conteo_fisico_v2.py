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
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, date
from decimal import Decimal
import pandas as pd

from .models import (
    Lote, Producto, Almacen, UbicacionAlmacen, 
    MovimientoInventario, Institucion, CategoriaProducto, LoteUbicacion,
    RegistroConteoFisico
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
    lote_ubicacion = None  # Inicializar como None
    if lote_ubicacion_id:
        lote_ubicacion = get_object_or_404(LoteUbicacion, id=lote_ubicacion_id)
        lote = lote_ubicacion.lote
        ubicaciones = [lote_ubicacion]  # Solo la ubicación seleccionada
    else:
        lote = get_object_or_404(Lote.objects.prefetch_related("ubicaciones_detalle__ubicacion__almacen"), id=lote_id)
        ubicaciones = lote.ubicaciones_detalle.all()
    
    producto = lote.producto
    
    # Obtener o crear registro de conteo para esta ubicación
    if lote_ubicacion_id:
        registro_conteo, created = RegistroConteoFisico.objects.get_or_create(
            lote_ubicacion_id=lote_ubicacion_id,
            defaults={'usuario_creacion': request.user}
        )
    else:
        registro_conteo = None
    
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
            cifra_primer_conteo = form.cleaned_data.get('cifra_primer_conteo')
            cifra_segundo_conteo = form.cleaned_data.get('cifra_segundo_conteo')
            tercer_conteo = form.cleaned_data.get('tercer_conteo')
            observaciones = form.cleaned_data.get('observaciones', '')
            
            # Validar que al menos uno de los conteos tenga valor
            if not any([cifra_primer_conteo, cifra_segundo_conteo, tercer_conteo]):
                messages.error(request, 'Debes ingresar al menos un conteo')
                return render(request, 'inventario/conteo_fisico/capturar_conteo.html', {
                    'form': form,
                    'lote': lote,
                    'lote_ubicacion': lote_ubicacion,
                    'ubicaciones': ubicaciones,
                    'registro_conteo': registro_conteo,
                })
            
            # Si se proporciona registro_conteo, guardar parcialmente
            if registro_conteo:
                # Actualizar registro de conteo
                if cifra_primer_conteo:
                    registro_conteo.primer_conteo = cifra_primer_conteo
                if cifra_segundo_conteo:
                    registro_conteo.segundo_conteo = cifra_segundo_conteo
                if tercer_conteo:
                    registro_conteo.tercer_conteo = tercer_conteo
                if observaciones:
                    registro_conteo.observaciones = observaciones
                
                registro_conteo.usuario_ultima_actualizacion = request.user
                registro_conteo.save()
                
                messages.success(request, f'Conteo guardado parcialmente. Progreso: {registro_conteo.progreso}')
                
                # Si se completó el tercer conteo, crear MovimientoInventario
                if tercer_conteo:
                    # Usar el tercer conteo como definitivo
                    cantidad_anterior = lote_ubicacion.cantidad
                    cantidad_nueva = tercer_conteo
                    diferencia = cantidad_nueva - cantidad_anterior
                    
                    # Actualizar LoteUbicacion
                    lote_ubicacion.cantidad = cantidad_nueva
                    lote_ubicacion.usuario_asignacion = request.user
                    lote_ubicacion.save()
                    
                    # Sincronizar cantidad del Lote
                    lote.sincronizar_cantidad_disponible()
                    
                    # Crear MovimientoInventario solo si hay diferencia
                    if diferencia != 0:
                        tipo_mov = 'AJUSTE_NEGATIVO' if diferencia < 0 else 'AJUSTE_POSITIVO'
                        
                        # Construir motivo dinámico
                        conteos_info = []
                        if registro_conteo.primer_conteo:
                            conteos_info.append(f"Primer Conteo: {registro_conteo.primer_conteo}")
                        if registro_conteo.segundo_conteo:
                            conteos_info.append(f"Segundo Conteo: {registro_conteo.segundo_conteo}")
                        conteos_info.append(f"Tercer Conteo (Definitivo): {tercer_conteo}")
                        
                        motivo_conteo = f"""Conteo Físico IMSS-Bienestar:
{chr(10).join('- ' + info for info in conteos_info)}
- Diferencia: {diferencia:+d}
{f'- Observaciones: {observaciones}' if observaciones else ''}"""
                        
                        MovimientoInventario.objects.create(
                            lote=lote,
                            tipo_movimiento=tipo_mov,
                            cantidad=abs(diferencia),
                            cantidad_anterior=cantidad_anterior,
                            cantidad_nueva=cantidad_nueva,
                            motivo=motivo_conteo,
                            usuario=request.user
                        )
                        
                        registro_conteo.completado = True
                        registro_conteo.save()
                        
                        messages.success(request, f'Conteo completado. Diferencia registrada: {diferencia:+d}')
                
                return redirect('logistica:capturar_conteo_lote', lote_ubicacion_id=lote_ubicacion_id)
            
            # Si no hay registro_conteo (conteo del lote completo), validar tercer conteo
            if not tercer_conteo:
                messages.error(request, 'El Tercer Conteo (Definitivo) es obligatorio')
                return render(request, 'inventario/conteo_fisico/capturar_conteo.html', {
                    'form': form,
                    'lote': lote,
                    'lote_ubicacion': lote_ubicacion,
                    'ubicaciones': ubicaciones,
                    'registro_conteo': registro_conteo,
                })
            
            # Convertir a números
            cifra_primer_conteo = cifra_primer_conteo or 0
            cifra_segundo_conteo = cifra_segundo_conteo or 0
            
            try:
                with transaction.atomic():
                    # Si es conteo por ubicación específica, actualizar LoteUbicacion
                    if lote_ubicacion_id:
                        # Obtener la ubicación específica
                        lote_ubicacion = LoteUbicacion.objects.get(id=lote_ubicacion_id)
                        cantidad_anterior = lote_ubicacion.cantidad
                        cantidad_nueva = tercer_conteo
                        diferencia = cantidad_nueva - cantidad_anterior
                        
                        # Actualizar cantidad en LoteUbicacion
                        lote_ubicacion.cantidad = cantidad_nueva
                        lote_ubicacion.usuario_asignacion = request.user
                        lote_ubicacion.save()
                        
                        # Sincronizar cantidad total del lote
                        lote.sincronizar_cantidad_disponible()
                    else:
                        # Conteo del lote completo (todas las ubicaciones)
                        cantidad_anterior = lote.cantidad_disponible
                        cantidad_nueva = tercer_conteo
                        diferencia = cantidad_nueva - cantidad_anterior
                        
                        # Actualizar cantidad disponible en el lote
                        lote.cantidad_disponible = cantidad_nueva
                        lote.valor_total = cantidad_nueva * (lote.precio_unitario or 0)
                        lote.save()
                    
                    # Crear MovimientoInventario
                    # Determinar tipo de movimiento según la diferencia
                    if diferencia > 0:
                        tipo_mov = 'AJUSTE_POSITIVO'
                    elif diferencia < 0:
                        tipo_mov = 'AJUSTE_NEGATIVO'
                    else:
                        tipo_mov = 'AJUSTE_POSITIVO'
                    
                    # Construir motivo dinámicamente según conteos capturados
                    conteos_info = []
                    if cifra_primer_conteo:
                        conteos_info.append(f"Primer Conteo: {cifra_primer_conteo}")
                    if cifra_segundo_conteo:
                        conteos_info.append(f"Segundo Conteo: {cifra_segundo_conteo}")
                    conteos_info.append(f"Tercer Conteo (Definitivo): {tercer_conteo}")
                    
                    motivo_conteo = f"""Conteo Físico IMSS-Bienestar:
{chr(10).join('- ' + info for info in conteos_info)}
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
    
    # Siempre crear formset
    formset = LoteUbicacionFormSet(queryset=LoteUbicacion.objects.filter(lote=lote), prefix='ubicaciones')
    
    # Cargar datos previos en el formulario si existen
    initial_data = {}
    if registro_conteo:
        if registro_conteo.primer_conteo:
            initial_data['cifra_primer_conteo'] = registro_conteo.primer_conteo
        if registro_conteo.segundo_conteo:
            initial_data['cifra_segundo_conteo'] = registro_conteo.segundo_conteo
        if registro_conteo.tercer_conteo:
            initial_data['tercer_conteo'] = registro_conteo.tercer_conteo
        if registro_conteo.observaciones:
            initial_data['observaciones'] = registro_conteo.observaciones
        
        # Si el formulario no fue enviado, crear uno con datos previos
        if request.method != 'POST':
            form = CapturarConteosForm(initial=initial_data)
    
    # Calcular valores para mostrar
    contexto = {
        'lote': lote,
        'producto': producto,
        'ubicaciones': ubicaciones,
        'form': form,
        'formset': formset,
        'cantidad_sistema': lote.cantidad_disponible,
        'registro_conteo': registro_conteo,
        'lote_ubicacion': lote_ubicacion,
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
    ).select_related('lote__producto', 'usuario').order_by('-fecha_movimiento')
    
    # Columnas disponibles para exportación
    columnas_disponibles = [
        {'value': 'id', 'label': 'ID'},
        {'value': 'lote__numero_lote', 'label': 'Número de Lote'},
        {'value': 'lote__producto__clave_cnis', 'label': 'CLAVE CNIS'},
        {'value': 'lote__producto__descripcion', 'label': 'Descripción del Producto'},
        {'value': 'tipo_movimiento', 'label': 'Tipo de Movimiento'},
        {'value': 'cantidad_anterior', 'label': 'Cantidad Anterior'},
        {'value': 'cantidad_nueva', 'label': 'Cantidad Nueva'},
        {'value': 'cantidad', 'label': 'Diferencia'},
        {'value': 'folio', 'label': 'Folio'},
        {'value': 'fecha_movimiento', 'label': 'Fecha de Movimiento'},
        {'value': 'usuario__username', 'label': 'Usuario'},
        {'value': 'motivo', 'label': 'Motivo'},
    ]
    
    contexto = {
        'movimientos': movimientos,
        'columnas_disponibles': columnas_disponibles,
    }
    
    return render(request, 'inventario/conteo_fisico/historial_conteos.html', contexto)


@login_required
def exportar_conteos_personalizado(request):
    """
    Vista para exportar conteos a Excel con campos personalizados.
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

            # 2️⃣ Consultar los datos (solo esos campos)
            datos = (
                MovimientoInventario.objects.filter(
                    tipo_movimiento__in=['AJUSTE_POSITIVO', 'AJUSTE_NEGATIVO']
                ).select_related('lote__producto', 'usuario')
                .values(*campos)
                .order_by('-fecha_movimiento')
            )

            datos_lista = list(datos)
            if not datos_lista:
                return JsonResponse({"error": "No hay datos para exportar"}, status=404)

            # 3️⃣ Procesar campos legibles
            for registro in datos_lista:
                # Tipo de movimiento legible
                if "tipo_movimiento" in registro:
                    tipo_mov = registro["tipo_movimiento"]
                    registro["tipo_movimiento"] = "Ajuste Positivo" if tipo_mov == 'AJUSTE_POSITIVO' else "Ajuste Negativo"

                # Fechas legibles
                for k, v in registro.items():
                    if isinstance(v, Decimal):
                        registro[k] = float(v)
                    elif isinstance(v, (date, datetime)):
                        registro[k] = v.strftime("%Y-%m-%d %H:%M") if isinstance(v, datetime) else v.strftime("%Y-%m-%d")
                    elif v is None:
                        registro[k] = ""

            # 4️⃣ Exportar a Excel respetando el orden de columnas
            df = pd.DataFrame(datos_lista)

            # Si hay orden definido, reordenamos las columnas
            columnas_finales = [col for col in campos if col in df.columns]
            df = df[columnas_finales]

            # Generar Excel
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; filename="conteos_fisicos.xlsx"'
            df.to_excel(response, index=False, sheet_name='Conteos')

            return response

        except Exception as e:
            return JsonResponse({"error": f"Error generando el reporte: {str(e)}"}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)
