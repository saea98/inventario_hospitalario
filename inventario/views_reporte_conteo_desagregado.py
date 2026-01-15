"""
Reporte de Conteo de Almacén Desagregado por Lote y Caducidad
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Q
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from collections import defaultdict

from .models import Lote, LoteUbicacion, RegistroConteoFisico, Producto, Almacen


@login_required
def reporte_conteo_desagregado(request):
    """
    Reporte de conteo de almacén desagregado por producto, lote y caducidad.
    """
    
    # Obtener filtros
    filtro_fecha_desde = request.GET.get("fecha_desde", "")
    filtro_fecha_hasta = request.GET.get("fecha_hasta", "")
    filtro_almacen = request.GET.get("almacen", "")
    
    # Obtener todos los lotes
    lotes = Lote.objects.select_related(
        "producto",
        "institucion",
        "almacen"
    ).all()
    
    # Aplicar filtro de almacén
    if filtro_almacen:
        lotes = lotes.filter(almacen__nombre=filtro_almacen)
    
    # Obtener conteos
    conteos = RegistroConteoFisico.objects.select_related(
        "lote_ubicacion",
        "lote_ubicacion__lote",
        "lote_ubicacion__lote__producto"
    ).all()
    
    # Aplicar filtro de fechas a conteos
    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, "%Y-%m-%d").date()
            conteos = conteos.filter(fecha_creacion__date__gte=fecha_desde)
        except ValueError:
            pass
    
    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, "%Y-%m-%d").date()
            fecha_hasta = fecha_hasta + timedelta(days=1)
            conteos = conteos.filter(fecha_creacion__date__lt=fecha_hasta)
        except ValueError:
            pass
            
    # Agrupar conteos por lote
    conteos_dict = defaultdict(lambda: {
        "primer_conteo": 0,
        "segundo_conteo": 0,
        "tercer_conteo": 0
    })
    
    for conteo in conteos:
        if not conteo.lote_ubicacion or not conteo.lote_ubicacion.lote:
            continue
        
        lote_id = conteo.lote_ubicacion.lote.id
        
        if conteo.primer_conteo:
            conteos_dict[lote_id]["primer_conteo"] += conteo.primer_conteo
        if conteo.segundo_conteo:
            conteos_dict[lote_id]["segundo_conteo"] += conteo.segundo_conteo
        if conteo.tercer_conteo:
            conteos_dict[lote_id]["tercer_conteo"] += conteo.tercer_conteo
            
    # Combinar datos
    reporte_data = []
    consecutivo = 1
    
    for lote in lotes:
        if not lote.producto:
            continue
            
        conteo_info = conteos_dict.get(lote.id, {
            "primer_conteo": 0,
            "segundo_conteo": 0,
            "tercer_conteo": 0
        })
        
        reporte_data.append({
            "consecutivo": consecutivo,
            "fuente_financiamiento": "U013",
            "clave_cnis": lote.producto.clave_cnis,
            "descripcion": lote.producto.descripcion,
            "unidad_medida": lote.producto.unidad_medida or "PIEZA",
            "lote": lote.numero_lote,
            "fecha_caducidad": lote.fecha_caducidad.strftime("%d/%m/%Y") if lote.fecha_caducidad else "N/A",
            "cantidad": lote.cantidad_disponible,
            "importe": lote.cantidad_disponible * (lote.precio_unitario or 0),
            "cifra_primer_conteo": conteo_info.get("primer_conteo", 0),
            "cifra_segundo_conteo": conteo_info.get("segundo_conteo", 0),
            "cifra_tercer_conteo": conteo_info.get("tercer_conteo", 0),
        })
        
        consecutivo += 1
        
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(reporte_data, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Obtener almacenes
    almacenes = Almacen.objects.all().order_by("nombre")
    
    # Calcular totales
    total_cantidad = sum(r["cantidad"] for r in reporte_data)
    total_importe = sum(r["importe"] for r in reporte_data)
    total_primer_conteo = sum(r["cifra_primer_conteo"] for r in reporte_data)
    total_segundo_conteo = sum(r["cifra_segundo_conteo"] for r in reporte_data)
    total_tercer_conteo = sum(r["cifra_tercer_conteo"] for r in reporte_data)
    
    context = {
        "page_obj": page_obj,
        "total_registros": len(reporte_data),
        "total_cantidad": total_cantidad,
        "total_importe": total_importe,
        "total_primer_conteo": total_primer_conteo,
        "total_segundo_conteo": total_segundo_conteo,
        "total_tercer_conteo": total_tercer_conteo,
        "almacenes": almacenes,
        "filtro_fecha_desde": filtro_fecha_desde,
        "filtro_fecha_hasta": filtro_fecha_hasta,
        "filtro_almacen": filtro_almacen,
    }
    
    return render(request, "inventario/reporte_conteo_desagregado.html", context)
