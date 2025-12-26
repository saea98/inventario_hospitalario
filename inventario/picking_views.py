from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from .pedidos_models import PropuestaPedido

@login_required
def picking_propuesta(request, propuesta_id):
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    orden_picking = request.GET.get("orden", "ubicacion")

    items_picking = []
    for item in propuesta.items.all():
        for lote_asignado in item.lotes_asignados.filter(surtido=False):
            lote_ubicacion = lote_asignado.lote_ubicacion
            lote = lote_ubicacion.lote
            items_picking.append({
                "item_id": item.id,
                "lote_asignado_id": lote_asignado.id,
                "producto": lote.producto.descripcion,
                "cantidad": lote_asignado.cantidad_asignada,
                "lote_numero": lote.numero_lote,
                "almacen": lote_ubicacion.ubicacion.almacen.nombre,
                "almacen_id": lote_ubicacion.ubicacion.almacen_id,
                "ubicacion": lote_ubicacion.ubicacion.codigo,
                "ubicacion_id": lote_ubicacion.ubicacion_id,
                "clave_cnis": lote.producto.clave_cnis,
            })

    if orden_picking == "producto":
        items_picking.sort(key=lambda x: x["producto"])
    else:
        items_picking.sort(key=lambda x: x["ubicacion"])

    context = {
        "propuesta": propuesta,
        "items_picking": items_picking,
        "orden_picking": orden_picking,
        "page_title": f"Picking para Propuesta {propuesta.solicitud.folio}",
    }
    return render(request, "inventario/picking/picking_propuesta.html", context)

@login_required
def imprimir_hoja_surtido(request, propuesta_id):
    propuesta = get_object_or_404(PropuestaPedido, id=propuesta_id)
    template_path = "inventario/picking/hoja_surtido_pdf.html"
    context = {"propuesta": propuesta}

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename=hoja_surtido_{propuesta.solicitud.folio}.pdf"

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("We had some errors <pre>" + html + "</pre>")
    return response
