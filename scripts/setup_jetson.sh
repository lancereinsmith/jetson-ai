#!/usr/bin/env bash
# =============================================================================
# Jetson Nano AI Server - Full Setup Script
# Run this on your Jetson Nano after cloning the repository.
# Usage: sudo bash scripts/setup_jetson.sh
# =============================================================================
set -euo pipefail

echo "============================================"
echo "  Jetson Nano AI Server - Setup"
echo "============================================"
echo ""

# --- Check we're on a Jetson ---
if [ ! -f /etc/nv_tegra_release ]; then
    echo "WARNING: /etc/nv_tegra_release not found."
    echo "This script is intended for NVIDIA Jetson devices."
    read -rp "Continue anyway? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# --- Check for root ---
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run with sudo: sudo bash scripts/setup_jetson.sh"
    exit 1
fi

REAL_USER="${SUDO_USER:-$USER}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[1/6] Updating system packages and installing Python 3.8..."
apt-get update
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y \
    python3.8 \
    python3.8-venv \
    python3.8-dev \
    libopenblas-base \
    libopenmpi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpython3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    curl \
    wget

echo ""
echo "[2/6] Setting up Python 3.8 virtual environment..."
cd "$PROJECT_DIR"
sudo -u "$REAL_USER" python3.8 -m venv venv
source venv/bin/activate

echo ""
echo "[3/6] Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
export OPENBLAS_CORETYPE=ARMV8

echo "[4/6] Installing PyTorch for Jetson..."
# PyTorch wheels for JetPack 4.6.x + Python 3.8
# Check https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048 for latest

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Detected Python $PY_VERSION"

if python3 -c "import torch" 2>/dev/null; then
    TORCH_VER=$(python3 -c "import torch; print(torch.__version__)")
    echo "PyTorch $TORCH_VER is already installed."
    python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
else
    echo ""
    echo "PyTorch is NOT installed."
    echo "Due to Jetson's ARM architecture, PyTorch must be installed from NVIDIA's wheels."
    echo ""
    echo "Please visit: https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048"
    echo "Download the wheel matching your JetPack version and Python $PY_VERSION."
    echo ""
    echo "Example (JetPack 4.6, Python 3.8):"
    echo "  wget https://nvidia.box.com/shared/static/ssf2v7pf5i245fber4hw0a2mkgdrbd4o.whl -O torch-1.13.0a0+d0d6b1f-cp38-cp38-linux_aarch64.whl"
    echo "  source venv/bin/activate"
    echo "  pip install torch-1.13.0a0+d0d6b1f-cp38-cp38-linux_aarch64.whl"
    echo ""
    echo "Then install torchvision from source:"
    echo "  git clone --branch v0.14.0 https://github.com/pytorch/vision torchvision"
    echo "  cd torchvision && python setup.py install"
    echo ""
fi

echo ""
echo "[5/6] Creating directories and downloading labels..."
sudo -u "$REAL_USER" mkdir -p "$PROJECT_DIR/models/weights"
sudo -u "$REAL_USER" mkdir -p "$PROJECT_DIR/logs"

# Download ImageNet labels
LABELS_FILE="$PROJECT_DIR/models/weights/imagenet_labels.txt"
if [ ! -f "$LABELS_FILE" ]; then
    echo "Downloading ImageNet labels..."
    curl -sL "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt" \
        -o "$LABELS_FILE"
    chown "$REAL_USER":"$REAL_USER" "$LABELS_FILE"
fi

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Install PyTorch if not already installed (see instructions above)"
echo "  2. (Optional) Download LLM model: bash scripts/download_models.sh"
echo "  3. Activate the environment: source venv/bin/activate"
echo "  4. Start the server: bash scripts/start_server.sh"
echo "  5. Access from any device: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
