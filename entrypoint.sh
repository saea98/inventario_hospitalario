#!/bin/bash
set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Iniciando contenedor Django${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"

# Esperar conexión a PostgreSQL (evita migrate colgado sin mensaje)
echo -e "${YELLOW}⏳ Esperando conexión a PostgreSQL...${NC}"
python <<'PY'
import os, sys, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventario_hospitalario.settings")
import django
django.setup()
from django.conf import settings
from django.db import connection
db = settings.DATABASES["default"]
print(f"   Host: {db.get('HOST')}:{db.get('PORT')}  DB: {db.get('NAME')}", flush=True)
max_attempts = 30
for attempt in range(1, max_attempts + 1):
    try:
        connection.ensure_connection()
        print("✓ Base de datos accesible", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"   Intento {attempt}/{max_attempts}: {e}", flush=True)
        time.sleep(3)
print("✗ No se pudo conectar a la base de datos", flush=True)
sys.exit(1)
PY

# Ejecutar migraciones
echo -e "${YELLOW}🔄 Ejecutando migraciones...${NC}"
if ! python manage.py migrate --noinput; then
    echo -e "${RED}❌ Error en migraciones (revisar POSTGRES_* en .env)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Migraciones completadas${NC}"

# Ejecutar collectstatic para producción
echo -e "${YELLOW}📦 Recolectando archivos estáticos...${NC}"
python manage.py collectstatic --noinput --clear 2>&1 | tail -1
echo -e "${GREEN}✓ Archivos estáticos recolectados${NC}"

# Verificar si DEBUG está configurado
if [ -z "$DEBUG" ]; then
    echo -e "${YELLOW}⚠️ Variable DEBUG no configurada, usando valor por defecto (True)${NC}"
    DEBUG=True
fi

# API móvil: montada en WSGI bajo /api/v1 (mismo puerto que Django, sin proceso extra)
if [ "${MOBILE_API_ENABLED:-true}" = "false" ] || [ "${MOBILE_API_ENABLED}" = "False" ]; then
    echo -e "${YELLOW}⏭ API móvil deshabilitada (MOBILE_API_ENABLED=false)${NC}"
else
    echo -e "${GREEN}✓ API móvil disponible en /api/v1 (montada en WSGI)${NC}"
fi

# Iniciar la aplicación web (proceso principal del contenedor)
if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🚀 Iniciando en modo PRODUCCIÓN con Gunicorn${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    exec gunicorn inventario_hospitalario.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 5 \
        --timeout 300 \
        --graceful-timeout 300 \
        --access-logfile - \
        --error-logfile - \
        --log-level info
else
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🚀 Iniciando en modo DESARROLLO con Django${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    exec python manage.py runserver 0.0.0.0:8000
fi
