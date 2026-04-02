#!/usr/bin/env bash
# Ejecutar lotes caducados sin Airflow (bajo consumo de recursos).
# Ajustar PROJECT_ROOT y PYTHON al entorno del servidor.
#
# Crontab (diario 2:00, como el DAG):
#   0 2 * * * /ruta/al/repo/scripts/cron_actualizar_lotes_caducados.sh
#
# Requisitos: .env en PROJECT_ROOT con DATABASES y opcionalmente TELEGRAM_*

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/var/www/inventario_hospitalario}"
PYTHON="${PYTHON:-python3}"
LOG="${LOG:-/var/log/inventario_lotes_caducados.log}"

cd "$PROJECT_ROOT"
exec >>"$LOG" 2>&1
echo "===== $(date -Iseconds) actualizar_lotes_caducados ====="
"$PYTHON" manage.py actualizar_lotes_caducados
echo "===== fin ====="
