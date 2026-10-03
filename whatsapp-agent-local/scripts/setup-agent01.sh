#!/usr/bin/env bash
# Instala y configura el agente de WhatsApp 100% local en agent01 (Lenovo Legion).
# Ejecutar DESDE agent01:  bash scripts/setup-agent01.sh
# Necesita sudo (instala PostgreSQL y el servicio systemd).
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/whatsapp-agent}"
NODE_VERSION="${NODE_VERSION:-v22.14.0}"
NODE_PREFIX="$HOME/.local/opt/node-${NODE_VERSION}-linux-x64"
BIN_DIR="$HOME/.local/bin"
DB_NAME="whatsapp_agent"
DB_USER="wa_agent"
SERVICE="whatsapp-agent"

log() { printf '\n==> %s\n' "$1"; }

log "Verificando sudo (se usara para PostgreSQL y systemd)"
sudo -v

# 1) Node.js en espacio de usuario (sin sudo)
if ! command -v node >/dev/null 2>&1 && [ ! -x "$NODE_PREFIX/bin/node" ]; then
  log "Instalando Node.js ${NODE_VERSION} en $NODE_PREFIX"
  mkdir -p "$NODE_PREFIX" "$BIN_DIR" "$HOME/.local/opt"
  curl -fsSL "https://nodejs.org/dist/${NODE_VERSION}/node-${NODE_VERSION}-linux-x64.tar.xz" \
    | tar -xJ -C "$HOME/.local/opt"
  ln -sf "$NODE_PREFIX/bin/node" "$BIN_DIR/node"
  ln -sf "$NODE_PREFIX/bin/npm" "$BIN_DIR/npm"
  ln -sf "$NODE_PREFIX/bin/npx" "$BIN_DIR/npx"
fi
export PATH="$BIN_DIR:$PATH"
node --version
npm --version

# 2) PostgreSQL
if ! command -v psql >/dev/null 2>&1; then
  log "Instalando PostgreSQL (sudo)"
  sudo apt-get update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib
fi
sudo systemctl enable --now postgresql
log "PostgreSQL listo: $(psql --version)"

# 3) Base de datos y usuario (password generada, nunca en Git)
cd "$APP_DIR"
if [ ! -f .env ]; then
  log "Creando .env con credenciales locales"
  PG_PASSWORD="$(openssl rand -hex 24)"
  sed -e "s|^PGPASSWORD=.*|PGPASSWORD=${PG_PASSWORD}|" \
      -e "s|^DATA_DIR=.*|DATA_DIR=${APP_DIR}/data|" \
      .env.example > .env
  chmod 600 .env
fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1; then
  log "Creando rol ${DB_USER}"
  sudo -u postgres psql -qc "CREATE ROLE ${DB_USER} LOGIN PASSWORD '${PGPASSWORD}'"
fi
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  log "Creando base ${DB_NAME}"
  sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"
fi

# 4) Dependencias + esquema
log "Instalando dependencias de Node"
npm install --omit=dev
log "Aplicando esquema SQL"
npm run db:init

# 5) Servicio systemd
log "Instalando servicio ${SERVICE}"
sudo tee "/etc/systemd/system/${SERVICE}.service" > /dev/null <<EOF
[Unit]
Description=AIF369 WhatsApp Agent local (Baileys + PostgreSQL + Ollama)
After=network-online.target ollama.service
Wants=network-online.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${APP_DIR}
ExecStart=${BIN_DIR}/node src/index.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE"

cat <<EOF

Instalacion completa.

Siguiente paso:
  1. sudo systemctl start ${SERVICE}
  2. journalctl -u ${SERVICE} -f      # escanea el QR que aparece ahi
  3. Ctrl+C para salir del log (el agente sigue corriendo)

Reportes locales:
  cd ${APP_DIR} && npm run leads
EOF
