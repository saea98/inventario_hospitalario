"""
Exportar / importar propuestas de pedido entre ambientes (ej. calidad → productivo).

El JSON usa claves de negocio (CLUE, clave CNIS, número de lote, código de ubicación,
nombre de almacén) para que en productivo se resuelvan los UUID reales del inventario.
"""

from __future__ import annotations

import json
import logging
from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import Institucion, Almacen, Producto, Lote, LoteUbicacion
from .pedidos_models import (
    SolicitudPedido,
    ItemSolicitud,
    PropuestaPedido,
    ItemPropuesta,
    LoteAsignado,
)
from .fase5_utils import generar_movimientos_suministro
from .propuesta_utils import sincronizar_cantidades_surtidas_items_propuesta

logger = logging.getLogger(__name__)

EXPORT_VERSION = 1


def _json_default(obj):
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(str(type(obj)))


def serializar_propuesta_para_export(propuesta_id) -> dict[str, Any]:
    """Genera el diccionario exportable (listo para json.dump)."""
    propuesta = (
        PropuestaPedido.objects.select_related(
            'solicitud__institucion_solicitante',
            'solicitud__almacen_destino',
        )
        .prefetch_related(
            'solicitud__items__producto',
            'items__producto',
            'items__item_solicitud',
            'items__lotes_asignados__lote_ubicacion__lote',
            'items__lotes_asignados__lote_ubicacion__ubicacion__almacen',
        )
        .get(id=propuesta_id)
    )
    sol = propuesta.solicitud
    inst = sol.institucion_solicitante
    alm = sol.almacen_destino

    items_sol = []
    for it in sol.items.all().order_by('producto__clave_cnis'):
        items_sol.append(
            {
                'clave_cnis': it.producto.clave_cnis,
                'cantidad_solicitada': it.cantidad_solicitada,
                'cantidad_aprobada': it.cantidad_aprobada,
                'justificacion_cambio': it.justificacion_cambio or '',
            }
        )

    items_prop = []
    for ip in propuesta.items.all().order_by('producto__clave_cnis'):
        lotes = []
        for la in ip.lotes_asignados.select_related(
            'lote_ubicacion__lote', 'lote_ubicacion__ubicacion__almacen'
        ).all():
            lu = la.lote_ubicacion
            lotes.append(
                {
                    'numero_lote': lu.lote.numero_lote,
                    'ubicacion_codigo': (lu.ubicacion.codigo or '').strip(),
                    'almacen_nombre': (lu.ubicacion.almacen.nombre or '').strip(),
                    'cantidad_asignada': la.cantidad_asignada,
                }
            )
        items_prop.append(
            {
                'clave_cnis': ip.producto.clave_cnis,
                'cantidad_solicitada': ip.cantidad_solicitada,
                'cantidad_disponible': ip.cantidad_disponible,
                'cantidad_propuesta': ip.cantidad_propuesta,
                'cantidad_surtida': ip.cantidad_surtida,
                'estado': ip.estado,
                'observaciones': ip.observaciones or '',
                'lotes': lotes,
            }
        )

    return {
        'version': EXPORT_VERSION,
        'exported_at': timezone.now().isoformat(),
        'origen': {
            'propuesta_id': str(propuesta.id),
            'folio_solicitud': sol.folio,
            'estado_propuesta': propuesta.estado,
        },
        'solicitud': {
            'institucion_clue': (inst.clue or '').strip(),
            'institucion_ib_clue': (getattr(inst, 'ib_clue', None) or '') or '',
            'institucion_denominacion': inst.denominacion,
            'almacen_destino_nombre': (alm.nombre or '').strip(),
            'fecha_entrega_programada': sol.fecha_entrega_programada.isoformat()
            if sol.fecha_entrega_programada
            else None,
            'observaciones_solicitud': sol.observaciones_solicitud or '',
            'observaciones_validacion': sol.observaciones_validacion or '',
            'items': items_sol,
        },
        'propuesta': {
            'observaciones_revision': propuesta.observaciones_revision or '',
            'items': items_prop,
        },
    }


