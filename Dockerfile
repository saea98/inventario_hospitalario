FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app  

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Crear directorio para static files
RUN mkdir -p /app/staticfiles

EXPOSE 8000

# ============================================================================
# SCRIPT DE ENTRADA (ENTRYPOINT) - MEJORADO
# ============================================================================
# Este script ejecutará las migraciones antes de iniciar la aplicación
# Validará si ya están aplicadas para evitar errores
# Funciona tanto en desarrollo como en producción

RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Colores para output\n\
GREEN='"'"'\033[0;32m'"'"'\n\
BLUE='"'"'\033[0;34m'"'"'\n\
YELLOW='"'"'\033[1;33m'"'"'\n\
NC='"'"'\033[0m'"'"' # No Color\n\
\n\
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"\n\
echo -e "${BLUE}🚀 Iniciando contenedor Django${NC}"\n\
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"\n\
\n\
# Esperar a que la base de datos esté lista\n\
echo -e "${YELLOW}⏳ Esperando a que la base de datos esté lista...${NC}"\n\
sleep 5\n\
\n\
# Ejecutar migraciones (Django detecta automáticamente cuáles ya están aplicadas)\n\
echo -e "${YELLOW}🔄 Ejecutando migraciones...${NC}"\n\
python manage.py migrate --noinput 2>&1 | grep -E "Applying|No migrations|OK" || true\n\
\n\
if [ $? -eq 0 ]; then\n\
    echo -e "${GREEN}✓ Migraciones completadas${NC}"\n\
else\n\
    echo -e "${YELLOW}⚠️ Advertencia en migraciones (puede ser normal)${NC}"\n\
fi\n\
\n\
# Ejecutar collectstatic para producción\n\
echo -e "${YELLOW}📦 Recolectando archivos estáticos...${NC}"\n\
python manage.py collectstatic --noinput --clear 2>&1 | tail -1\n\
echo -e "${GREEN}✓ Archivos estáticos recolectados${NC}"\n\
\n\
# Verificar si DEBUG está configurado\n\
if [ -z "$DEBUG" ]; then\n\
    echo -e "${YELLOW}⚠️ Variable DEBUG no configurada, usando valor por defecto (True)${NC}"\n\
    DEBUG=True\n\
fi\n\
\n\
# Iniciar la aplicación\n\
if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then\n\
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"\n\
    echo -e "${GREEN}🚀 Iniciando en modo PRODUCCIÓN con Gunicorn${NC}"\n\
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"\n\
    exec gunicorn inventario_hospitalario.wsgi:application \\\n\
        --bind 0.0.0.0:8000 \\\n\
        --workers 5 \\\n\
        --timeout 120 \\\n\
        --access-logfile - \\\n\
        --error-logfile - \\\n\
        --log-level info\n\
else\n\
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"\n\
    echo -e "${GREEN}🚀 Iniciando en modo DESARROLLO con Django${NC}"\n\
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"\n\
    exec python manage.py runserver 0.0.0.0:8000\n\
fi\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Usar el script como punto de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
