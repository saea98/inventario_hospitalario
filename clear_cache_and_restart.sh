#!/bin/bash

# Script para limpiar caché de Django y reiniciar los servicios
# Ejecutar en cada ambiente (DEV, QA, PROD)

echo "🧹 Limpiando caché de Django..."

# Limpiar caché de Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Limpiar caché de Redis (si está disponible)
redis-cli FLUSHALL 2>/dev/null || echo "⚠️  Redis no disponible, saltando..."

# Limpiar caché de Django (si existe)
python manage.py clear_cache 2>/dev/null || echo "⚠️  clear_cache no disponible"

# Limpiar archivos estáticos compilados
python manage.py collectstatic --noinput --clear 2>/dev/null || echo "⚠️  collectstatic no disponible"

echo "✅ Caché limpiado"

# Reiniciar Docker si está disponible
if command -v docker-compose &> /dev/null; then
    echo "🔄 Reiniciando contenedores Docker..."
    docker-compose restart web
    echo "✅ Contenedores reiniciados"
elif command -v docker &> /dev/null; then
    echo "🔄 Reiniciando contenedor Docker..."
    docker restart inventario_dev 2>/dev/null || docker restart inventario_qa 2>/dev/null || docker restart inventario_prod 2>/dev/null
    echo "✅ Contenedor reiniciado"
else
    echo "⚠️  Docker no disponible, reinicia manualmente el servidor"
fi

echo "🎉 Listo. Recarga la página en el navegador (Ctrl+F5 o Cmd+Shift+R)"
