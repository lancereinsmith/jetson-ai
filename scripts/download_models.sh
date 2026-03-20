#!/usr/bin/env bash
# =============================================================================
# Download model weights for the Jetson Nano AI Server
# Usage: bash scripts/download_models.sh [--all | --llm | --labels]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WEIGHTS_DIR="$PROJECT_DIR/models/weights"

mkdir -p "$WEIGHTS_DIR"

download_labels() {
    echo "--- Downloading ImageNet labels ---"
    if [ -f "$WEIGHTS_DIR/imagenet_labels.txt" ]; then
        echo "Already exists. Skipping."
    else
        curl -sL "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt" \
            -o "$WEIGHTS_DIR/imagenet_labels.txt"
        echo "Done: $WEIGHTS_DIR/imagenet_labels.txt"
    fi
}

download_llm() {
    echo "--- Downloading TinyLlama 1.1B Chat (Q4_K_M quantized, ~670MB) ---"
    LLM_FILE="$WEIGHTS_DIR/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    if [ -f "$LLM_FILE" ]; then
        echo "Already exists. Skipping."
    else
        echo "This will download ~670MB. Continue? (y/N)"
        read -rp "> " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            echo "Skipped."
            return
        fi
        wget -O "$LLM_FILE" \
            "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        echo "Done: $LLM_FILE"
    fi
}

case "${1:-all}" in
    --labels)
        download_labels
        ;;
    --llm)
        download_llm
        ;;
    --all|all)
        download_labels
        echo ""
        download_llm
        ;;
    *)
        echo "Usage: $0 [--all | --llm | --labels]"
        exit 1
        ;;
esac

echo ""
echo "PyTorch vision models (MobileNetV2, SSD) are downloaded"
echo "automatically on first use via torchvision."
