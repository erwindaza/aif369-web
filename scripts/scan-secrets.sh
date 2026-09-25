#!/usr/bin/env bash
set -euo pipefail

PATTERN='AIza[0-9A-Za-z_-]{20,}|ya29\.|sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]+|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]+|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC |DSA |PRIVATE )?PRIVATE KEY-----|Bearer[[:space:]]+[A-Za-z0-9._-]{20,}'

if git ls-files -z | xargs -0 rg -n --pcre2 "$PATTERN"; then
  echo "Potential secret detected in tracked files." >&2
  exit 1
fi

echo "No high-confidence secrets detected in tracked files."
