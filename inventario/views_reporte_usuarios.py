"""
Reporte de usuarios del sistema con resumen de actividades.
Usa la tabla LogSistema y los modelos que ya tienen usuario_id (sin migraciones).
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()


def _count_by_user(model, user_attr):
    """Retorna dict user_id -> count para el modelo y el campo FK a User."""
    if not hasattr(model, user_attr):
        return {}
    qs = (
        model.objects.filter(**{f'{user_attr}__isnull': False})
        .values(user_attr)
        .annotate(c=Count('id'))
    )
    return {r[user_attr]: r['c'] for r in qs}


@login_required
def reporte_usuarios_actividades(request):
    """
    Reporte de usuarios del sistema con resumen de actividades por sección.
    Usa únicamente tablas existentes (LogSistema y modelos con usuario_id).
    """
    from .models import (
        LogSistema,
        CitaProveedor,
        ConteoFisico,
        OrdenTraslado,
        DevolucionProveedor,
        ItemDevolucion,
        SalidaExistencias,
        DistribucionArea,
        ListaRevision,
        RegistroConteoFisico,
        MovimientoInventario,
    )
    from .llegada_models import LlegadaProveedor
    from .pedidos_models import (
        SolicitudPedido,
        PropuestaPedido,
        LoteAsignado,
        LogPropuesta,
        LogErrorPedido,
    )

    # Actividades a contar: (modelo, nombre del campo FK a User, etiqueta para la tabla)
    actividades = [
        (SolicitudPedido, 'usuario_solicitante', 'Pedidos solicitados'),
        (SolicitudPedido, 'usuario_validacion', 'Pedidos validados'),
        (PropuestaPedido, 'usuario_generacion', 'Propuestas generadas'),
        (PropuestaPedido, 'usuario_revision', 'Propuestas revisadas'),
        (PropuestaPedido, 'usuario_surtimiento', 'Propuestas surtidas'),
        (LoteAsignado, 'usuario_surtido', 'Ítems picking (recogidos)'),
        (CitaProveedor, 'usuario_creacion', 'Citas creadas'),
        (CitaProveedor, 'usuario_autorizacion', 'Citas autorizadas'),
        (CitaProveedor, 'usuario_cancelacion', 'Citas canceladas'),
        (ConteoFisico, 'usuario_creacion', 'Conteos creados'),
        (OrdenTraslado, 'usuario_creacion', 'Traslados creados'),
        (LlegadaProveedor, 'creado_por', 'Llegadas creadas'),
        (LlegadaProveedor, 'usuario_calidad', 'Llegadas (calidad)'),
        (LlegadaProveedor, 'usuario_facturacion', 'Llegadas (facturación)'),
        (LlegadaProveedor, 'usuario_supervision', 'Llegadas (supervisión)'),
        (LlegadaProveedor, 'usuario_ubicacion', 'Llegadas (ubicación)'),
        (DevolucionProveedor, 'usuario_creacion', 'Devoluciones creadas'),
        (DevolucionProveedor, 'usuario_autorizo', 'Devoluciones autorizadas'),
        (ItemDevolucion, 'usuario_inspeccion', 'Items devolución inspeccionados'),
        (SalidaExistencias, 'usuario_autoriza', 'Salidas autorizadas'),
        (DistribucionArea, 'usuario_creacion', 'Distribuciones creadas'),
        (ListaRevision, 'usuario_creacion', 'Listas revisión creadas'),
        (ListaRevision, 'usuario_validacion', 'Listas revisión validadas'),
        (RegistroConteoFisico, 'usuario_creacion', 'Registros conteo creados'),
        (MovimientoInventario, 'usuario', 'Movimientos inventario'),
        (MovimientoInventario, 'usuario_anulacion', 'Movimientos anulados'),
        (LogSistema, 'usuario', 'Logs sistema'),
        (LogPropuesta, 'usuario', 'Acciones en propuestas'),
        (LogErrorPedido, 'usuario', 'Errores pedido'),
    ]

    # Construir dict global user_id -> { etiqueta: count }
    counts_by_user = {}
    for model, user_attr, label in actividades:
        try:
            d = _count_by_user(model, user_attr)
        except Exception:
            d = {}
        for uid, c in d.items():
            if uid not in counts_by_user:
                counts_by_user[uid] = {}
            counts_by_user[uid][label] = c

    # Usuarios activos (o todos si se pide)
    solo_activos = request.GET.get('activos', '1') == '1'
    usuarios = User.objects.all().order_by('username')
    if solo_activos:
        usuarios = usuarios.filter(is_active=True)

    # Armar lista para la tabla: por cada usuario, lista de conteos en el mismo orden que etiquetas
    etiquetas = [label for _, _, label in actividades]
    filas = []
    for u in usuarios:
        counts = counts_by_user.get(u.id, {})
        counts_list = [counts.get(label, 0) for label in etiquetas]
        filas.append({
            'usuario': u,
            'counts': counts,
            'counts_list': counts_list,
            'etiquetas': etiquetas,
        })

    context = {
        'filas': filas,
        'etiquetas': etiquetas,
        'solo_activos': solo_activos,
    }
    return render(request, 'inventario/reportes/reporte_usuarios_actividades.html', context)
