"""
Vista para reporte detallado de inventario con las columnas:
ENTIDAD, CLUES, ORDEN DE SUMINISTRO, RFC, CLAVE, ESTADO DEL INSUMO,
INVENTARIO DISPONIBLE, LOTE, F_CAD, F_FAB, F_REC
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from datetime import date, datetime

from .models import Lote, Producto, Institucion, OrdenSuministro, Proveedor
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


@login_required
def reporte_inventario_detallado(request):
    """
    Reporte detallado de inventario con información de lotes, instituciones y órdenes de suministro.
    """
    
    # Obtener parámetros de filtro
    filtro_entidad = request.GET.get('entidad', '').strip()
    filtro_clues = request.GET.get('clues', '').strip()
    filtro_orden = request.GET.get('orden', '').strip()
    filtro_rfc = request.GET.get('rfc', '').strip()
    filtro_clave = request.GET.get('clave', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()
    filtro_lote = request.GET.get('lote', '').strip()
    excluir_sin_orden = request.GET.get('excluir_sin_orden', '') == 'si'

    # Query base con todas las relaciones necesarias
    lotes = Lote.objects.select_related(
        'producto',
        'institucion',
        'orden_suministro__proveedor'
    ).all()

    # Excluir lotes sin orden de suministro (opción del usuario)
    if excluir_sin_orden:
        lotes = lotes.exclude(orden_suministro__isnull=True)

    # Aplicar filtros
    if filtro_entidad:
        lotes = lotes.filter(institucion__denominacion__icontains=filtro_entidad)
    
    if filtro_clues:
        lotes = lotes.filter(institucion__clue__icontains=filtro_clues)
    
    if filtro_orden:
        lotes = lotes.filter(orden_suministro__numero_orden__icontains=filtro_orden)
    
    if filtro_rfc:
        lotes = lotes.filter(orden_suministro__proveedor__rfc__icontains=filtro_rfc)
    
    if filtro_clave:
        lotes = lotes.filter(producto__clave_cnis__icontains=filtro_clave)
    
    if filtro_estado:
        lotes = lotes.filter(estado=filtro_estado)
    
    if filtro_lote:
        lotes = lotes.filter(numero_lote__icontains=filtro_lote)

    # Ordenación por clic en encabezado (sort=columna&order=asc|desc)
    sort_column = request.GET.get('sort', '').strip()
    sort_order = request.GET.get('order', 'asc').strip().lower()
    if sort_order not in ('asc', 'desc'):
        sort_order = 'asc'
    # Mapeo: parámetro GET -> campo(s) order_by (prefijo - para desc)
    sort_map = {
        'entidad': 'institucion__denominacion',
        'clues': 'institucion__clue',
        'orden': 'orden_suministro__numero_orden',
        'rfc': 'orden_suministro__proveedor__rfc',
        'clave': 'producto__clave_cnis',
        'estado': 'estado',
        'inventario': 'cantidad_disponible',
        'lote': 'numero_lote',
        'f_cad': 'fecha_caducidad',
        'f_fab': 'fecha_fabricacion',
        'f_rec': 'fecha_recepcion',
    }
    if sort_column and sort_column in sort_map:
        order_field = sort_map[sort_column]
        if sort_order == 'desc':
            order_field = f'-{order_field}'
        lotes = lotes.order_by(order_field)
    else:
        # Orden por defecto
        lotes = lotes.order_by('institucion__denominacion', '-fecha_recepcion', 'producto__clave_cnis')

    # Paginación
    paginator = Paginator(lotes, 50)  # 50 items por página
    page = request.GET.get('page', 1)
    
    try:
        lotes_paginados = paginator.page(page)
    except PageNotAnInteger:
        lotes_paginados = paginator.page(1)
    except EmptyPage:
        lotes_paginados = paginator.page(paginator.num_pages)
    
    # Preparar datos para el template (f_cad = fecha caducidad, f_rec = fecha recepción; campos distintos del modelo)
    datos_reporte = []
    for lote in lotes_paginados:
        # Estado del insumo: leyenda (get_estado_display), no el dígito
        estado_texto = lote.get_estado_display() if lote.estado is not None else ''
        if not estado_texto and lote.estado is not None:
            estado_texto = str(lote.estado)

        # Fechas: usar explícitamente el campo correcto para cada columna
        fecha_caducidad_str = lote.fecha_caducidad.strftime('%d/%m/%Y') if getattr(lote, 'fecha_caducidad', None) else ''
        fecha_fabricacion_str = lote.fecha_fabricacion.strftime('%d/%m/%Y') if getattr(lote, 'fecha_fabricacion', None) else ''
        fecha_recepcion_str = lote.fecha_recepcion.strftime('%d/%m/%Y') if getattr(lote, 'fecha_recepcion', None) else ''

        datos_reporte.append({
            'entidad': 'CIUDAD DE MÉXICO',  # Leyenda fija (no almacén/institucion)
            'clues': lote.institucion.clue if lote.institucion else '',
            'orden_suministro': lote.orden_suministro.numero_orden if lote.orden_suministro else '',
            'rfc': lote.orden_suministro.proveedor.rfc if lote.orden_suministro and lote.orden_suministro.proveedor else '',
            'clave': lote.producto.clave_cnis if lote.producto else '',
            'estado_insumo': estado_texto,
            'inventario_disponible': lote.cantidad_disponible,
            'lote': lote.numero_lote,
            'f_cad': fecha_caducidad_str,
            'f_fab': fecha_fabricacion_str,
            'f_rec': fecha_recepcion_str,
        })
    
    # Query string base para enlaces de ordenación (conserva filtros, quita sort/order/page)
    get_copy = request.GET.copy()
    get_copy.pop('sort', None)
    get_copy.pop('order', None)
    get_copy.pop('page', None)
    sort_base_query = get_copy.urlencode()

    # Obtener listas para filtros
    instituciones = Institucion.objects.filter(activo=True).order_by('denominacion')[:100]

    context = {
        'datos_reporte': datos_reporte,
        'lotes_paginados': lotes_paginados,
        'filtro_entidad': filtro_entidad,
        'filtro_clues': filtro_clues,
        'filtro_orden': filtro_orden,
        'filtro_rfc': filtro_rfc,
        'filtro_clave': filtro_clave,
        'filtro_estado': filtro_estado,
        'filtro_lote': filtro_lote,
        'excluir_sin_orden': excluir_sin_orden,
        'sort_column': sort_column,
        'sort_order': sort_order,
        'sort_base_query': sort_base_query,
        'estados_lote': [
            (1, 'Disponible'),
            (4, 'Suspendido'),
            (5, 'Deteriorado'),
            (6, 'Caducado'),
        ],
    }
    
    return render(request, 'inventario/reportes/reporte_inventario_detallado.html', context)


@login_required
def exportar_inventario_detallado_excel(request):
    """
    Exporta el reporte de inventario detallado a Excel.
    """
    
    # Obtener los mismos filtros que en la vista
    filtro_entidad = request.GET.get('entidad', '').strip()
    filtro_clues = request.GET.get('clues', '').strip()
    filtro_orden = request.GET.get('orden', '').strip()
    filtro_rfc = request.GET.get('rfc', '').strip()
    filtro_clave = request.GET.get('clave', '').strip()
    filtro_estado = request.GET.get('estado', '').strip()
    filtro_lote = request.GET.get('lote', '').strip()
    excluir_sin_orden = request.GET.get('excluir_sin_orden', '') == 'si'

    # Query base con todas las relaciones necesarias
    lotes = Lote.objects.select_related(
        'producto',
        'institucion',
        'orden_suministro__proveedor'
    ).all()

    if excluir_sin_orden:
        lotes = lotes.exclude(orden_suministro__isnull=True)

    # Aplicar filtros (mismos que en la vista)
    if filtro_entidad:
        lotes = lotes.filter(institucion__denominacion__icontains=filtro_entidad)
    
    if filtro_clues:
        lotes = lotes.filter(institucion__clue__icontains=filtro_clues)
    
    if filtro_orden:
        lotes = lotes.filter(orden_suministro__numero_orden__icontains=filtro_orden)
    
    if filtro_rfc:
        lotes = lotes.filter(orden_suministro__proveedor__rfc__icontains=filtro_rfc)
    
    if filtro_clave:
        lotes = lotes.filter(producto__clave_cnis__icontains=filtro_clave)
    
    if filtro_estado:
        lotes = lotes.filter(estado=filtro_estado)
    
    if filtro_lote:
        lotes = lotes.filter(numero_lote__icontains=filtro_lote)
    
    # Ordenar por institución y fecha de recepción
    lotes = lotes.order_by('institucion__denominacion', '-fecha_recepcion', 'producto__clave_cnis')
    
    # Crear workbook Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario Detallado"
    
    # Estilos
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Encabezados
    headers = [
        'ENTIDAD',
        'CLUES',
        'ORDEN DE SUMINISTRO',
        'RFC',
        'CLAVE',
        'ESTADO DEL INSUMO',
        'INVENTARIO DISPONIBLE',
        'LOTE',
        'F_CAD',
        'F_FAB',
        'F_REC'
    ]
    
    # Escribir encabezados
    for col_num, header in enumerate(headers, 1):
        col_letter = get_column_letter(col_num)
        cell = ws[f"{col_letter}1"]
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # Escribir datos
    for row_num, lote in enumerate(lotes, 2):
        # Estado del insumo: leyenda (get_estado_display), no el dígito
        estado_texto = lote.get_estado_display() if lote.estado is not None else ''
        if not estado_texto and lote.estado is not None:
            estado_texto = str(lote.estado)

        # RFC como string para que Excel no lo interprete como número/fecha (evita truncar o modificar)
        rfc_val = ''
        if lote.orden_suministro and lote.orden_suministro.proveedor:
            rfc_val = (lote.orden_suministro.proveedor.rfc or '').strip()

        # Fechas: cada columna usa explícitamente su campo (F_CAD=caducidad, F_FAB=fabricación, F_REC=recepción)
        fecha_caducidad_str = lote.fecha_caducidad.strftime('%d/%m/%Y') if getattr(lote, 'fecha_caducidad', None) else ''
        fecha_fabricacion_str = lote.fecha_fabricacion.strftime('%d/%m/%Y') if getattr(lote, 'fecha_fabricacion', None) else ''
        fecha_recepcion_str = lote.fecha_recepcion.strftime('%d/%m/%Y') if getattr(lote, 'fecha_recepcion', None) else ''

        row_data = [
            'CIUDAD DE MÉXICO',  # Entidad fija (leyenda), no almacén/institucion
            lote.institucion.clue if lote.institucion else '',
            lote.orden_suministro.numero_orden if lote.orden_suministro else '',
            rfc_val,
            lote.producto.clave_cnis if lote.producto else '',
            estado_texto,
            lote.cantidad_disponible,
            lote.numero_lote,
            fecha_caducidad_str,   # F_CAD
            fecha_fabricacion_str, # F_FAB
            fecha_recepcion_str,   # F_REC
        ]

        for col_num, value in enumerate(row_data, 1):
            col_letter = get_column_letter(col_num)
            cell = ws[f"{col_letter}{row_num}"]
            cell.value = value
            cell.border = border
            # Columna RFC (D): formato texto para que no se corte ni se interprete como número/fecha
            if col_num == 4:
                cell.number_format = '@'
            if col_num == 7:  # INVENTARIO DISPONIBLE - alinear a la derecha
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
    
    # Ajustar ancho de columnas (RFC más ancho por posibles guiones y 13+ caracteres)
    column_widths = {
        'A': 22,  # ENTIDAD (CIUDAD DE MEXICO)
        'B': 15,  # CLUES
        'C': 25,  # ORDEN DE SUMINISTRO
        'D': 20,  # RFC (formato texto; ancho para RFC con guiones)
        'E': 20,  # CLAVE
        'F': 20,  # ESTADO DEL INSUMO
        'G': 20,  # INVENTARIO DISPONIBLE
        'H': 20,  # LOTE
        'I': 12,  # F_CAD
        'J': 12,  # F_FAB
        'K': 12,  # F_REC
    }
    
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width
    
    # Crear respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="reporte_inventario_detallado_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    wb.save(response)
    return response


# --- Carga masiva desde Excel (mismo layout que el reporte) ---

ESTADO_INSUMO_MAP = {
    'disponible': 1,
    'suspendido': 4,
    'deteriorado': 5,
    'caducado': 6,
}

HEADERS_INVENTARIO_DETALLADO = [
    'ENTIDAD', 'CLUES', 'ORDEN DE SUMINISTRO', 'RFC', 'CLAVE', 'ESTADO DEL INSUMO',
    'INVENTARIO DISPONIBLE', 'LOTE', 'F_CAD', 'F_FAB', 'F_REC',
]


def _parse_fecha_celda(val):
    """Convierte celda Excel a date. Acepta str 'dd/mm/yyyy' o 'dd/mm/yyyy HH:MM' o objeto date/datetime."""
    if val is None or (isinstance(val, str) and not val.strip()):
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    for fmt in ('%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _estado_to_int(estado_texto):
    if not estado_texto:
        return None
    key = str(estado_texto).strip().lower()
    return ESTADO_INSUMO_MAP.get(key)


@login_required
def carga_masiva_inventario_detallado(request):
    """
    Carga masiva: sube un Excel con el layout del reporte inventario detallado
    (ENTIDAD, CLUES, ORDEN DE SUMINISTRO, RFC, CLAVE, ESTADO DEL INSUMO,
     INVENTARIO DISPONIBLE, LOTE, F_CAD, F_FAB, F_REC) y actualiza los lotes
     existentes (identificados por CLUES + CLAVE + LOTE).
    """
    if request.method == 'GET':
        return render(request, 'inventario/reportes/carga_masiva_inventario_detallado.html', {})

    archivo = request.FILES.get('archivo_excel')
    if not archivo:
        messages.error(request, 'Debe seleccionar un archivo Excel.')
        return redirect('reportes:carga_masiva_inventario_detallado')

    if not archivo.name.lower().endswith(('.xlsx', '.xls')):
        messages.error(request, 'El archivo debe ser Excel (.xlsx).')
        return redirect('reportes:carga_masiva_inventario_detallado')

    dry_run = request.POST.get('dry_run') == '1'
    no_sobrescribir = request.POST.get('no_sobrescribir') == '1'

    try:
        wb = load_workbook(archivo, read_only=True, data_only=True)
        ws = wb.active
    except Exception as e:
        messages.error(request, f'No se pudo leer el Excel: {str(e)}')
        return redirect('reportes:carga_masiva_inventario_detallado')

    # Primera fila = encabezados
    header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
    if not header_row:
        messages.error(request, 'El archivo no tiene encabezados.')
        wb.close()
        return redirect('reportes:carga_masiva_inventario_detallado')

    header_row = [str(c).strip() if c is not None else '' for c in header_row]
    col_index = {h: i for i, h in enumerate(header_row) if h}

    # Índices esperados (nombres exactos o muy parecidos)
    def col(name, alternatives=None):
        for n in [name] + (alternatives or []):
            if n in col_index:
                return col_index[n]
            for k in col_index:
                if n.lower() in k.lower() or k.lower() in n.lower():
                    return col_index[k]
        return None

    idx_entidad = col('ENTIDAD')
    idx_clues = col('CLUES')
    idx_orden = col('ORDEN DE SUMINISTRO')
    idx_rfc = col('RFC')
    idx_clave = col('CLAVE')
    idx_estado = col('ESTADO DEL INSUMO')
    idx_inventario = col('INVENTARIO DISPONIBLE')
    idx_lote = col('LOTE')
    idx_f_cad = col('F_CAD')
    idx_f_fab = col('F_FAB')
    idx_f_rec = col('F_REC')

    if idx_clues is None or idx_clave is None or idx_lote is None:
        messages.error(request, 'Faltan columnas obligatorias: CLUES, CLAVE, LOTE.')
        wb.close()
        return redirect('reportes:carga_masiva_inventario_detallado')

    actualizados = 0
    no_encontrados = []
    errores = []

    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        row = list(row) if row else []
        max_idx = max((i for i in [idx_clues, idx_clave, idx_lote] if i is not None), default=0)
        if len(row) <= max_idx:
            continue
        clues = str(row[idx_clues]).strip() if idx_clues is not None and len(row) > idx_clues and row[idx_clues] else ''
        clave = str(row[idx_clave]).strip() if idx_clave is not None and len(row) > idx_clave and row[idx_clave] else ''
        numero_lote = str(row[idx_lote]).strip() if idx_lote is not None and len(row) > idx_lote and row[idx_lote] else ''
        if not clues or not clave or not numero_lote:
            continue

        try:
            institucion = Institucion.objects.filter(clue=clues).first()
            producto = Producto.objects.filter(clave_cnis=clave).first()
            if not institucion:
                no_encontrados.append(f"Fila {row_num}: CLUES '{clues}' no encontrado")
                continue
            if not producto:
                no_encontrados.append(f"Fila {row_num}: CLAVE '{clave}' no encontrado")
                continue

            lote = Lote.objects.filter(
                institucion=institucion,
                producto=producto,
                numero_lote=numero_lote,
            ).first()
            if not lote:
                no_encontrados.append(f"Fila {row_num}: Lote '{numero_lote}' / CLAVE {clave} / CLUES {clues} no existe")
                continue

            # Helper: solo asignar si no_sobrescribir está desactivado, o si el campo actual está "vacío"
            def _valor_actual_vacio(model_obj, attr, consider_cero_vacio=True):
                val = getattr(model_obj, attr, None)
                if val is None:
                    return True
                if isinstance(val, str) and not val.strip():
                    return True
                if consider_cero_vacio and isinstance(val, (int, float)) and val == 0:
                    return True
                return False

            # Actualizar campos (respeta no_sobrescribir: solo asigna si el campo actual está vacío)
            if idx_inventario is not None and len(row) > idx_inventario and row[idx_inventario] is not None:
                if not no_sobrescribir or _valor_actual_vacio(lote, 'cantidad_disponible'):
                    try:
                        val = int(float(row[idx_inventario]))
                        if val >= 0:
                            lote.cantidad_disponible = val
                    except (ValueError, TypeError):
                        pass
            if idx_estado is not None and len(row) > idx_estado:
                estado_int = _estado_to_int(row[idx_estado])
                if estado_int is not None and (not no_sobrescribir or _valor_actual_vacio(lote, 'estado')):
                    lote.estado = estado_int
            if idx_f_cad is not None and len(row) > idx_f_cad:
                f = _parse_fecha_celda(row[idx_f_cad])
                if f is not None and (not no_sobrescribir or _valor_actual_vacio(lote, 'fecha_caducidad', consider_cero_vacio=False)):
                    lote.fecha_caducidad = f
            if idx_f_fab is not None and len(row) > idx_f_fab:
                f = _parse_fecha_celda(row[idx_f_fab])
                if f is not None and (not no_sobrescribir or _valor_actual_vacio(lote, 'fecha_fabricacion', consider_cero_vacio=False)):
                    lote.fecha_fabricacion = f
            if idx_f_rec is not None and len(row) > idx_f_rec:
                f = _parse_fecha_celda(row[idx_f_rec])
                if f is not None and (not no_sobrescribir or _valor_actual_vacio(lote, 'fecha_recepcion', consider_cero_vacio=False)):
                    lote.fecha_recepcion = f
            if idx_rfc is not None and len(row) > idx_rfc and row[idx_rfc] is not None:
                rfc_val = str(row[idx_rfc]).strip()
                if rfc_val and (not no_sobrescribir or _valor_actual_vacio(lote, 'rfc_proveedor', consider_cero_vacio=False)):
                    lote.rfc_proveedor = rfc_val[:50]

            # Opcional: vincular OrdenSuministro si existe (solo si no_sobrescribir y actual vacío, o si no no_sobrescribir)
            if idx_orden is not None and len(row) > idx_orden and row[idx_orden]:
                orden_num = str(row[idx_orden]).strip()
                if orden_num and (not no_sobrescribir or not lote.orden_suministro_id):
                    if lote.rfc_proveedor:
                        proveedor = Proveedor.objects.filter(rfc=lote.rfc_proveedor).first()
                        if proveedor:
                            orden = OrdenSuministro.objects.filter(
                                numero_orden=orden_num,
                                proveedor=proveedor,
                            ).first()
                            if orden:
                                lote.orden_suministro = orden
                    if not lote.orden_suministro_id:
                        orden = OrdenSuministro.objects.filter(numero_orden=orden_num).first()
                        if orden:
                            lote.orden_suministro = orden

            if not dry_run:
                lote.save()
            actualizados += 1
        except Exception as e:
            errores.append(f"Fila {row_num}: {str(e)}")

    wb.close()

    if dry_run and actualizados:
        messages.info(request, f'[Dry-run] Se habrían actualizado {actualizados} lote(s). No se guardó nada.')
    elif actualizados:
        messages.success(request, f'Se actualizaron {actualizados} lote(s).')
    if no_encontrados:
        messages.warning(request, f'{len(no_encontrados)} registro(s) no encontrados (CLUES/CLAVE/Lote no existen). Ver detalle abajo.')
    if errores:
        messages.error(request, f'{len(errores)} error(es) al procesar filas.')

    context = {
        'actualizados': actualizados,
        'no_encontrados': no_encontrados[:100],
        'errores': errores[:100],
        'total_no_encontrados': len(no_encontrados),
        'total_errores': len(errores),
        'dry_run': dry_run,
        'no_sobrescribir': no_sobrescribir,
    }
    return render(request, 'inventario/reportes/carga_masiva_inventario_detallado.html', context)