def _resolver_lote_ubicacion(
    clave_cnis: str,
    numero_lote: str,
    ubicacion_codigo: str,
    almacen_nombre: str,
) -> tuple[LoteUbicacion | None, str | None]:
    """
    Retorna (LoteUbicacion, None) si OK, o (None, mensaje_error).
    """
    prod = Producto.objects.filter(clave_cnis=clave_cnis.strip()).first()
    if not prod:
        return None, f'Producto con clave CNIS "{clave_cnis}" no existe en este ambiente.'

    almacen_nombre = (almacen_nombre or '').strip()
    ubicacion_codigo = (ubicacion_codigo or '').strip()
    numero_lote = (numero_lote or '').strip()

    lotes = list(
        Lote.objects.filter(
            producto=prod,
            numero_lote=numero_lote,
            almacen__nombre__iexact=almacen_nombre,
        ).select_related('almacen')
    )
    if not lotes:
        lotes = list(
            Lote.objects.filter(producto=prod, numero_lote=numero_lote).select_related(
                'almacen'
            )
        )
        if len(lotes) > 1:
            return (
                None,
                f'Lote "{numero_lote}" ({clave_cnis}): hay varios en distintos almacenes; '
                f'especifique almacén "{almacen_nombre}" exacto como en calidad.',
            )
    if not lotes:
        return (
            None,
            f'No hay lote "{numero_lote}" para producto {clave_cnis}'
            + (f' en almacén "{almacen_nombre}".' if almacen_nombre else '.'),
        )

    lote = lotes[0]
    lu = (
        LoteUbicacion.objects.filter(
            lote=lote,
            ubicacion__codigo__iexact=ubicacion_codigo,
        )
        .select_related('ubicacion', 'lote')
        .first()
    )
    if not lu:
        return (
            None,
            f'Lote "{numero_lote}" ({clave_cnis}): no existe ubicación código "{ubicacion_codigo}".',
        )

    return lu, None


def validar_payload_importacion(data: dict[str, Any]) -> dict[str, Any]:
    """
    Valida el JSON sin escribir en BD.
    Retorna:
      ok: bool
      errores: list[str]
      advertencias: list[str]
      resumen_filas: list[dict]  # para mostrar en pantalla
    """
    errores: list[str] = []
    advertencias: list[str] = []
    resumen_filas: list[dict] = []

    if not isinstance(data, dict):
        return {
            'ok': False,
            'errores': ['El archivo no contiene un objeto JSON válido.'],
            'advertencias': [],
            'resumen_filas': [],
        }

    if data.get('version') != EXPORT_VERSION:
        errores.append(
            f"Versión de exportación no soportada (esperada {EXPORT_VERSION}, recibida {data.get('version')})."
        )
        return {'ok': False, 'errores': errores, 'advertencias': [], 'resumen_filas': []}

    sol = data.get('solicitud') or {}
    clue = (sol.get('institucion_clue') or '').strip()
    ib = (sol.get('institucion_ib_clue') or '').strip()
    inst = None
    if clue:
        inst = Institucion.objects.filter(clue=clue).first()
    if not inst and ib:
        inst = Institucion.objects.filter(ib_clue=ib).first()
    if not inst:
        errores.append(
            f'Institución no encontrada por CLUE "{clue}"'
            + (f' ni IB_CLUE "{ib}".' if ib else '.')
        )

    alm_nombre = (sol.get('almacen_destino_nombre') or '').strip()
    almacen = Almacen.objects.filter(nombre__iexact=alm_nombre).first() if alm_nombre else None
    if alm_nombre and not almacen:
        errores.append(f'Almacén destino "{alm_nombre}" no encontrado (nombre exacto, sin distinguir mayúsculas).')

    prop = data.get('propuesta') or {}
    items_prop = prop.get('items') or []
    if not items_prop:
        errores.append('La propuesta no tiene ítems con surtimiento para importar.')

    for idx, it in enumerate(items_prop):
        clave = (it.get('clave_cnis') or '').strip()
        lotes = it.get('lotes') or []
        if not lotes:
            errores.append(f'Ítem {clave or idx}: no tiene lotes/ubicaciones asignadas en el archivo.')
            continue
        for j, row in enumerate(lotes):
            cant = int(row.get('cantidad_asignada') or 0)
            if cant < 1:
                errores.append(f'Ítem {clave}, fila lote {j + 1}: cantidad asignada inválida.')
                continue
            lu, err = _resolver_lote_ubicacion(
                clave,
                row.get('numero_lote') or '',
                row.get('ubicacion_codigo') or '',
                row.get('almacen_nombre') or alm_nombre,
            )
            if err:
                errores.append(f'{clave} / lote {row.get("numero_lote")}: {err}')
                resumen_filas.append(
                    {
                        'clave_cnis': clave,
                        'numero_lote': row.get('numero_lote'),
                        'ubicacion': row.get('ubicacion_codigo'),
                        'cantidad': cant,
                        'ok': False,
                        'detalle': err,
                    }
                )
                continue
            disp = lu.cantidad
            if disp < cant:
                errores.append(
                    f'{clave} / lote {row.get("numero_lote")} / {row.get("ubicacion_codigo")}: '
                    f'solo hay {disp} unidades en ubicación; se requieren {cant}.'
                )
                resumen_filas.append(
                    {
                        'clave_cnis': clave,
                        'numero_lote': row.get('numero_lote'),
                        'ubicacion': row.get('ubicacion_codigo'),
                        'cantidad': cant,
                        'ok': False,
                        'detalle': f'Disponible {disp}, requerido {cant}',
                    }
                )
            else:
                if disp > cant * 5:
                    advertencias.append(
                        f'{clave} / lote {row.get("numero_lote")}: hay mucho stock en ubicación ({disp}); verifique que sea el lote correcto.'
                    )
                resumen_filas.append(
                    {
                        'clave_cnis': clave,
                        'numero_lote': row.get('numero_lote'),
                        'ubicacion': row.get('ubicacion_codigo'),
                        'cantidad': cant,
                        'ok': True,
                        'detalle': f'Disponible en ubicación: {disp}',
                        'lote_ubicacion_id': str(lu.pk),
                    }
                )

    ok = len(errores) == 0 and inst is not None and almacen is not None
    return {
        'ok': ok,
        'errores': errores,
        'advertencias': advertencias,
        'resumen_filas': resumen_filas,
        '_institucion': inst,
        '_almacen': almacen,
    }


