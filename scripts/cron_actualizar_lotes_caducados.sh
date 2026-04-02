#!/bin/sh
# Marca lotes caducados vía manage.py, sin Airflow.
#
# Por defecto ejecuta DENTRO del contenedor Docker `inventario_dev`
# (container_name del servicio web en docker-compose.yml, WORKDIR /app).
#
# Crontab en el HOST (el que tiene Docker), diario 2:00:
#   0 2 * * * /ruta/al/repo/scripts/cron_actualizar_lotes_caducados.sh
#
# Variables opcionales:
#   RUN_INSIDE_DOCKER=0     — no usar docker; usar PROJECT_ROOT + PYTHON en el host
#   CONTAINER_NAME          — default: inventario_dev
#   CONTAINER_WORKDIR       — default: /app
#   DOCKER                  — default: docker (puede ser podman)
#   LOG                     — default: $HOME/logs/inventario_lotes_caducados.log (sin permisos root)
#                             Para /var/log (una vez, como root):
#                               sudo touch /var/log/inventario_lotes_caducados.log
#                               sudo chown USUARIO_CRON:USUARIO_CRON /var/log/inventario_lotes_caducados.log
#                             Luego en crontab: LOG=/var/log/inventario_lotes_caducados.log
#   PROJECT_ROOT / PYTHON   — solo si RUN_INSIDE_DOCKER=0
#
# Compatible con /bin/sh (dash). Ejecutar: sh scripts/... o ./scripts/... (chmod +x).

set -eu

# Log por defecto: $HOME/logs/... (sin root). Solo entonces, si no se puede crear ~/logs, usar /tmp.
if [ -z "${LOG:-}" ]; then
  LOG="${HOME:-/tmp}/logs/inventario_lotes_caducados.log"
  if ! mkdir -p "$(dirname "$LOG")" 2>/dev/null; then
    LOG="/tmp/inventario_lotes_caducados.log"
  fi
fi

RUN_INSIDE_DOCKER="${RUN_INSIDE_DOCKER:-1}"
CONTAINER_NAME="${CONTAINER_NAME:-inventario_dev}"
CONTAINER_WORKDIR="${CONTAINER_WORKDIR:-/app}"
DOCKER="${DOCKER:-docker}"

PROJECT_ROOT="${PROJECT_ROOT:-/var/www/inventario_hospitalario}"
PYTHON="${PYTHON:-python3}"

exec >>"$LOG" 2>&1
echo "===== $(date '+%Y-%m-%dT%H:%M:%S') actualizar_lotes_caducados ====="

if [ "$RUN_INSIDE_DOCKER" = "1" ]; then
  if ! "$DOCKER" inspect -f '{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null | grep -q true; then
    echo "ERROR: contenedor $CONTAINER_NAME no está en ejecución. Arranca con: docker compose up -d"
    exit 1
  fi
  "$DOCKER" exec "$CONTAINER_NAME" sh -c "cd ${CONTAINER_WORKDIR} && python manage.py actualizar_lotes_caducados"
else
  cd "$PROJECT_ROOT"
  "$PYTHON" manage.py actualizar_lotes_caducados
fi

echo "===== fin ====="
