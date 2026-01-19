# ============================================================
# VISTAS PARA FLUJO DE DOS PASOS EN CREACIÓN DE CITAS
# ============================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
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
    
    Permite agregar múltiples líneas dinámicamente
    """
    
    # Verificar que vienen del paso 1
    cita_data = request.session.get('cita_paso1_data')
    if not cita_data:
        messages.error(request, 'Debes completar el paso 1 primero.')
        return redirect('logistica:crear_cita_paso1')
    
    if request.method == 'POST':
        # Obtener los detalles capturados
        detalles_json = request.POST.get('detalles_json', '[]')
        
        try:
            detalles = json.loads(detalles_json)
        except json.JSONDecodeError:
            detalles = []
        
        # Validar que haya al menos un detalle
        if not detalles:
            messages.error(request, 'Debes agregar al menos un detalle (remisión y clave de producto).')
            return redirect('logistica:crear_cita_paso2')
        
        # Crear la cita con los datos del paso 1
        try:
            proveedor = Proveedor.objects.get(id=cita_data['proveedor_id'])
            almacen = Almacen.objects.get(id=cita_data['almacen_id'])
            fecha_cita = datetime.fromisoformat(cita_data['fecha_cita'])
            
            # Crear la cita base
            cita = CitaProveedor(
                proveedor=proveedor,
                fecha_cita=fecha_cita,
                almacen=almacen,
                tipo_entrega=cita_data['tipo_entrega'],
                numero_orden_suministro=cita_data['numero_orden_suministro'],
                usuario_creacion=request.user,
                # Los siguientes campos quedan en blanco como se solicita
                numero_contrato='',
                tipo_transporte='',
                fecha_expedicion=None,
                fecha_limite_entrega=None,
            )
            cita.save()
            
            # Generar folio
            ServicioFolio.asignar_folio_a_cita(cita)
            
            # Procesar detalles (remisión y clave de producto)
            for detalle in detalles:
                remision = detalle.get('numero_orden_remision', '').strip()
                clave = detalle.get('clave_medicamento', '').strip()
                
                # Actualizar la cita con los datos del primer detalle
                # (o crear múltiples citas si es necesario)
                if remision or clave:
                    # Por ahora, guardamos el primer detalle en la cita
                    if not cita.numero_orden_remision:
                        cita.numero_orden_remision = remision
                        cita.clave_medicamento = clave
                        cita.save()
            
            # Enviar notificación
            notificaciones.notificar_cita_creada(cita)
            
            # Limpiar sesión
            if 'cita_paso1_data' in request.session:
                del request.session['cita_paso1_data']
            request.session.modified = True
            
            messages.success(request, f'✓ Cita creada exitosamente con {cita.proveedor.razon_social}')
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
            messages.error(request, "Verifica el archivo seleccionado")
    else:
        form = CargaMasivaCitasForm()
    
    context = {
        'form': form,
        'page_title': 'Crear Cita - Carga Masiva'
    }
    return render(request, 'inventario/citas/crear_masiva.html', context)
