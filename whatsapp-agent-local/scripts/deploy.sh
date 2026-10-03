#!/usr/bin/env bash
# Sincroniza el desarrollo al laptop agent01 (Lenovo Legion).
# Uso: bash scripts/deploy.sh [host]   (por defecto: agent01)
set -euo pipefail

HOST="${1:-agent01}"
SRC="$(cd "$(dirname "$0")/.." && pwd)/"

rsync -az --delete \
  --exclude node_modules \
  --exclude data \
  --exclude runtime \
  --exclude .env \
  --exclude '__pycache__' \
  --exclude '.DS_Store' \
  "$SRC" "${HOST}:~/whatsapp-agent/"

echo "OK: codigo sincronizado en ${HOST}:~/whatsapp-agent"
echo "Siguiente: ssh ${HOST} 'cd ~/whatsapp-agent && npm install'"
