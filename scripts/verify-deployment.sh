#!/usr/bin/env bash
# Smoke-test a deployed API. Usage:
#   API_BASE_URL=https://api.example.com ./scripts/verify-deployment.sh
set -euo pipefail
BASE="${API_BASE_URL:-}"
if [[ -z "$BASE" ]]; then
  echo "Usage: API_BASE_URL=https://api.example.com $0" >&2
  exit 1
fi
BASE="${BASE%/}"
echo "GET ${BASE}/api/health"
curl -sS -f "${BASE}/api/health" | head -c 500
echo
echo "OK"
