#!/usr/bin/env bash
# Smoke test: server is up and /health returns {"status":"ok", ...}.
# Usage:  ./tests/test_health.sh [port]
set -euo pipefail

PORT="${1:-8000}"
HOST="${HOST:-localhost}"

body=$(curl -sf "http://${HOST}:${PORT}/health")
echo "$body" | python3 -m json.tool

status=$(echo "$body" | python3 -c "import json, sys; print(json.load(sys.stdin)['status'])")
if [ "$status" != "ok" ]; then
    echo "ERROR: status was $status, expected 'ok'"
    exit 1
fi
echo "OK"
