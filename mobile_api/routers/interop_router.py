"""
API de interoperabilidad (lectura) para otros equipos.

Base (montada en WSGI): /api/v1/interop/...
Auth: header X-API-Key (crear consumidor en Django Admin → API consumidores).

Existencias siempre con la regla canónica:
  disponible_neto = max(0, fisico − reservas activas LoteAsignado surtido=False)

Los lotes caducados (estado Caducado o fecha vencida) nunca se devuelven.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from inventario.interop_models import ApiConsumidor
from inventario.interop_services import (
    consultar_existencias,
    obtener_lote,
    resumen_existencia_clave,
    buscar_productos,
    listar_almacenes,
)
from mobile_api.interop_auth import require_api_consumidor, require_scope

router = APIRouter(prefix='/interop', tags=['interop'])


def _institucion_efectiva(
    consumidor: ApiConsumidor,
    institucion_id: Optional[int],
) -> Optional[int]:
    if consumidor.institucion_id:
        if institucion_id and institucion_id != consumidor.institucion_id:
            raise HTTPException(
                status_code=403,
                detail='Este consumidor solo puede consultar su institución asignada',
            )
        return consumidor.institucion_id
    return institucion_id


@router.get('/ping')
def ping(consumidor: ApiConsumidor = Depends(require_api_consumidor)):
    """Verifica API key y muestra scopes disponibles."""
    return {
        'ok': True,
        'consumidor': consumidor.nombre,
        'scopes': consumidor.scopes or [],
        'institucion_id': consumidor.institucion_id,
        'politica': {'excluye_caducados': True},
    }


@router.get('/existencias')
def existencias(
    clave_cnis: Optional[str] = Query(None, description='Clave CNIS (acepta con/sin .00)'),
    numero_lote: Optional[str] = Query(
        None,
        description='Número de lote (se puede combinar con clave_cnis)',
    ),
    lote_id: Optional[int] = Query(None, description='ID interno del lote'),
    uuid: Optional[str] = Query(None, description='UUID del lote'),
    almacen_id: Optional[int] = Query(None),
    institucion_id: Optional[int] = Query(None),
    solo_con_neto: bool = Query(
        True,
        description='Si true, solo lotes con disponible_neto > 0',
    ),
    limite_lotes: int = Query(500, ge=1, le=2000),
    consumidor: ApiConsumidor = Depends(require_api_consumidor),
):
    """
    Listado de existencias (agregado por clave + detalle por lote).

    Filtros combinables, p.ej. `clave_cnis` + `numero_lote`.
    No incluye caducados. Cada lote trae `existencia.fisico|reservado|disponible_neto`.
    """
    require_scope(consumidor, ApiConsumidor.SCOPE_EXISTENCIAS)
    inst = _institucion_efectiva(consumidor, institucion_id)
    return consultar_existencias(
        clave_cnis=clave_cnis,
        numero_lote=numero_lote,
        lote_id=lote_id,
        uuid=uuid,
        almacen_id=almacen_id,
        institucion_id=inst,
        solo_con_neto=solo_con_neto,
        limite_lotes=limite_lotes,
    )


@router.get('/existencias/{clave_cnis}')
def existencia_por_clave(
    clave_cnis: str,
    numero_lote: Optional[str] = Query(
        None,
        description='Opcional: acotar a un número de lote',
    ),
    almacen_id: Optional[int] = Query(None),
    institucion_id: Optional[int] = Query(None),
    consumidor: ApiConsumidor = Depends(require_api_consumidor),
):
    """Resumen y lotes de una clave CNIS (sin caducados; solo neto > 0)."""
    require_scope(consumidor, ApiConsumidor.SCOPE_EXISTENCIAS)
    inst = _institucion_efectiva(consumidor, institucion_id)
    return resumen_existencia_clave(
        clave_cnis,
        numero_lote=numero_lote,
        institucion_id=inst,
        almacen_id=almacen_id,
    )


@router.get('/lotes')
def listar_lotes(
    clave_cnis: Optional[str] = Query(None),
    numero_lote: Optional[str] = Query(None),
    almacen_id: Optional[int] = Query(None),
    institucion_id: Optional[int] = Query(None),
    solo_con_neto: bool = Query(True),
    limite: int = Query(100, ge=1, le=500),
    consumidor: ApiConsumidor = Depends(require_api_consumidor),
):
    """
    Búsqueda de lotes (ideal para CNIS + lote). Sin caducados.
    """
    require_scope(consumidor, ApiConsumidor.SCOPE_LOTES)
    if not clave_cnis and not numero_lote:
        raise HTTPException(
            status_code=400,
            detail='Indica al menos clave_cnis o numero_lote',
        )
    inst = _institucion_efectiva(consumidor, institucion_id)
    return consultar_existencias(
        clave_cnis=clave_cnis,
        numero_lote=numero_lote,
        almacen_id=almacen_id,
        institucion_id=inst,
        solo_con_neto=solo_con_neto,
        limite_lotes=limite,
    )


@router.get('/lotes/{lote_id}')
def detalle_lote(
    lote_id: int,
    consumidor: ApiConsumidor = Depends(require_api_consumidor),
):
    """Detalle de un lote con desglose de existencia neta. 404 si está caducado."""
    require_scope(consumidor, ApiConsumidor.SCOPE_LOTES)
    data = obtener_lote(lote_id, institucion_id=consumidor.institucion_id)
    if not data:
        raise HTTPException(
            status_code=404,
            detail='Lote no encontrado o caducado (los caducados no se exponen en interop)',
        )
    return data


@router.get('/almacenes')
def almacenes(
    q: Optional[str] = Query(None, description='Busca por nombre, código o CLUE'),
    institucion_id: Optional[int] = Query(None),
    solo_activos: bool = Query(True),
    consumidor: ApiConsumidor = Depends(require_api_consumidor),
):
    """
    Catálogo de almacenes (ids para filtrar existencias/lotes).

    Acepta scope `almacenes:read` o, por compatibilidad, `existencias:read` / `lotes:read`.
    """
    if not (
        consumidor.tiene_scope(ApiConsumidor.SCOPE_ALMACENES)
        or consumidor.tiene_scope(ApiConsumidor.SCOPE_EXISTENCIAS)
        or consumidor.tiene_scope(ApiConsumidor.SCOPE_LOTES)
    ):
        raise HTTPException(
            status_code=403,
            detail='Scope requerido: almacenes:read (o existencias:read / lotes:read)',
        )
    inst = _institucion_efectiva(consumidor, institucion_id)
    return listar_almacenes(institucion_id=inst, q=q, solo_activos=solo_activos)


@router.get('/productos')
def productos(
    q: Optional[str] = Query(None, description='Busca en clave CNIS o descripción'),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    consumidor: ApiConsumidor = Depends(require_api_consumidor),
):
    """Catálogo de productos activos (paginado)."""
    require_scope(consumidor, ApiConsumidor.SCOPE_PRODUCTOS)
    return buscar_productos(q=q, page=page, page_size=page_size)
