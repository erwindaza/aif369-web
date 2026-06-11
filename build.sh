#!/usr/bin/env bash
# ─── Vercel Build Script ───
# Injects environment variables into static files at build time.
# Vercel env vars are set in the Vercel dashboard (not in code).
#
# Required Vercel Environment Variables:
#   GA_MEASUREMENT_ID  — Google Analytics 4 ID (e.g. G-VV325VBQYV)

set -euo pipefail

echo "=== AIF369 Build: injecting environment config ==="

# Generate runtime config from Vercel env vars
cat > _config.js <<EOF
// Auto-generated at build time — DO NOT EDIT
window.__AIF369_CONFIG__ = {
  GA_MEASUREMENT_ID: "${GA_MEASUREMENT_ID:-}",
  ENVIRONMENT: "${VERCEL_ENV:-development}"
};
EOF

echo "  ✓ _config.js generated (GA4: ${GA_MEASUREMENT_ID:+set}${GA_MEASUREMENT_ID:-NOT SET})"
echo "  ✓ Environment: ${VERCEL_ENV:-development}"
echo "=== Build complete ==="
