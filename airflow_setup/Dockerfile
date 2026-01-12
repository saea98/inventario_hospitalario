FROM apache/airflow:2.7.3-python3.11

# Cambiar a usuario root para instalar paquetes
USER root

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Volver al usuario airflow
USER airflow

# Instalar paquetes Python adicionales
RUN pip install --no-cache-dir \
    psycopg2-binary==2.9.9 \
    requests==2.31.0 \
    python-dotenv==1.0.0
