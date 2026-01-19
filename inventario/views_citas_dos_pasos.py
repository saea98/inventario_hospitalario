# ============================================================
# VISTAS PARA FLUJO DE DOS PASOS EN CREACIÓN DE CITAS
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from datetime import datetime
import json

from .models import CitaProveedor, Proveedor, Almacen, Producto
from .forms import CitaProveedorPaso1Form, CitaProveedorDetalleForm, CargaMasivaCitasForm
from .servicio_folio import ServicioFolio
from .servicios_notificaciones import ServicioNotificaciones
notificaciones = ServicioNotificaciones()


@login_required
def crear_cita_paso1(request):
    """
    PASO 1: Capturar datos generales de la cita
    - Proveedor
    - Fecha y Hora (default 08:00)
    - Almacén
    - Tipo de Entrega
    - Número de Orden de Suministro
    """
    
    if request.method == 'POST':
        form = CitaProveedorPaso1Form(request.POST)
        
        if form.is_valid():
            # Guardar en sesión los datos del paso 1
            request.session['cita_paso1_data'] = {
                'proveedor_id': form.cleaned_data['proveedor'].id,
                'fecha_cita': form.cleaned_data['fecha_cita'].isoformat(),
                'almacen_id': form.cleaned_data['almacen'].id,
                'tipo_entrega': form.cleaned_data['tipo_entrega'],
                'numero_orden_suministro': form.cleaned_data['numero_orden_suministro'] or '',
            }
            request.session.modified = True
            
            # Ir al paso 2
            return redirect('logistica:crear_cita_paso2')
        else:
            messages.error(request, 'Error en los datos generales. Verifica los campos.')
    else:
        form = CitaProveedorPaso1Form()
    
    context = {
        'form': form,
        'paso': 1,
        'page_title': 'Crear Cita - Paso 1: Datos Generales'
    }
    return render(request, 'inventario/citas/crear_paso1.html', context)


