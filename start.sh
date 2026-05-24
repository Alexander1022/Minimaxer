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

echo "==> Building image..."
$COMPOSE build

echo "==> Starting container in detached mode..."
$COMPOSE up -d

echo
echo "==> Container status:"
$COMPOSE ps

echo
echo "Minimaxer API is running:"
echo "  Root:    http://localhost:8000/"
echo "  Health:  http://localhost:8000/api/health"
echo "  Solve:   http://localhost:8000/api/solve   (POST)"
echo "  Docs:    http://localhost:8000/docs"
echo
echo "Logs:  ./logs.sh        (or: $COMPOSE logs -f)"
echo "Stop:  ./stop.sh"
