"""
Vista: complementar reporte mensual de desplazamiento con surtimientos del mes.
"""

from datetime import date

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render

from .decorators_roles import requiere_rol
from .desplazamiento_mensual_service import (
    asegurar_menu_desplazamiento_mensual,
    complementar_workbook,
)

MESES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


@requiere_rol('Administrador', 'Gestor de Inventario', 'Supervisión', 'Analista')
def desplazamiento_mensual(request):
    """
    Sube el Excel del programa mensual (hoja Datos), indica mes/año,
    y descarga el mismo archivo complementado con surtimientos del sistema.
    """
    try:
        asegurar_menu_desplazamiento_mensual()
    except Exception:
        pass

    hoy = date.today()
    context = {
        'meses': MESES,
        'anio_actual': hoy.year,
        'mes_actual': hoy.month,
        'anios': list(range(hoy.year, hoy.year - 5, -1)),
        'stats': None,
    }

    if request.method != 'POST':
        return render(request, 'inventario/reportes/desplazamiento_mensual.html', context)

    archivo = request.FILES.get('archivo')
    mes_raw = request.POST.get('mes', '').strip()
    anio_raw = request.POST.get('anio', '').strip()

    context['mes_sel'] = mes_raw
    context['anio_sel'] = anio_raw

    if not archivo:
        messages.error(request, 'Selecciona el archivo Excel del programa mensual.')
        return render(request, 'inventario/reportes/desplazamiento_mensual.html', context)

    if not archivo.name.lower().endswith(('.xlsx', '.xlsm')):
        messages.error(request, 'El archivo debe ser Excel (.xlsx).')
        return render(request, 'inventario/reportes/desplazamiento_mensual.html', context)

    try:
        mes = int(mes_raw)
        anio = int(anio_raw)
        if mes < 1 or mes > 12:
            raise ValueError('mes inválido')
        if anio < 2020 or anio > hoy.year + 1:
            raise ValueError('año inválido')
    except (TypeError, ValueError):
        messages.error(request, 'Indica un mes y año válidos.')
        return render(request, 'inventario/reportes/desplazamiento_mensual.html', context)

    try:
        buf, stats = complementar_workbook(
            archivo,
            anio=anio,
            mes=mes,
            nombre_fuente=archivo.name,
        )
    except ValueError as e:
        messages.error(request, str(e))
        return render(request, 'inventario/reportes/desplazamiento_mensual.html', context)
    except Exception as e:
        messages.error(request, f'No se pudo procesar el archivo: {e}')
        return render(request, 'inventario/reportes/desplazamiento_mensual.html', context)

    mes_nombre = dict(MESES).get(mes, str(mes))
    filename = (
        f"desplazamiento_{mes_nombre.lower()}_{anio}_con_entregas.xlsx"
    )
    response = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    # flash no se ve bien en download-only; igual dejamos stats en query si quisieran
    # — devolvemos directo el archivo
    return response
