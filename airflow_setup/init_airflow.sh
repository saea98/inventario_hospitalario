#!/bin/bash

# Script de inicialización de Airflow
# Configura variables y conexiones necesarias para el DAG

set -e

echo "🚀 Inicializando Airflow..."

# Esperar a que Airflow esté listo
echo "⏳ Esperando a que Airflow esté disponible..."
sleep 30

# Crear usuario admin por defecto
echo "👤 Creando usuario admin..."
docker exec airflow_webserver airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin \
    2>/dev/null || echo "Usuario admin ya existe"

# Crear conexión a PostgreSQL del inventario
echo "🔗 Creando conexión a PostgreSQL (inventario)..."
docker exec airflow_webserver airflow connections add \
    --conn-id 'postgres_inventario' \
    --conn-type 'postgres' \
    --conn-host 'host.docker.internal' \
    --conn-port '5432' \
    --conn-login 'postgres' \
    --conn-password 'postgres' \
    --conn-schema 'inventario_hospitalario' \
    2>/dev/null || echo "Conexión postgres_inventario ya existe"

# Establecer variables de Airflow
echo "📝 Configurando variables de Airflow..."

# Variables de Base de Datos
docker exec airflow_webserver airflow variables set DB_HOST "host.docker.internal" 2>/dev/null || true
docker exec airflow_webserver airflow variables set DB_PORT "5432" 2>/dev/null || true
docker exec airflow_webserver airflow variables set DB_NAME "inventario_hospitalario" 2>/dev/null || true
docker exec airflow_webserver airflow variables set DB_USER "postgres" 2>/dev/null || true
docker exec airflow_webserver airflow variables set DB_PASSWORD "postgres" 2>/dev/null || true

# Variables de Telegram (IMPORTANTE: Configurar con tus valores reales)
echo "📱 Configurando variables de Telegram..."
docker exec airflow_webserver airflow variables set TELEGRAM_BOT_TOKEN "TU_TOKEN_AQUI" 2>/dev/null || true
docker exec airflow_webserver airflow variables set TELEGRAM_CHAT_ID "TU_CHAT_ID_AQUI" 2>/dev/null || true

# Variables de configuración del DAG
docker exec airflow_webserver airflow variables set DAG_ENABLED "true" 2>/dev/null || true
docker exec airflow_webserver airflow variables set NOTIFICATION_ENABLED "true" 2>/dev/null || true

echo "✅ Inicialización completada"
echo ""
echo "📊 Acceso a Airflow:"
echo "   URL: http://localhost:8080"
echo "   Usuario: admin"
echo "   Contraseña: admin"
echo ""
echo "🌸 Acceso a Flower (Monitor de Celery):"
echo "   URL: http://localhost:5555"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   1. Actualiza las variables de Telegram con tus valores reales:"
echo "      - TELEGRAM_BOT_TOKEN: Token del bot de Telegram"
echo "      - TELEGRAM_CHAT_ID: ID del chat donde enviar notificaciones"
echo ""
echo "   2. Verifica que DB_HOST sea accesible desde los contenedores"
echo "      Si usas Docker Desktop, usa 'host.docker.internal'"
echo "      Si usas Linux, usa la IP de la red Docker o el nombre del contenedor"
echo ""
echo "   3. El DAG se ejecutará diariamente a las 2:00 AM"