@login_required
def crear_cita_paso2(request):
    """
    PASO 2: Capturar detalles de la cita (líneas)
    - Remisión
    - Clave de Producto
    
    Crea UNA CITA POR CADA REMISIÓN capturada
    """
    
    # Verificar que vienen del paso 1
    cita_data = request.session.get('cita_paso1_data')
    if not cita_data:
        messages.error(request, 'Debes completar el paso 1 primero.')
        return redirect('logistica:crear_cita_paso1')
    
    if request.method == 'POST':
        # Obtener los detalles capturados
        detalles_json = request.POST.get('detalles_json', '[]')
        print(f'[CREAR_CITA_PASO2] JSON recibido: {detalles_json}')
        
        try:
            detalles = json.loads(detalles_json)
            print(f'[CREAR_CITA_PASO2] Detalles parseados: {len(detalles)} elementos')
            for i, detalle in enumerate(detalles):
                print(f'[CREAR_CITA_PASO2]   Detalle {i+1}: remision={detalle.get("numero_orden_remision")}, clave={detalle.get("clave_medicamento")}')
        except json.JSONDecodeError as e:
            print(f'[CREAR_CITA_PASO2] Error al parsear JSON: {e}')
            detalles = []
        
        # Validar que haya al menos un detalle
        if not detalles:
            messages.error(request, 'Debes agregar al menos un detalle (remisión y clave de producto).')
            return redirect('logistica:crear_cita_paso2')
        
        # Crear múltiples citas (una por cada remisión)
        try:
            proveedor = Proveedor.objects.get(id=cita_data['proveedor_id'])
            almacen = Almacen.objects.get(id=cita_data['almacen_id'])
            fecha_cita = datetime.fromisoformat(cita_data['fecha_cita'])
            
            citas_creadas = []
            
            # Crear una cita por cada remisión/detalle
            for i, detalle in enumerate(detalles):
                cita = CitaProveedor(
                    proveedor=proveedor,
                    fecha_cita=fecha_cita,
                    almacen=almacen,
                    tipo_entrega=cita_data['tipo_entrega'],
                    numero_orden_suministro=cita_data['numero_orden_suministro'],
                    usuario_creacion=request.user,
                    # Guardar los datos de esta remisión específica
                    numero_orden_remision=detalle.get('numero_orden_remision', '').strip(),
                    clave_medicamento=detalle.get('clave_medicamento', '').strip(),
                    # Los siguientes campos quedan en blanco como se solicita
                    numero_contrato='',
                    tipo_transporte='',
                    fecha_expedicion=None,
                    fecha_limite_entrega=None,
                    # Guardar todos los detalles en JSON para referencia
                    detalles_json=detalles,
                )
                cita.save()
                
                # Generar folio
                ServicioFolio.asignar_folio_a_cita(cita)
                citas_creadas.append(cita)
                
                print(f'[CREAR_CITA_PASO2] Cita {i+1} guardada con ID {cita.id}')
                print(f'[CREAR_CITA_PASO2]   Remisión: {detalle.get("numero_orden_remision")}, Clave: {detalle.get("clave_medicamento")}')
            
            # Enviar notificación
            for cita in citas_creadas:
                notificaciones.notificar_cita_creada(cita)
            
            # Limpiar sesión
            if 'cita_paso1_data' in request.session:
                del request.session['cita_paso1_data']
            request.session.modified = True
            
            cantidad = len(citas_creadas)
            messages.success(request, f'✓ {cantidad} cita(s) creada(s) exitosamente con {proveedor.razon_social}')
            return redirect('logistica:lista_citas')
        
        except (Proveedor.DoesNotExist, Almacen.DoesNotExist) as e:
            messages.error(request, f'Error: Proveedor o Almacén no encontrado.')
            return redirect('logistica:crear_cita_paso1')
        except Exception as e:
            messages.error(request, f'Error al crear la cita: {str(e)}')
            return redirect('logistica:crear_cita_paso1')
    
    # Preparar contexto con datos del paso 1
    proveedor = Proveedor.objects.get(id=cita_data['proveedor_id'])
    almacen = Almacen.objects.get(id=cita_data['almacen_id'])
    
    context = {
        'paso': 2,
        'page_title': 'Crear Cita - Paso 2: Detalles',
        'proveedor': proveedor,
        'almacen': almacen,
        'numero_orden_suministro': cita_data['numero_orden_suministro'],
        'tipo_entrega': cita_data['tipo_entrega'],
        'fecha_cita': cita_data['fecha_cita'],
    }
    return render(request, 'inventario/citas/crear_paso2.html', context)


@login_required
@require_http_methods(["POST"])
def agregar_detalle_cita(request):
    """
    AJAX: Agregar un nuevo detalle (línea) a la cita
    Retorna HTML para la nueva línea
    """
    
    numero_linea = int(request.POST.get('numero_linea', 1))
    
    # Generar HTML para la nueva línea
    html = f'''
    <div class="detalle-linea" data-linea="{numero_linea}">
        <div class="row g-2 mb-3">
            <div class="col-md-5">
                <input type="text" 
                       class="form-control numero_orden_remision" 
                       placeholder="Número de remisión"
                       data-linea="{numero_linea}">
            </div>
            <div class="col-md-5">
                <input type="text" 
                       class="form-control clave_medicamento" 
                       placeholder="Clave de producto (CNIS)"
                       data-linea="{numero_linea}">
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-danger btn-sm w-100 eliminar-linea" 
                        data-linea="{numero_linea}">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </div>
        </div>
    </div>
    '''
    
    return JsonResponse({'html': html, 'numero_linea': numero_linea})