def ejecutar_importacion(data: dict[str, Any], usuario) -> dict[str, Any]:
    """
    Crea solicitud, propuesta, asignaciones y movimientos de inventario.
    Asume que validar_payload_importacion ya pasó (volver a validar por seguridad).
    """
    v = validar_payload_importacion(data)
    if not v['ok']:
        return {'exito': False, 'mensaje': 'Validación fallida: ' + '; '.join(v['errores'][:5])}

    inst = v['_institucion']
    almacen = v['_almacen']
    sol_data = data['solicitud']
    prop_data = data['propuesta']
    origen = data.get('origen') or {}

    nota_origen = (
        f"Importado desde calidad/copia. Folio origen: {origen.get('folio_solicitud', 'N/A')} "
        f"(propuesta {origen.get('propuesta_id', '')}). "
    )
    obs_sol = (sol_data.get('observaciones_solicitud') or '').strip()
    if obs_sol:
        obs_sol = nota_origen + obs_sol
    else:
        obs_sol = nota_origen.strip()

    fe_prog = sol_data.get('fecha_entrega_programada')
    if isinstance(fe_prog, str) and fe_prog.strip():
        try:
            fe_prog = date_type.fromisoformat(fe_prog.strip()[:10])
        except ValueError:
            fe_prog = timezone.now().date()
    elif not fe_prog:
        fe_prog = timezone.now().date()

    solicitud = None
    try:
        with transaction.atomic():
            solicitud = SolicitudPedido.objects.create(
                institucion_solicitante=inst,
                almacen_destino=almacen,
                usuario_solicitante=usuario,
                usuario_validacion=usuario,
                fecha_entrega_programada=fe_prog,
                estado='PREPARADA',
                observaciones_solicitud=obs_sol,
                observaciones_validacion=sol_data.get('observaciones_validacion') or '',
                fecha_validacion=timezone.now(),
            )

            clave_to_item_sol = {}
            for it in sol_data.get('items') or []:
                clave = (it.get('clave_cnis') or '').strip()
                if not clave:
                    continue
                prod = Producto.objects.filter(clave_cnis=clave).first()
                if not prod:
                    raise ValueError(f'Producto {clave} no existe')
                ap = int(it.get('cantidad_aprobada') or it.get('cantidad_solicitada') or 0)
                if ap < 1:
                    continue
                if clave in clave_to_item_sol:
                    continue
                item_sol = ItemSolicitud.objects.create(
                    solicitud=solicitud,
                    producto=prod,
                    cantidad_solicitada=int(it.get('cantidad_solicitada') or ap),
                    cantidad_aprobada=ap,
                    justificacion_cambio=(it.get('justificacion_cambio') or '')[:255],
                )
                clave_to_item_sol[clave] = item_sol

            propuesta = PropuestaPedido.objects.create(
                solicitud=solicitud,
                usuario_generacion=usuario,
                estado='REVISADA',
                observaciones_revision=prop_data.get('observaciones_revision') or '',
                total_solicitado=0,
                total_disponible=0,
                total_propuesto=0,
            )

            total_sol = 0
            total_prop = 0
            for it in prop_data.get('items') or []:
                clave = (it.get('clave_cnis') or '').strip()
                prod = Producto.objects.filter(clave_cnis=clave).first()
                if not prod:
                    raise ValueError(f'Producto ítem propuesta {clave} no existe')
                item_sol = clave_to_item_sol.get(clave)
                if not item_sol:
                    item_sol = ItemSolicitud.objects.create(
                        solicitud=solicitud,
                        producto=prod,
                        cantidad_solicitada=it.get('cantidad_solicitada') or it.get('cantidad_propuesta') or 1,
                        cantidad_aprobada=it.get('cantidad_propuesta') or it.get('cantidad_solicitada') or 1,
                    )
                    clave_to_item_sol[clave] = item_sol

                ip = ItemPropuesta.objects.create(
                    propuesta=propuesta,
                    item_solicitud=item_sol,
                    producto=prod,
                    cantidad_solicitada=it.get('cantidad_solicitada') or item_sol.cantidad_solicitada,
                    cantidad_disponible=it.get('cantidad_disponible') or it.get('cantidad_propuesta') or 0,
                    cantidad_propuesta=it.get('cantidad_propuesta') or 0,
                    cantidad_surtida=it.get('cantidad_surtida') or 0,
                    estado=it.get('estado') or 'DISPONIBLE',
                    observaciones=it.get('observaciones') or '',
                )
                total_sol += ip.cantidad_solicitada
                total_prop += ip.cantidad_propuesta

                alm_n = (sol_data.get('almacen_destino_nombre') or '').strip()
                for row in it.get('lotes') or []:
                    lu, err = _resolver_lote_ubicacion(
                        clave,
                        row.get('numero_lote') or '',
                        row.get('ubicacion_codigo') or '',
                        row.get('almacen_nombre') or alm_n,
                    )
                    if err or not lu:
                        raise ValueError(err or 'Lote-ubicación no resuelto')
                    cant = int(row.get('cantidad_asignada') or 0)
                    if cant < 1:
                        continue
                    LoteAsignado.objects.create(
                        item_propuesta=ip,
                        lote_ubicacion=lu,
                        cantidad_asignada=cant,
                        surtido=False,
                    )

            propuesta.total_solicitado = total_sol
            propuesta.total_disponible = total_prop
            propuesta.total_propuesto = total_prop
            propuesta.save()

        res = generar_movimientos_suministro(propuesta.id, usuario)
        if not res.get('exito'):
            solicitud.delete()
            return {'exito': False, 'mensaje': res.get('mensaje', 'Error en movimientos')}

        now = timezone.now()
        propuesta.refresh_from_db()
        for item in propuesta.items.all():
            for la in item.lotes_asignados.all():
                la.surtido = True
                la.fecha_surtimiento = now
                la.usuario_surtido = usuario
                la.save()
        propuesta.estado = 'SURTIDA'
        propuesta.fecha_surtimiento = now
        propuesta.usuario_surtimiento = usuario
        propuesta.save()

        sincronizar_cantidades_surtidas_items_propuesta(propuesta)

        return {
            'exito': True,
            'mensaje': res.get('mensaje', ''),
            'propuesta_id': str(propuesta.id),
            'folio': solicitud.folio,
        }
    except Exception as e:
        logger.exception('Error importando pedido desde JSON')
        if solicitud and solicitud.pk:
            try:
                solicitud.delete()
            except Exception:
                pass
        return {'exito': False, 'mensaje': str(e)}
