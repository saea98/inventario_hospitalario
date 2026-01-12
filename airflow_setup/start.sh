#!/bin/bash

# Script para iniciar Airflow con LocalExecutor

set -e

echo "🚀 Iniciando Airflow..."
echo ""

# Crear directorios si no existen
echo "📁 Creando directorios..."
mkdir -p dags logs plugins config

# Iniciar contenedores
echo "🐳 Iniciando contenedores Docker..."
COMPOSE_HTTP_TIMEOUT=300 docker-compose up -d

# Esperar a que todo esté listo
echo "⏳ Esperando a que Airflow esté listo (esto puede tardar 1-2 minutos)..."
sleep 30

# Verificar que los contenedores estén corriendo
echo ""
echo "📊 Estado de los contenedores:"
docker-compose ps

echo ""
echo "✅ ¡Airflow iniciado correctamente!"
echo ""
echo "📊 Acceso:"
echo "   Airflow Web: http://localhost:8080"
echo "   Usuario: admin"
echo "   Contraseña: admin"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Accede a http://localhost:8080"
echo "   2. Busca el DAG 'actualizar_lotes_caducados'"
echo "   3. Actívalo con el toggle"
echo "   4. Se ejecutará diariamente a las 2:00 AM"
echo ""
echo "🔍 Para ver logs:"
echo "   docker-compose logs -f airflow-webserver"
echo ""
echo "⚠️  Si los contenedores no están 'Up', espera un poco más y ejecuta:"
echo "   docker-compose ps"
