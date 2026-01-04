from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import json

from .models_logs import LogSistema


def es_admin_o_superuser(user):
    """Verifica si el usuario es admin o superuser"""
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(es_admin_o_superuser)
def lista_logs(request):
    """Vista para listar logs del sistema"""
    
    # Filtros
    nivel = request.GET.get('nivel', '')
    tipo = request.GET.get('tipo', '')
    resuelto = request.GET.get('resuelto', '')
    dias = request.GET.get('dias', '7')
    
    # Query base
    logs = LogSistema.objects.all()
    
    # Filtrar por fecha
    try:
        dias_int = int(dias)
        fecha_limite = timezone.now() - timedelta(days=dias_int)
        logs = logs.filter(fecha_creacion__gte=fecha_limite)
    except:
        pass
    
    # Filtrar por nivel
    if nivel:
        logs = logs.filter(nivel=nivel)
    
    # Filtrar por tipo
    if tipo:
        logs = logs.filter(tipo=tipo)
    
    # Filtrar por estado de resolución
    if resuelto == 'si':
        logs = logs.filter(resuelto=True)
    elif resuelto == 'no':
        logs = logs.filter(resuelto=False)
    
    # Estadísticas
    total_logs = logs.count()
    logs_por_nivel = logs.values('nivel').annotate(count=Count('id'))
    logs_por_tipo = logs.values('tipo').annotate(count=Count('id'))
    logs_no_resueltos = logs.filter(resuelto=False).count()
    
    # Paginación simple
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except:
        page = 1
    
    items_por_pagina = 50
    inicio = (page - 1) * items_por_pagina
    fin = inicio + items_por_pagina
    
    logs_paginados = logs[inicio:fin]
    total_paginas = (total_logs + items_por_pagina - 1) // items_por_pagina
    
    context = {
        'logs': logs_paginados,
        'total_logs': total_logs,
        'logs_por_nivel': logs_por_nivel,
        'logs_por_tipo': logs_por_tipo,
        'logs_no_resueltos': logs_no_resueltos,
        'nivel_filtro': nivel,
        'tipo_filtro': tipo,
        'resuelto_filtro': resuelto,
        'dias_filtro': dias,
        'page': page,
        'total_paginas': total_paginas,
        'niveles': LogSistema.NIVEL_CHOICES,
        'tipos': LogSistema.TIPO_CHOICES,
    }
    
    return render(request, 'inventario/logs/lista_logs.html', context)


@login_required
@user_passes_test(es_admin_o_superuser)
def detalle_log(request, pk):
    """Vista para ver detalle de un log"""
    
    log = get_object_or_404(LogSistema, pk=pk)
    
    context = {
        'log': log,
    }
    
    return render(request, 'inventario/logs/detalle_log.html', context)


@login_required
@user_passes_test(es_admin_o_superuser)
@require_http_methods(["POST"])
def marcar_resuelto(request, pk):
    """Marcar un log como resuelto"""
    
    log = get_object_or_404(LogSistema, pk=pk)
    notas = request.POST.get('notas', '')
    
    log.marcar_resuelto(notas)
    
    return JsonResponse({
        'success': True,
        'message': 'Log marcado como resuelto'
    })


@login_required
@user_passes_test(es_admin_o_superuser)
@require_http_methods(["POST"])
def limpiar_logs(request):
    """Limpiar logs antiguos"""
    
    dias = request.POST.get('dias', '30')
    
    try:
        dias_int = int(dias)
        fecha_limite = timezone.now() - timedelta(days=dias_int)
        
        # Solo eliminar logs resueltos
        logs_eliminados = LogSistema.objects.filter(
            fecha_creacion__lt=fecha_limite,
            resuelto=True
        ).delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Se eliminaron {logs_eliminados[0]} logs resueltos'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@user_passes_test(es_admin_o_superuser)
def api_logs_recientes(request):
    """API para obtener logs recientes (para dashboard)"""
    
    limite = request.GET.get('limite', '10')
    
    try:
        limite = int(limite)
    except:
        limite = 10
    
    logs = LogSistema.objects.filter(
        resuelto=False,
        nivel__in=['ERROR', 'CRITICAL']
    )[:limite]
    
    datos = []
    for log in logs:
        datos.append({
            'id': log.id,
            'nivel': log.nivel,
            'tipo': log.tipo,
            'titulo': log.titulo,
            'mensaje': log.mensaje[:100],
            'fecha': log.fecha_creacion.isoformat(),
            'url': f'/admin/logs/{log.id}/',
        })
    
    return JsonResponse({
        'success': True,
        'logs': datos,
        'total': LogSistema.objects.filter(resuelto=False).count()
    })
