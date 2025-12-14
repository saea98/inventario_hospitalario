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
# SCRIPT DE ENTRADA (ENTRYPOINT)
# ============================================================================
# Este script ejecutará las migraciones antes de iniciar la aplicación
# Funciona tanto en desarrollo como en producción

RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🔄 Ejecutando migraciones..."\n\
python manage.py migrate --noinput\n\
\n\
echo "✓ Migraciones completadas"\n\
\n\
# Ejecutar collectstatic para producción\n\
echo "📦 Recolectando archivos estáticos..."\n\
python manage.py collectstatic --noinput --clear\n\
\n\
echo "✓ Archivos estáticos recolectados"\n\
\n\
# Iniciar la aplicación\n\
if [ "$DEBUG" = "False" ]; then\n\
    echo "🚀 Iniciando en modo PRODUCCIÓN con Gunicorn..."\n\
    exec gunicorn inventario_hospitalario.wsgi:application \\\n\
        --bind 0.0.0.0:8000 \\\n\
        --workers 5 \\\n\
        --timeout 120 \\\n\
        --access-logfile - \\\n\
        --error-logfile -\n\
else\n\
    echo "🚀 Iniciando en modo DESARROLLO con Django..."\n\
    exec python manage.py runserver 0.0.0.0:8000\n\
fi\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Usar el script como punto de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
