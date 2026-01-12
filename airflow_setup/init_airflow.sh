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
    --conn-host 'localhost' \
    --conn-port '5432' \
    --conn-login 'postgres' \
    --conn-password 'postgres' \
    --conn-schema 'inventario_hospitalario' \
    2>/dev/null || echo "Conexión postgres_inventario ya existe"

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
echo "   1. Las credenciales de BD se leen del archivo .env"
echo "   2. Verifica que los valores en .env sean correctos:"
echo "      - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD"
echo ""
echo "   3. (Opcional) Configura Telegram:"
echo "      - TELEGRAM_BOT_TOKEN"
echo "      - TELEGRAM_CHAT_ID"
echo ""
echo "   4. El DAG se ejecutará diariamente a las 2:00 AM"
