"""
Reporte de logs de propuestas (LogPropuesta).
Permite visualizar las acciones específicas de usuarios sobre propuestas con filtros.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime, timedelta

User = get_user_model()


@login_required
def reporte_logs_propuestas(request):
    """
    Lista los registros de LogPropuesta con filtros por:
    - Usuario
    - Rango de fechas (desde / hasta)
    - Tipo de acción (texto exacto o contiene)
    - Texto en contenido (busca en accion y detalles)
    """
    from .pedidos_models import LogPropuesta

    qs = LogPropuesta.objects.select_related(
        'usuario',
        'propuesta',
        'propuesta__solicitud',
        'propuesta__solicitud__institucion_solicitante',
    ).order_by('-timestamp')

    # Filtros desde GET
    filtro_usuario_id = request.GET.get('usuario', '').strip()
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip()
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    filtro_accion = request.GET.get('accion', '').strip()
    filtro_texto = request.GET.get('texto', '').strip()

    if filtro_usuario_id:
        qs = qs.filter(usuario_id=filtro_usuario_id)
    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d').date()
            qs = qs.filter(timestamp__date__gte=fecha_desde)
        except ValueError:
            pass
    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d').date() + timedelta(days=1)
            qs = qs.filter(timestamp__date__lt=fecha_hasta)
        except ValueError:
            pass
    if filtro_accion:
        qs = qs.filter(accion__icontains=filtro_accion)
    if filtro_texto:
        qs = qs.filter(
            Q(accion__icontains=filtro_texto) | Q(detalles__icontains=filtro_texto)
        )

    # Valores distintos de "accion" para el selector (máximo 50 para no sobrecargar)
    acciones_distintas = list(
        LogPropuesta.objects.values_list('accion', flat=True).distinct().order_by('accion')[:50]
    )

    # Usuarios que tienen al menos un log (para el filtro)
    usuarios_con_logs = User.objects.filter(
        id__in=LogPropuesta.objects.filter(usuario_id__isnull=False).values_list('usuario_id', flat=True).distinct()
    ).order_by('username')

    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_registros': paginator.count,
        'acciones_distintas': acciones_distintas,
        'usuarios_con_logs': usuarios_con_logs,
        'filtro_usuario': filtro_usuario_id,
        'filtro_fecha_desde': filtro_fecha_desde,
        'filtro_fecha_hasta': filtro_fecha_hasta,
        'filtro_accion': filtro_accion,
        'filtro_texto': filtro_texto,
    }
    return render(request, 'inventario/reportes/reporte_logs_propuestas.html', context)
