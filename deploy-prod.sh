#!/bin/bash
set -e

echo "=== DEPLOY PRODUCCIÓN ==="
cd ~/inventario/inventario_hospitalario

echo "1. Checkout main..."
git checkout main

echo "2. Pull desde GitHub..."
git pull origin main

echo "3. Aplicar migraciones..."
docker exec -it inventario_dev_2 python manage.py migrate

echo "4. Reiniciar contenedor..."
docker-compose restart web

echo "5. Verificar estado..."
docker exec -it inventario_dev_2 python manage.py check

echo "✓ PRODUCCIÓN actualizado correctamente"
