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

EXPOSE 8000

# --- Opción 1: para desarrollo
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --- Opción 2: para producción
#CMD ["gunicorn", "inventario_hospitalario.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "5", "--timeout", "120"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]