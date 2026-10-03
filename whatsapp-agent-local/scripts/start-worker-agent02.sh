#!/usr/bin/env bash
# Starts the backoffice sales worker as the current user.
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/whatsapp-agent}"
NODE_BIN="${NODE_BIN:-}"
if [ -z "$NODE_BIN" ]; then
  NODE_BIN="$(command -v node || true)"
fi
if [ -z "$NODE_BIN" ]; then
  NODE_BIN="$HOME/.local/bin/node"
fi

cd "$APP_DIR"
mkdir -p runtime
LOG="$APP_DIR/runtime/worker-agent02.log"
PID_FILE="$APP_DIR/runtime/worker-agent02.pid"
touch "$LOG"

if [ -f "$PID_FILE" ]; then
  OLD_PID="$(cat "$PID_FILE" || true)"
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
    exit 0
  fi
fi

nohup "$NODE_BIN" src/worker-loop.js > "$LOG" 2>&1 &
echo "$!" > "$PID_FILE"
