from fastapi import APIRouter, HTTPException

from mobile_api.auth import LoginRequest, TokenResponse, authenticate_user, create_access_token

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=TokenResponse)
def login(body: LoginRequest):
    user = authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail='Credenciales inválidas o usuario sin rol de conteo',
        )
    token = create_access_token(user.id, user.username)
    nombre = user.get_full_name() or user.username
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        nombre=nombre,
    )
