#!/bin/bash
set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Iniciando contenedor Django${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"

# Esperar a que la base de datos esté lista
echo -e "${YELLOW}⏳ Esperando a que la base de datos esté lista...${NC}"
sleep 5

# Ejecutar migraciones (Django detecta automáticamente cuáles ya están aplicadas)
echo -e "${YELLOW}🔄 Ejecutando migraciones...${NC}"
python manage.py migrate --noinput 2>&1 | grep -E "Applying|No migrations|OK" || true

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migraciones completadas${NC}"
else
    echo -e "${YELLOW}⚠️ Advertencia en migraciones (puede ser normal)${NC}"
fi

# Ejecutar collectstatic para producción
echo -e "${YELLOW}📦 Recolectando archivos estáticos...${NC}"
python manage.py collectstatic --noinput --clear 2>&1 | tail -1
echo -e "${GREEN}✓ Archivos estáticos recolectados${NC}"

# Verificar si DEBUG está configurado
if [ -z "$DEBUG" ]; then
    echo -e "${YELLOW}⚠️ Variable DEBUG no configurada, usando valor por defecto (True)${NC}"
    DEBUG=True
fi

# Iniciar la aplicación
if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🚀 Iniciando en modo PRODUCCIÓN con Gunicorn${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    exec gunicorn inventario_hospitalario.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 4 \
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
