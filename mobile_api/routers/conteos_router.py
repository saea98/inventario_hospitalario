from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from inventario.conteo_mobile_services import (
    asegurar_acceso_almacen,
    asegurar_acceso_lote_ubicacion,
    asegurar_acceso_ubicacion,
    crear_lote_en_ubicacion,
    listar_almacenes_usuario,
    listar_lotes_ubicacion,
    registrar_conteo_ubicacion,
)
from inventario.models import UbicacionAlmacen
from mobile_api.deps import get_current_user
from mobile_api.schemas import ConteoRequest, CrearLoteRequest

router = APIRouter(prefix='/conteos', tags=['conteos'])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@router.get('/almacenes')
def almacenes(user=Depends(get_current_user)):
    return listar_almacenes_usuario(user)


@router.get('/ubicaciones')
def ubicaciones(
    almacen_id: int = Query(...),
    q: Optional[str] = Query(None),
    user=Depends(get_current_user),
):
    try:
        asegurar_acceso_almacen(user, almacen_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    qs = UbicacionAlmacen.objects.filter(almacen_id=almacen_id, activo=True).order_by('codigo')
    if q:
        qs = qs.filter(codigo__icontains=q.strip())
    return [
        {
            'id': u.id,
            'codigo': u.codigo,
            'descripcion': u.descripcion,
            'almacen_id': u.almacen_id,
        }
        for u in qs[:200]
    ]


@router.get('/ubicaciones/{ubicacion_id}/lotes')
def lotes_en_ubicacion(ubicacion_id: int, user=Depends(get_current_user)):
    try:
        return listar_lotes_ubicacion(ubicacion_id, usuario=user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/lotes/{lote_ubicacion_id}/conteo')
def registrar_conteo(lote_ubicacion_id: int, body: ConteoRequest, user=Depends(get_current_user)):
    try:
        resultado = registrar_conteo_ubicacion(
            lote_ubicacion_id,
            user,
            body.cantidad_fisica,
            fecha_caducidad=body.fecha_caducidad,
            observaciones=body.observaciones,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise _http_error(exc) from exc
    return {
        'lote_ubicacion_id': resultado.lote_ubicacion_id,
        'movimiento_id': resultado.movimiento_id,
        'cantidad_anterior': resultado.cantidad_anterior,
        'cantidad_nueva': resultado.cantidad_nueva,
        'diferencia': resultado.diferencia,
        'tipo_movimiento': resultado.tipo_movimiento,
        'completado': resultado.completado,
    }


@router.post('/lotes/{lote_ubicacion_id}/verificar')
def verificar_coincide(lote_ubicacion_id: int, user=Depends(get_current_user)):
    from inventario.models import LoteUbicacion

    try:
        asegurar_acceso_lote_ubicacion(user, lote_ubicacion_id)
        lu = LoteUbicacion.objects.get(pk=lote_ubicacion_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LoteUbicacion.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail='Lote en ubicación no encontrado') from exc
    try:
        resultado = registrar_conteo_ubicacion(
            lote_ubicacion_id,
            user,
            lu.cantidad,
            observaciones='Coincide con sistema',
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise _http_error(exc) from exc
    return {
        'lote_ubicacion_id': resultado.lote_ubicacion_id,
        'movimiento_id': resultado.movimiento_id,
        'cantidad_anterior': resultado.cantidad_anterior,
        'cantidad_nueva': resultado.cantidad_nueva,
        'diferencia': resultado.diferencia,
        'tipo_movimiento': resultado.tipo_movimiento,
        'completado': resultado.completado,
    }


@router.post('/ubicaciones/{ubicacion_id}/lotes')
def alta_lote(ubicacion_id: int, body: CrearLoteRequest, user=Depends(get_current_user)):
    try:
        return crear_lote_en_ubicacion(
            ubicacion_id,
            user,
            body.clave_cnis,
            body.numero_lote,
            body.cantidad_inicial,
            body.fecha_caducidad,
            precio_unitario=body.precio_unitario,
            observaciones=body.observaciones,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise _http_error(exc) from exc
