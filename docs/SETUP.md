# Setup Guide

Complete instructions for setting up the Jetson Nano AI Server from a fresh Jetson Nano.

## Prerequisites

### Hardware

- NVIDIA Jetson Nano Developer Kit (4GB version recommended)
- MicroSD card: 32GB or larger (64GB recommended)
- Power supply: 5V 4A barrel jack (recommended over micro-USB for stability)
- Ethernet cable or compatible WiFi adapter
- (Optional) A fan or heatsink for sustained workloads

### Software

- NVIDIA JetPack 4.6.x flashed to the SD card

## Step 1: Flash JetPack to SD Card

If your Jetson Nano is not already set up:

1. Download JetPack SD card image from [NVIDIA's developer site](https://developer.nvidia.com/embedded/jetpack-sdk-46)
2. Flash to SD card using [Balena Etcher](https://www.balena.io/etcher/) or `dd`:

   ```bash
   # Example with dd (replace /dev/sdX with your SD card device)
   sudo dd if=jetson-nano-jp46-sd-card-image.zip of=/dev/sdX bs=1M status=progress
   ```

3. Insert SD card into Jetson Nano
4. Connect a monitor, keyboard, and ethernet cable
5. Power on and complete the initial Ubuntu setup wizard

## Step 2: Initial Jetson Configuration

After first boot, connect via SSH or use the terminal directly:

```bash
# Update the system
sudo apt-get update && sudo apt-get upgrade -y

# Set the Jetson to maximum performance mode
sudo nvpmodel -m 0        # Max performance (10W mode)
sudo jetson_clocks         # Lock clocks at maximum frequency

# Verify CUDA is available
nvcc --version
# Should show CUDA 10.2

# Check JetPack version
head -n 1 /etc/nv_tegra_release
```

### Set a Static IP (Recommended)

So you can always reach your Jetson at the same address:

```bash
# Find your current network interface and IP
ip addr show

# Option A: Set static IP via NetworkManager (for Ethernet)
sudo nmcli con mod "Wired connection 1" \
  ipv4.addresses "192.168.1.100/24" \
  ipv4.gateway "192.168.1.1" \
  ipv4.dns "8.8.8.8,8.8.4.4" \
  ipv4.method "manual"
sudo nmcli con up "Wired connection 1"

# Option B: Or configure via your router's DHCP reservation
# (assign a fixed IP to the Jetson's MAC address in your router settings)
```

### Enable SSH (if not already enabled)

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

Now you can work remotely:

```bash
# From your Mac/PC:
ssh <username>@192.168.1.100
```

## Step 3: Clone the Repository

```bash
# On the Jetson Nano:
cd ~
git clone <your-repo-url> jetson-ai
cd jetson-ai
```

## Step 4: Run the Setup Script

The setup script installs system packages, creates a Python virtual environment, and installs dependencies:

```bash
sudo bash scripts/setup_jetson.sh
```

This will:

1. Install system dependencies (libopenblas, libjpeg, etc.)
2. Create a Python virtual environment at `./venv`
3. Install pip packages from `requirements.txt`
4. Check if PyTorch is installed
5. Download ImageNet class labels

### Install PyTorch (if not already installed)

PyTorch must be installed from NVIDIA's pre-built wheels for ARM64. The setup script will tell you if it needs to be installed.

```bash
# Check your Python version
python3 --version

# Download the correct PyTorch wheel for your JetPack + Python version
# Visit: https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048

# Example for JetPack 4.6 + Python 3.6:
wget https://nvidia.box.com/shared/static/p57jwntv436lfrd78inwl7iml6p13fzh.whl -O torch-1.12.0-cp36-cp36m-linux_aarch64.whl
pip install torch-1.12.0-cp36-cp36m-linux_aarch64.whl

# Verify PyTorch + CUDA:
python3 -c "import torch; print(torch.__version__); print(f'CUDA: {torch.cuda.is_available()}')"
# Expected: 1.12.0 (or similar), CUDA: True
```

### Install torchvision (from source)

torchvision must be built from source to match your PyTorch version:

```bash
# Install build dependencies
sudo apt-get install -y libjpeg-dev zlib1g-dev libpython3-dev

# Clone and build torchvision
# Match the version to your PyTorch version:
#   PyTorch 1.10 → torchvision 0.11
#   PyTorch 1.11 → torchvision 0.12
#   PyTorch 1.12 → torchvision 0.13
git clone --branch v0.13.0 https://github.com/pytorch/vision torchvision
cd torchvision
export BUILD_VERSION=0.13.0
python3 setup.py install
cd ..
rm -rf torchvision  # Clean up source

# Verify
python3 -c "import torchvision; print(torchvision.__version__)"
```

## Step 5: Download Models (Optional)

PyTorch vision models (MobileNetV2, SSD) download automatically on first use. The only manual download is the LLM model (if you want text generation):

```bash
# Download TinyLlama 1.1B (Q4_K_M quantized, ~670MB)
bash scripts/download_models.sh --llm
```

If you want to use the LLM, you also need `llama-cpp-python` with CUDA:

```bash
# Build llama-cpp-python with CUDA support
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python

# Then enable text_generator in configs/config.yaml:
# text_generator:
#   enabled: true
```

## Step 6: Start the Server

```bash
# Activate environment
source venv/bin/activate

# Start the server
bash scripts/start_server.sh

# Or in development mode (auto-reload on code changes):
bash scripts/start_server.sh --dev
```

The server starts on port 8000 by default. You'll see output like:

```text
Starting Jetson Nano AI Server...
  Host: 0.0.0.0
  Port: 8000
  URL:  http://192.168.1.100:8000
  API:  http://192.168.1.100:8000/api
```

## Step 7: Verify It Works

From any device on your network:

```bash
# Health check
curl http://192.168.1.100:8000/health
# → {"status":"ok"}

# System info
curl http://192.168.1.100:8000/system/info
# → CPU, memory, GPU, temperature info

# List available API endpoints:
# http://192.168.1.100:8000/api
```

The first request to each model endpoint will be slower as the model loads into memory. Subsequent requests will be fast.

## Step 8: Run as a System Service (Optional)

To have the server start automatically on boot:

```bash
sudo tee /etc/systemd/service/jetson-ai.service << 'EOF'
[Unit]
Description=Jetson Nano AI Server
After=network.target

[Service]
Type=simple
User=<your-username>
WorkingDirectory=/home/<your-username>/jetson-ai
Environment=PATH=/home/<your-username>/jetson-ai/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=OPENBLAS_CORETYPE=ARMV8
Environment=FLASK_APP=src.main:app
ExecStart=/home/<your-username>/jetson-ai/venv/bin/python3 -m flask run --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Replace <your-username> with your actual username, then:
sudo systemctl daemon-reload
sudo systemctl enable jetson-ai
sudo systemctl start jetson-ai

# Check status:
sudo systemctl status jetson-ai

# View logs:
journalctl -u jetson-ai -f
```

## Step 9: Run Benchmarks (Optional)

With the server running:

```bash
python3 scripts/benchmark.py
```

This tests all endpoints and reports latency. See [Models Guide](MODELS.md) for expected performance numbers.

## Network Diagram

```text
Your Home Network
┌─────────────────────────────────────────┐
│                                         │
│   ┌──────────┐     ┌──────────────┐    │
│   │  Phone   │────▶│              │    │
│   └──────────┘     │  Jetson Nano │    │
│   ┌──────────┐     │  AI Server   │    │
│   │  Laptop  │────▶│  :8000       │    │
│   └──────────┘     │              │    │
│   ┌──────────┐     └──────────────┘    │
│   │  Other   │────▶      ▲             │
│   │  Device  │           │             │
│   └──────────┘     Router/Switch       │
│                                         │
└─────────────────────────────────────────┘
```