@login_required
@require_http_methods(["GET"])
def buscar_productos_cita(request):
    """
    API para buscar productos por clave CNIS
    Retorna lista de productos para Select2
    """
    
    try:
        busqueda = request.GET.get('q', '').strip()
        
        # Necesita al menos 2 caracteres
        if len(busqueda) < 2:
            return JsonResponse({'results': []})
        
        # Buscar productos por clave CNIS o descripción
        productos = Producto.objects.filter(
            Q(clave_cnis__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        ).values('id', 'clave_cnis', 'descripcion').order_by('clave_cnis')[:20]
        
        # Formatear para Select2
        results = []
        for producto in productos:
            results.append({
                'id': producto['clave_cnis'],
                'text': f"{producto['clave_cnis']} - {producto['descripcion'][:60]}"
            })
        
        return JsonResponse({'results': results})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def crear_cita_masiva(request):
    """
    Carga masiva de citas desde archivo CSV
    """
    
    if request.method == 'POST':
        form = CargaMasivaCitasForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                from .citas_masivas import CargaMasivaCitas
                
                archivo = request.FILES['archivo']
                cargador = CargaMasivaCitas()
                resultado = cargador.procesar_archivo(archivo)
                
                if resultado['exito']:
                    messages.success(
                        request,
                        f"✓ Carga completada: {resultado['citas_creadas']} citas creadas"
                    )
                    
                    if resultado['advertencias']:
                        for adv in resultado['advertencias'][:5]:
                            messages.warning(request, f"⚠️ {adv}")
                        if len(resultado['advertencias']) > 5:
                            messages.warning(request, f"⚠️ ...y {len(resultado['advertencias']) - 5} advertencias más")
                    
                    return redirect('logistica:lista_citas')
                else:
                    for error in resultado['errores']:
                        messages.error(request, f"❌ {error}")
                    
                    for adv in resultado['advertencias'][:5]:
                        messages.warning(request, f"⚠️ {adv}")
            
            except Exception as e:
                messages.error(request, f"Error al procesar archivo: {str(e)}")
        else:
            messages.error(request, 'Formulario inválido.')
    else:
        form = CargaMasivaCitasForm()
    
    return render(request, 'inventario/citas/crear_masiva.html', {'form': form})


@login_required
def editar_cita_paso1(request, pk):
    """
    PASO 1 EDICIÓN: Editar datos generales de la cita
    """
    cita = get_object_or_404(CitaProveedor, pk=pk)
    
    if cita.estado != 'programada':
        messages.warning(request, f'No se puede editar una cita en estado {cita.get_estado_display()}')
        return redirect('logistica:lista_citas')
    
    if request.method == 'POST':
        form = CitaProveedorPaso1Form(request.POST)
        
        if form.is_valid():
            # Guardar en sesión los datos del paso 1
            request.session['cita_paso1_data'] = {
                'proveedor_id': form.cleaned_data['proveedor'].id,
                'fecha_cita': form.cleaned_data['fecha_cita'].isoformat(),
                'almacen_id': form.cleaned_data['almacen'].id,
                'tipo_entrega': form.cleaned_data['tipo_entrega'],
                'numero_orden_suministro': form.cleaned_data['numero_orden_suministro'] or '',
            }
            request.session['cita_edicion_id'] = pk
            request.session.modified = True
            
            # Ir al paso 2
            return redirect('logistica:editar_cita_paso2', pk=pk)
        else:
            messages.error(request, 'Error en los datos generales. Verifica los campos.')
    else:
        form = CitaProveedorPaso1Form(initial={
            'proveedor': cita.proveedor,
            'fecha_cita': cita.fecha_cita,
            'almacen': cita.almacen,
            'tipo_entrega': cita.tipo_entrega,
            'numero_orden_suministro': cita.numero_orden_suministro,
        })
    
    context = {
        'form': form,
        'paso': 1,
        'page_title': 'Editar Cita - Paso 1: Datos Generales',
        'cita': cita,
    }
    return render(request, 'inventario/citas/editar_paso1.html', context)


@login_required
def editar_cita_paso2(request, pk):
    """
    PASO 2 EDICIÓN: Editar detalles de la cita
    """
    cita = get_object_or_404(CitaProveedor, pk=pk)
    
    if cita.estado != 'programada':
        messages.warning(request, f'No se puede editar una cita en estado {cita.get_estado_display()}')
        return redirect('logistica:lista_citas')
    
    # Verificar que vienen del paso 1
    cita_data = request.session.get('cita_paso1_data')
    if not cita_data:
        messages.error(request, 'Debes completar el paso 1 primero.')
        return redirect('logistica:editar_cita', pk=pk)
    
    if request.method == 'POST':
        # Obtener los detalles capturados
        detalles_json = request.POST.get('detalles_json', '[]')
        print(f'[EDITAR_CITA_PASO2] JSON recibido: {detalles_json}')
        
        try:
            detalles = json.loads(detalles_json)
            print(f'[EDITAR_CITA_PASO2] Detalles parseados: {len(detalles)} elementos')
        except json.JSONDecodeError as e:
            print(f'[EDITAR_CITA_PASO2] Error al parsear JSON: {e}')
            detalles = []
        
        # Validar que haya al menos un detalle
        if not detalles:
            messages.error(request, 'Debes agregar al menos un detalle (remisión y clave de producto).')
            return redirect('logistica:editar_cita_paso2', pk=pk)
        
        # Actualizar la cita
        try:
            proveedor = Proveedor.objects.get(id=cita_data['proveedor_id'])
            almacen = Almacen.objects.get(id=cita_data['almacen_id'])
            fecha_cita = datetime.fromisoformat(cita_data['fecha_cita'])
            
            cita.proveedor = proveedor
            cita.fecha_cita = fecha_cita
            cita.almacen = almacen
            cita.tipo_entrega = cita_data['tipo_entrega']
            cita.numero_orden_suministro = cita_data['numero_orden_suministro']
            
            # Guardar todos los detalles en JSON
            cita.detalles_json = detalles
            
            # Guardar el primer detalle en los campos simples (para compatibilidad)
            if detalles:
                primer_detalle = detalles[0]
                cita.numero_orden_remision = primer_detalle.get('numero_orden_remision', '').strip()
                cita.clave_medicamento = primer_detalle.get('clave_medicamento', '').strip()
            
            cita.save()
            print(f'[EDITAR_CITA_PASO2] Cita actualizada con ID {cita.id}')
            
            # Limpiar sesión
            if 'cita_paso1_data' in request.session:
                del request.session['cita_paso1_data']
            if 'cita_edicion_id' in request.session:
                del request.session['cita_edicion_id']
            request.session.modified = True
            
            messages.success(request, f'✓ Cita actualizada exitosamente')
            return redirect('logistica:lista_citas')
        
        except (Proveedor.DoesNotExist, Almacen.DoesNotExist) as e:
            messages.error(request, f'Error: Proveedor o Almacén no encontrado.')
            return redirect('logistica:editar_cita', pk=pk)
        except Exception as e:
            messages.error(request, f'Error al actualizar la cita: {str(e)}')
            return redirect('logistica:editar_cita', pk=pk)
    
    # Preparar contexto con datos del paso 1
    proveedor = Proveedor.objects.get(id=cita_data['proveedor_id'])
    almacen = Almacen.objects.get(id=cita_data['almacen_id'])
    
    context = {
        'paso': 2,
        'page_title': 'Editar Cita - Paso 2: Detalles',
        'proveedor': proveedor,
        'almacen': almacen,
        'numero_orden_suministro': cita_data['numero_orden_suministro'],
        'tipo_entrega': cita_data['tipo_entrega'],
        'fecha_cita': cita_data['fecha_cita'],
        'cita': cita,
        'detalles_json': json.dumps(cita.detalles_json) if cita.detalles_json else '[]',
    }
    return render(request, 'inventario/citas/editar_paso2.html', context)
