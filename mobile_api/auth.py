"""Autenticación JWT con usuarios Django."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from mobile_api.django_setup import setup_django

setup_django()

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model

from inventario.conteo_mobile_services import usuario_puede_conteo_movil

User = get_user_model()

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_HOURS = 12


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user_id: int
    username: str
    nombre: str


class LoginRequest(BaseModel):
    username: str
    password: str


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {'sub': str(user_id), 'username': username, 'exp': expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str) -> Optional[User]:
    user = authenticate(username=username, password=password)
    if not user or not user.is_active:
        return None
    if not usuario_puede_conteo_movil(user):
        return None
    return user


def get_user_from_token(token: str) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get('sub', 0))
    except (JWTError, ValueError, TypeError) as exc:
        raise PermissionError('Token inválido o expirado') from exc
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if not user or not usuario_puede_conteo_movil(user):
        raise PermissionError('Usuario sin permiso de conteo móvil')
    return user
