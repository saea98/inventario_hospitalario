"""Autenticación de consumidores externos vía X-API-Key."""

from typing import Optional

from fastapi import Header, HTTPException, status

from mobile_api.django_setup import setup_django

setup_django()

from inventario.interop_models import ApiConsumidor


def require_api_consumidor(
    x_api_key: Optional[str] = Header(None, alias='X-API-Key'),
) -> ApiConsumidor:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Header X-API-Key requerido',
            headers={'WWW-Authenticate': 'ApiKey'},
        )
    consumidor = ApiConsumidor.autenticar(x_api_key)
    if not consumidor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='API key inválida o inactiva',
        )
    consumidor.marcar_uso()
    return consumidor


def require_scope(consumidor: ApiConsumidor, scope: str) -> None:
    if not consumidor.tiene_scope(scope):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Scope requerido: {scope}',
        )
