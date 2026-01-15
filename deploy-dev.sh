#!/bin/bash
set -e

echo "=== DEPLOY DESARROLLO ==="
cd ~/inventario/inventario_hospitalario

echo "1. Checkout develop..."
git checkout develop

echo "2. Pull desde GitHub..."
git pull origin develop

echo "3. Aplicar migraciones..."
docker exec -it inventario_dev python manage.py migrate

echo "4. Reiniciar contenedor..."
docker-compose restart web

echo "5. Verificar estado..."
docker exec -it inventario_dev python manage.py check

echo "✓ DESARROLLO actualizado correctamente"
