#!/bin/bash

# Script para iniciar Airflow de forma simple

set -e

echo "🚀 Iniciando Airflow..."
echo ""

# Crear directorios si no existen
echo "📁 Creando directorios..."
mkdir -p dags logs plugins

# Dar permisos
echo "🔐 Configurando permisos..."
chmod -R 777 logs/ dags/ plugins/

# Iniciar contenedores
echo "🐳 Iniciando contenedores Docker..."
COMPOSE_HTTP_TIMEOUT=300 docker-compose up -d

# Esperar a que PostgreSQL esté listo
echo "⏳ Esperando a PostgreSQL..."
sleep 10

# Esperar a que Airflow esté listo
echo "⏳ Esperando a Airflow (esto puede tardar 2-3 minutos)..."
for i in {1..30}; do
    if docker exec airflow_webserver airflow db check > /dev/null 2>&1; then
        echo "✓ Airflow está listo"
        break
    fi
    echo "  Intento $i/30..."
    sleep 10
done

# Inicializar BD
echo "🗄️  Inicializando base de datos..."
docker exec airflow_webserver airflow db init

# Crear usuario admin
echo "👤 Creando usuario admin..."
docker exec airflow_webserver airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin \
    2>/dev/null || echo "  Usuario admin ya existe"

# Esperar un poco
sleep 5

# Reiniciar webserver para asegurar que carga bien
echo "🔄 Reiniciando webserver..."
docker-compose restart airflow_webserver

# Esperar
sleep 10

echo ""
echo "✅ ¡Airflow iniciado correctamente!"
echo ""
echo "📊 Acceso:"
echo "   Airflow Web: http://localhost:8080"
echo "   Usuario: admin"
echo "   Contraseña: admin"
echo ""
echo "🌸 Flower (Monitor):"
echo "   URL: http://localhost:5555"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Accede a http://localhost:8080"
echo "   2. Busca el DAG 'actualizar_lotes_caducados'"
echo "   3. Actívalo con el toggle"
echo "   4. Se ejecutará diariamente a las 2:00 AM"
echo ""
echo "🔍 Para ver logs:"
echo "   docker-compose logs -f airflow_webserver"
