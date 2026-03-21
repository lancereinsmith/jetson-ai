#!/usr/bin/env bash
# =============================================================================
# Start the Jetson Nano AI Server
# Usage: bash scripts/start_server.sh [--dev]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Skip venv activation when running inside Docker
if [ ! -f "/.dockerenv" ]; then
    # Activate venv if it exists and we're not already in one
    if [ -z "${VIRTUAL_ENV:-}" ] && [ -d "venv" ]; then
        source venv/bin/activate
    fi
fi

# Set Jetson-specific environment variables for performance
export OPENBLAS_CORETYPE=ARMV8
export OMP_NUM_THREADS=4
export FLASK_APP=src.main:app

# Create logs directory
mkdir -p logs

HOST="${JETSON_AI_HOST:-0.0.0.0}"
PORT="${JETSON_AI_PORT:-8000}"

if [ "${1:-}" = "--dev" ]; then
    echo "Starting in development mode (auto-reload)..."
    export FLASK_DEBUG=1
    python3 -m flask run --host "$HOST" --port "$PORT"
else
    echo "Starting Jetson Nano AI Server..."
    echo "  Host: $HOST"
    echo "  Port: $PORT"
    echo "  URL:  http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'localhost'):$PORT"
    echo ""
    python3 -m flask run --host "$HOST" --port "$PORT" \
        2>&1 | tee logs/server.log
fi
