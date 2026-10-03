#!/usr/bin/env bash
# Starts the WhatsApp agent as the current user when systemd is unavailable.
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/whatsapp-agent}"
NODE_BIN="${NODE_BIN:-$HOME/.local/bin/node}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8090/health}"

cd "$APP_DIR"
mkdir -p runtime
LOG="$APP_DIR/runtime/manual-agent.log"
touch "$LOG"

if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
  exit 0
fi

if [ -f runtime/manual-agent.pid ]; then
  OLD_PID="$(cat runtime/manual-agent.pid || true)"
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
    exit 0
  fi
fi

nohup "$NODE_BIN" src/index.js > "$LOG" 2>&1 &
echo "$!" > runtime/manual-agent.pid
