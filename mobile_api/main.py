from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mobile_api.django_setup import setup_django

setup_django()

from mobile_api.routers import auth_router, conteos_router

app = FastAPI(
    title='Inventario Hospitalario — API móvil conteo',
    version='1.0.0',
    docs_url='/docs',
    openapi_url='/openapi.json',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth_router.router)
app.include_router(conteos_router.router)


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'mobile_api'}
