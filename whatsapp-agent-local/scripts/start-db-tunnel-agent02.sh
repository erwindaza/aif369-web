#!/usr/bin/env bash
# Opens a local Postgres tunnel from agent02 to agent01.
set -euo pipefail

REMOTE_DB_HOST="${REMOTE_DB_HOST:-192.168.100.93}"
REMOTE_DB_USER="${REMOTE_DB_USER:-erwin}"
LOCAL_DB_PORT="${LOCAL_DB_PORT:-15432}"
REMOTE_DB_PORT="${REMOTE_DB_PORT:-5432}"
SSH_IDENTITY_FILE="${SSH_IDENTITY_FILE:-$HOME/.ssh/agent02_to_agent01_ed25519}"

mkdir -p "$HOME/whatsapp-agent/runtime"
PID_FILE="$HOME/whatsapp-agent/runtime/db-tunnel-agent02.pid"
LOG="$HOME/whatsapp-agent/runtime/db-tunnel-agent02.log"

if [ -f "$PID_FILE" ]; then
  OLD_PID="$(cat "$PID_FILE" || true)"
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
    exit 0
  fi
fi

nohup ssh \
  -i "$SSH_IDENTITY_FILE" \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -N \
  -L "127.0.0.1:${LOCAL_DB_PORT}:127.0.0.1:${REMOTE_DB_PORT}" \
  "${REMOTE_DB_USER}@${REMOTE_DB_HOST}" > "$LOG" 2>&1 &
echo "$!" > "$PID_FILE"
