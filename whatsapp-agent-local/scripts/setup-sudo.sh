#!/usr/bin/env bash
# Operaciones que requieren root en agent01.
# Uso: printf '<password>' | sudo -S bash scripts/setup-sudo.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/home/erwin/whatsapp-agent}"
SERVICE="whatsapp-agent"
SERVICE_USER="${SERVICE_USER:-erwin}"

export DEBIAN_FRONTEND=noninteractive

if ! command -v psql >/dev/null 2>&1; then
  echo "==> Instalando PostgreSQL"
  apt-get update -y -qq
  apt-get install -y -qq postgresql postgresql-contrib
fi
systemctl enable --now postgresql >/dev/null 2>&1 || true

echo "==> Leyendo credenciales de ${APP_DIR}/.env"
set -a
# shellcheck disable=SC1091
. "${APP_DIR}/.env"
set +a

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${PGUSER}'" | grep -q 1; then
  echo "==> Creando rol ${PGUSER}"
  sudo -u postgres psql -qc "CREATE ROLE ${PGUSER} LOGIN PASSWORD '${PGPASSWORD}'"
fi
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${PGDATABASE}'" | grep -q 1; then
  echo "==> Creando base ${PGDATABASE}"
  sudo -u postgres createdb -O "${PGUSER}" "${PGDATABASE}"
fi

echo "==> Instalando servicio ${SERVICE}"
cat > "/etc/systemd/system/${SERVICE}.service" <<EOF
[Unit]
Description=AIF369 WhatsApp Agent local (Baileys + PostgreSQL + Ollama)
After=network-online.target ollama.service
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${APP_DIR}
ExecStart=/home/${SERVICE_USER}/.local/bin/node src/index.js
Restart=on-failure
RestartSec=5
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE}" >/dev/null

echo "==> Verificando conexion a PostgreSQL como ${PGUSER}"
PGPASSWORD="${PGPASSWORD}" psql -h "${PGHOST:-127.0.0.1}" -U "${PGUSER}" -d "${PGDATABASE}" -tAc "SELECT 'pg_ok'" || {
  echo "ERROR: el usuario no pudo conectarse a la base"; exit 1; }

echo "setup-sudo: OK (servicio habilitado, base lista)"
