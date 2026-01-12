#!/bin/bash

# Script de limpieza de Airflow
# Detiene y elimina todos los contenedores y volúmenes

set -e

echo "🧹 Limpieza de Airflow"
echo "====================="
echo ""

read -p "¿Estás seguro de que deseas eliminar todos los contenedores y volúmenes de Airflow? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Operación cancelada"
    exit 1
fi

echo ""
echo "⏹️  Deteniendo contenedores..."
docker-compose down

echo "🗑️  Eliminando volúmenes..."
docker-compose down -v

echo ""
echo "📁 Limpiando directorios locales..."
rm -rf logs/*
rm -rf config/__pycache__

echo ""
echo "✅ Limpieza completada"
echo ""
echo "Para reiniciar Airflow:"
echo "  docker-compose up -d"
echo "  bash init_airflow.sh"
