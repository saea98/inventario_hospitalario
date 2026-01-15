#!/bin/bash
set -e

echo "=== DEPLOY CALIDAD ==="
cd ~/inventario/inventario_hospitalario

echo "1. Checkout release..."
git checkout release/v1.0.0

echo "2. Pull desde GitHub..."
git pull origin release/v1.0.0

echo "3. Aplicar migraciones..."
docker exec -it inventario_qa python manage.py migrate

echo "4. Reiniciar contenedor..."
docker-compose restart web

echo "5. Verificar estado..."
docker exec -it inventario_qa python manage.py check

echo "✓ CALIDAD actualizado correctamente"
