#!/usr/bin/env bash
# =============================================================================
# Build and run the Jetson AI Server in Docker
# Usage: sudo bash scripts/docker_run.sh [--build]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Docker requires root on JetPack 4.6
if [ "$EUID" -ne 0 ]; then
    echo "Docker requires root. Re-running with sudo..."
    exec sudo bash "$0" "$@"
fi

IMAGE_NAME="jetson-ai"
CONTAINER_NAME="jetson-ai"

# Build if image doesn't exist or --build flag passed
if [ "${1:-}" = "--build" ] || ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "Building $IMAGE_NAME image..."
    docker build -t "$IMAGE_NAME" .
fi

# Stop existing container if running
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "Stopping existing $CONTAINER_NAME container..."
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

# Create model weights dir if it doesn't exist
mkdir -p models/weights

echo "Starting $CONTAINER_NAME..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --runtime nvidia \
    -p 8000:8000 \
    -v "$(pwd)/configs:/app/configs" \
    -e OPENBLAS_CORETYPE=ARMV8 \
    -e CUDA_VISIBLE_DEVICES=0 \
    --restart unless-stopped \
    "$IMAGE_NAME"

echo ""
echo "Container started. Useful commands:"
echo "  sudo docker logs -f $CONTAINER_NAME    # View logs"
echo "  sudo docker stop $CONTAINER_NAME       # Stop"
echo "  sudo docker start $CONTAINER_NAME      # Restart"
echo ""
echo "Waiting for server..."
sleep 3
curl -sf http://localhost:8000/health && echo " Server is up!" || echo " Server still starting — check: docker logs -f $CONTAINER_NAME"
