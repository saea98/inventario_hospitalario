# Forzar arquitectura x86 para compatibilidad con producción
# Esto es importante para dependencias binarias como WeasyPrint (Pango, Cairo)
FROM --platform=linux/amd64 python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app  

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl \
    libcairo2-dev pkg-config python3-dev \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Crear directorio para static files
RUN mkdir -p /app/staticfiles

EXPOSE 8000

# ============================================================================
# CREAR SCRIPT DE ENTRADA (ENTRYPOINT)
# ============================================================================

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Usar el script como punto de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
