#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"

case "$TARGET" in
  prod|production|main|aif369-backend-api|aif369-master-api|terraform-production)
    if [ "${AIF369_HUMAN_PROD_APPROVAL:-}" != "true" ]; then
      echo "Blocked by AIF369 agent policy: production/main actions require explicit human approval." >&2
      exit 1
    fi
    ;;
esac

echo "Agent policy check passed for target: ${TARGET:-unspecified}"
