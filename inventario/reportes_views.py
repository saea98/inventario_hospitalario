from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.paginator import Paginator
import openpyxl
from openpyxl.utils import get_column_letter


from .llegada_models import ItemLlegada
from .reportes_forms import ReporteEntradasForm


class ReporteEntradasView(LoginRequiredMixin, View):
    def get(self, request):
        form = ReporteEntradasForm(request.GET)
        items = ItemLlegada.objects.select_related("llegada", "producto", "llegada__proveedor").all()

        if form.is_valid():
            if form.cleaned_data.get("fecha_inicio"):
                items = items.filter(llegada__fecha_llegada_real__gte=form.cleaned_data["fecha_inicio"])
            if form.cleaned_data.get("fecha_fin"):
                items = items.filter(llegada__fecha_llegada_real__lte=form.cleaned_data["fecha_fin"])
            if form.cleaned_data.get("proveedor"):
                items = items.filter(llegada__proveedor=form.cleaned_data["proveedor"])
            if form.cleaned_data.get("clave"):
                items = items.filter(producto__clave_cnis__icontains=form.cleaned_data["clave"])
            if form.cleaned_data.get("lote"):
                items = items.filter(numero_lote__icontains=form.cleaned_data["lote"])

        if "export" in request.GET:
            if request.GET["export"] == "excel":
                return self.export_to_excel(items)

        # Paginación
        paginator = Paginator(items, 20)  # 20 items por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, "inventario/reportes/reporte_entradas.html", {"form": form, "page_obj": page_obj, "items": page_obj.object_list})

    def export_to_excel(self, items):
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = "attachment; filename=reporte_entradas.xlsx"

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Reporte de Entradas"

        headers = ["Fecha de Entrada", "Proveedor", "Clave", "Descripción", "Lote", "Fecha de Caducidad", "Cantidad Recibida"]
        for col_num, header in enumerate(headers, 1):
            col_letter = get_column_letter(col_num)
            cell = worksheet[f"{col_letter}1"]
            cell.value = header

        for row_num, item in enumerate(items, 2):
            worksheet[f"A{row_num}"] = item.llegada.fecha_llegada_real.strftime("%d/%m/%Y")
            worksheet[f"B{row_num}"] = item.llegada.proveedor.nombre
            worksheet[f"C{row_num}"] = item.producto.clave_cnis
            worksheet[f"D{row_num}"] = item.producto.descripcion
            worksheet[f"E{row_num}"] = item.numero_lote
            worksheet[f"F{row_num}"] = item.fecha_caducidad.strftime("%d/%m/%Y")
            worksheet[f"G{row_num}"] = item.cantidad_recibida

        workbook.save(response)
        return response


