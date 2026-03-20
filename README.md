# Jetson Nano AI Server

A local AI inference server that runs on an NVIDIA Jetson Nano (4GB). Exposes a REST API accessible from any device on your home network for image classification, object detection, text embeddings, text similarity, and text generation.

## Capabilities

| Endpoint | Model | What It Does |
|---|---|---|
| `POST /image/classify` | MobileNetV2 | Classify images (ImageNet 1000 classes) |
| `POST /image/detect` | SSD MobileNet V3 | Detect objects with bounding boxes (COCO 80 classes) |
| `POST /text/embeddings` | all-MiniLM-L6-v2 | Generate text embeddings (384 dimensions) |
| `POST /text/similarity` | all-MiniLM-L6-v2 | Compute semantic similarity between two texts |
| `POST /text/generate` | TinyLlama 1.1B (Q4) | Generate text with a local LLM |
| `GET /system/info` | - | GPU/CPU/RAM/temperature monitoring |

## Quick Start

```bash
# On your Jetson Nano:
git clone <your-repo-url> ~/jetson-ai
cd ~/jetson-ai

# Run the setup script (installs dependencies)
sudo bash scripts/setup_jetson.sh

# (Optional) Download the LLM model (~670MB)
bash scripts/download_models.sh

# Start the server
bash scripts/start_server.sh
```

Then from any device on your network, open: `http://<jetson-ip>:8000`

The built-in web dashboard lets you interact with all models directly from your browser -- classify images, detect objects, compute text similarity, generate text, and monitor system stats.

The Swagger API docs are available at `http://<jetson-ip>:8000/docs`.

## Documentation

- **[Jetson Nano Preparation](docs/JETSON_PREP.md)** - From unboxing to ready-to-run (start here if your Nano is new)
- **[Setup Guide](docs/SETUP.md)** - Install and run the AI server
- **[API Reference](docs/API.md)** - Full endpoint documentation with examples
- **[Models Guide](docs/MODELS.md)** - Model details, performance, and customization
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and fixes

## Project Structure

```text
.
├── configs/config.yaml        # Server and model configuration
├── docs/                      # Documentation
├── models/weights/            # Model weight files (git-ignored)
├── scripts/
│   ├── setup_jetson.sh        # Full setup script
│   ├── download_models.sh     # Download optional model weights
│   ├── start_server.sh        # Start the server
│   └── benchmark.py           # Performance benchmarking
└── src/
    ├── main.py                # Flask application
    ├── config.py              # Configuration loader
    ├── model_manager.py       # Model lifecycle management
    ├── static/index.html      # Web dashboard UI
    ├── routes/                # API endpoint definitions
    └── services/              # Model inference services
```

## Usage Examples

From any machine on your network (replace `192.168.1.x` with your Jetson's IP):

```bash
# Classify an image
curl -X POST http://192.168.1.x:8000/image/classify \
  -F "file=@photo.jpg"

# Detect objects
curl -X POST http://192.168.1.x:8000/image/detect \
  -F "file=@photo.jpg"

# Get text embeddings
curl -X POST http://192.168.1.x:8000/text/embeddings \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'

# Compare two texts
curl -X POST http://192.168.1.x:8000/text/similarity \
  -H "Content-Type: application/json" \
  -d '{"text1": "The cat sat on the mat", "text2": "A feline rested on the rug"}'

# Check system stats
curl http://192.168.1.x:8000/system/info
```

## Requirements

- NVIDIA Jetson Nano (4GB recommended)
- JetPack 4.6.x
- MicroSD card (32GB+ recommended)
- Network connection (Ethernet or WiFi)
