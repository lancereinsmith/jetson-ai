# API Reference

Base URL: `http://<jetson-ip>:8000`

API index: `http://<jetson-ip>:8000/api`

## Health & Status

### `GET /health`

Health check endpoint.

**Response:**

```json
{"status": "ok"}
```

### `GET /models/status`

Shows which models are registered and loaded.

**Response:**

```json
{
  "image_classifier": {"loaded": true, "last_used": 1700000000.0},
  "object_detector": {"loaded": false, "last_used": null},
  "text_embedder": {"loaded": true, "last_used": 1700000000.0}
}
```

---

## Image Endpoints

### `POST /image/classify`

Classify an uploaded image. Returns top-5 predictions from ImageNet (1000 classes).

**Request:** `multipart/form-data` with a `file` field containing a JPEG/PNG image.

```bash
curl -X POST http://192.168.1.100:8000/image/classify \
  -F "file=@dog.jpg"
```

**Response:**

```json
{
  "predictions": [
    {"label": "golden retriever", "confidence": 0.9234, "class_id": 207},
    {"label": "Labrador retriever", "confidence": 0.0412, "class_id": 208},
    {"label": "cocker spaniel", "confidence": 0.0089, "class_id": 219},
    {"label": "tennis ball", "confidence": 0.0034, "class_id": 852},
    {"label": "kuvasz", "confidence": 0.0021, "class_id": 222}
  ]
}
```

### `POST /image/detect`

Detect objects in an uploaded image. Returns bounding boxes, labels, and confidence scores.

**Request:** `multipart/form-data` with a `file` field.

```bash
curl -X POST http://192.168.1.100:8000/image/detect \
  -F "file=@street.jpg"
```

**Response:**

```json
{
  "detections": [
    {
      "label": "person",
      "confidence": 0.9521,
      "bbox": {"x1": 120.5, "y1": 80.2, "x2": 340.1, "y2": 450.8}
    },
    {
      "label": "car",
      "confidence": 0.8734,
      "bbox": {"x1": 400.0, "y1": 200.5, "x2": 620.3, "y2": 380.1}
    }
  ]
}
```

Bounding box coordinates are in pixels relative to the original image dimensions.

---

## Text Endpoints

### `POST /text/embeddings`

Generate embeddings for one or more text strings.

**Request:**

```bash
# Single text
curl -X POST http://192.168.1.100:8000/text/embeddings \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'

# Multiple texts
curl -X POST http://192.168.1.100:8000/text/embeddings \
  -H "Content-Type: application/json" \
  -d '{"text": ["Hello world", "How are you?"]}'
```

**Response:**

```json
{
  "embeddings": [
    [0.0234, -0.0891, 0.0456, ...]
  ],
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384
}
```

Each embedding is a 384-dimensional vector, normalized to unit length. Use these for semantic search, clustering, or as features for downstream tasks.

### `POST /text/similarity`

Compute cosine similarity between two texts. Returns a score from -1.0 to 1.0 (higher = more similar).

**Request:**

```bash
curl -X POST http://192.168.1.100:8000/text/similarity \
  -H "Content-Type: application/json" \
  -d '{
    "text1": "The cat sat on the mat",
    "text2": "A feline rested on the rug"
  }'
```

**Response:**

```json
{
  "similarity": 0.7823,
  "text1": "The cat sat on the mat",
  "text2": "A feline rested on the rug"
}
```

### `POST /text/generate`

Generate text using a local LLM. Only available if `text_generator` is enabled in config and the model is downloaded.

**Request:**

```bash
curl -X POST http://192.168.1.100:8000/text/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms:",
    "max_tokens": 128,
    "temperature": 0.7
  }'
```

**Parameters:**

| Field | Type | Default | Description |
|---|---|---|---|
| `prompt` | string | (required) | Input text prompt |
| `max_tokens` | integer | 256 | Maximum tokens to generate |
| `temperature` | float | 0.7 | Sampling temperature (0.0 = deterministic, 1.0 = creative) |

**Response:**

```json
{
  "text": " Quantum computing uses quantum bits (qubits) that can be both 0 and 1 at the same time...",
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 45
  }
}
```

Note: Text generation on the Jetson Nano is slow (~1-3 tokens/sec with TinyLlama). Best for short responses.

---

## System Endpoints

### `GET /system/info`

Returns system monitoring information including CPU, RAM, GPU, disk, and temperature.

```bash
curl http://192.168.1.100:8000/system/info
```

**Response:**

```json
{
  "cpu": {
    "cores": 4,
    "percent": 23.5,
    "frequency_mhz": 1479.0
  },
  "memory": {
    "total_mb": 3964.0,
    "available_mb": 2100.5,
    "used_percent": 47.0
  },
  "disk": {
    "total_gb": 59.0,
    "free_gb": 42.3,
    "used_percent": 28.3
  },
  "gpu": {
    "available": true,
    "load_percent": 15.2
  },
  "temperature": {
    "CPU-therm": 42.0,
    "GPU-therm": 41.5,
    "AO-therm": 38.0
  }
}
```

---

## Error Responses

All endpoints return standard HTTP error codes:

| Code | Meaning |
|---|---|
| 400 | Bad request (e.g., invalid image file) |
| 503 | Model not available (not enabled or failed to load) |
| 500 | Internal server error |

Error response format:

```json
{"detail": "Error description here"}
```

---

## Python Client Example

```python
import requests

JETSON_URL = "http://192.168.1.100:8000"

# Classify an image
with open("photo.jpg", "rb") as f:
    response = requests.post(f"{JETSON_URL}/image/classify", files={"file": f})
    print(response.json()["predictions"][0])

# Get embeddings
response = requests.post(f"{JETSON_URL}/text/embeddings", json={"text": "Hello world"})
embedding = response.json()["embeddings"][0]
print(f"Embedding dimensions: {len(embedding)}")

# Check system health
response = requests.get(f"{JETSON_URL}/system/info")
info = response.json()
print(f"GPU load: {info['gpu']['load_percent']}%")
print(f"RAM free: {info['memory']['available_mb']}MB")
```
