#!/usr/bin/env bash
# Usage:
#   ./logs.sh             # all services
#   ./logs.sh server      # just the API server
#   ./logs.sh client      # just the Gradio client
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "Error: neither 'docker compose' nor 'docker-compose' is installed." >&2
    exit 1
fi

$COMPOSE logs -f --tail=100 "$@"
