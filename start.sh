#!/usr/bin/env bash
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

echo "==> Building images..."
$COMPOSE build

echo "==> Starting containers in detached mode..."
$COMPOSE up -d

echo
echo "==> Container status:"
$COMPOSE ps

echo
echo "Minimaxer is running:"
echo "  Client (UI):    http://localhost:7860/"
echo "  Server (API):   http://localhost:8000/"
echo "  API docs:       http://localhost:8000/docs"
echo "  API health:     http://localhost:8000/api/health"
echo
echo "Logs:  ./logs.sh             (all services)"
echo "       ./logs.sh server      (just one)"
echo "Stop:  ./stop.sh"
