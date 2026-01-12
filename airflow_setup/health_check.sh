#!/bin/bash

# Script de verificación de salud de Airflow

echo "🏥 Verificación de Salud - Airflow"
echo "===================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir estado
print_status() {
    local status=$1
    local message=$2
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $message"
    else
        echo -e "${RED}✗${NC} $message"
    fi
}

# 1. Verificar Docker
echo "1️⃣  Docker"
docker --version > /dev/null 2>&1
print_status $? "Docker instalado"

# 2. Verificar Docker Compose
echo ""
echo "2️⃣  Docker Compose"
docker-compose --version > /dev/null 2>&1
print_status $? "Docker Compose instalado"

# 3. Verificar contenedores
echo ""
echo "3️⃣  Contenedores"

containers=("postgres_airflow" "redis_airflow" "airflow_webserver" "airflow_scheduler" "airflow_worker" "airflow_flower")

for container in "${containers[@]}"; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            print_status 0 "$container está corriendo"
        else
            print_status 1 "$container existe pero no está corriendo"
        fi
    else
        print_status 1 "$container no existe"
    fi
done

# 4. Verificar conectividad
echo ""
echo "4️⃣  Conectividad"

# Airflow Web
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    print_status 0 "Airflow Web (http://localhost:8080)"
else
    print_status 1 "Airflow Web (http://localhost:8080)"
fi

# Flower
if curl -s http://localhost:5555/ > /dev/null 2>&1; then
    print_status 0 "Flower (http://localhost:5555)"
else
    print_status 1 "Flower (http://localhost:5555)"
fi

# PostgreSQL Airflow
if docker exec postgres_airflow pg_isready -U airflow > /dev/null 2>&1; then
    print_status 0 "PostgreSQL Airflow"
else
    print_status 1 "PostgreSQL Airflow"
fi

# Redis
if docker exec redis_airflow redis-cli ping > /dev/null 2>&1; then
    print_status 0 "Redis"
else
    print_status 1 "Redis"
fi

# 5. Verificar DAGs
echo ""
echo "5️⃣  DAGs"

if docker exec airflow_webserver airflow dags list 2>/dev/null | grep -q "actualizar_lotes_caducados"; then
    print_status 0 "DAG 'actualizar_lotes_caducados' encontrado"
else
    print_status 1 "DAG 'actualizar_lotes_caducados' no encontrado"
fi

# 6. Verificar variables
echo ""
echo "6️⃣  Variables de Airflow"

DB_HOST=$(docker exec airflow_webserver airflow variables get DB_HOST 2>/dev/null || echo "")
if [ -n "$DB_HOST" ]; then
    print_status 0 "DB_HOST configurado: $DB_HOST"
else
    print_status 1 "DB_HOST no configurado"
fi

TELEGRAM_TOKEN=$(docker exec airflow_webserver airflow variables get TELEGRAM_BOT_TOKEN 2>/dev/null || echo "")
if [ -n "$TELEGRAM_TOKEN" ] && [ "$TELEGRAM_TOKEN" != "TU_TOKEN_AQUI" ]; then
    print_status 0 "TELEGRAM_BOT_TOKEN configurado"
else
    print_status 1 "TELEGRAM_BOT_TOKEN no configurado"
fi

TELEGRAM_CHAT=$(docker exec airflow_webserver airflow variables get TELEGRAM_CHAT_ID 2>/dev/null || echo "")
if [ -n "$TELEGRAM_CHAT" ] && [ "$TELEGRAM_CHAT" != "TU_CHAT_ID_AQUI" ]; then
    print_status 0 "TELEGRAM_CHAT_ID configurado"
else
    print_status 1 "TELEGRAM_CHAT_ID no configurado"
fi

# 7. Verificar conexión a PostgreSQL del inventario
echo ""
echo "7️⃣  Conexión a PostgreSQL del Inventario"

if docker exec airflow_webserver psql -h host.docker.internal -U postgres -d inventario_hospitalario -c "SELECT 1" > /dev/null 2>&1; then
    print_status 0 "Conexión a inventario_hospitalario"
else
    print_status 1 "No se puede conectar a inventario_hospitalario"
    echo "  💡 Tip: Verifica que PostgreSQL esté corriendo y accesible desde Docker"
fi

# 8. Resumen
echo ""
echo "===================================="
echo "📊 Resumen"
echo "===================================="
echo ""
echo "Airflow Web: http://localhost:8080"
echo "Flower: http://localhost:5555"
echo "Usuario: admin"
echo "Contraseña: admin"
echo ""
echo "Para más información, ver README.md"
