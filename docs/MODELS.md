# Models Guide

## Overview

| Model | Task | Size in RAM | First Load | Inference Speed |
|---|---|---|---|---|
| MobileNetV2 | Image Classification | ~14MB (FP16) | ~3s | ~15-30ms/image |
| SSD MobileNet V3 | Object Detection | ~18MB | ~4s | ~30-60ms/image |
| all-MiniLM-L6-v2 | Text Embeddings | ~90MB | ~5s | ~20-50ms/text |
| TinyLlama 1.1B Q4 | Text Generation | ~670MB | ~15s | ~1-3 tokens/sec |

Performance numbers are approximate, measured on Jetson Nano 4GB with JetPack 4.6, max performance mode (`nvpmodel -m 0`, `jetson_clocks`).

## Image Classification (MobileNetV2)

**What it does:** Classifies images into one of 1,000 ImageNet categories (animals, objects, vehicles, food, etc.).

**Model details:**

- Architecture: MobileNetV2 (optimized for mobile/edge)
- Input: 224x224 RGB image (resized automatically)
- Output: Top-5 class predictions with confidence scores
- Precision: FP16 (half precision) for faster inference on Jetson GPU

**Good for:** Identifying what's in a photo, sorting images by category, content tagging.

**Configuration** (`configs/config.yaml`):

```yaml
image_classifier:
  enabled: true
  model: "mobilenet_v2"    # or "resnet18" (more accurate, slower)
  precision: "fp16"        # or "fp32"
  input_size: 224
```

**Alternative:** Switch to `resnet18` for better accuracy at the cost of ~2x slower inference and ~45MB RAM.

## Object Detection (SSD MobileNet V3)

**What it does:** Detects and locates objects in images with bounding boxes. Recognizes 80 object categories from the COCO dataset.

**COCO categories include:** person, bicycle, car, motorcycle, bus, truck, cat, dog, bird, chair, laptop, phone, bottle, cup, and more.

**Model details:**

- Architecture: SSDLite320 with MobileNetV3-Large backbone
- Input: 320x320 RGB image (resized automatically)
- Output: List of detections with labels, confidence scores, and bounding boxes
- Configurable confidence threshold (default: 0.5)

**Good for:** Counting objects, finding specific items in photos, spatial analysis.

**Configuration:**

```yaml
object_detector:
  enabled: true
  model: "ssd_mobilenet_v2"
  precision: "fp16"
  confidence_threshold: 0.5    # Lower = more detections (more false positives)
  input_size: 300
```

## Text Embeddings (all-MiniLM-L6-v2)

**What it does:** Converts text into a 384-dimensional vector that captures semantic meaning. Similar texts produce similar vectors.

**Model details:**

- Architecture: MiniLM (distilled from larger transformer)
- Parameters: 22M
- Output: 384-dimensional normalized embedding vector
- Max input length: 256 tokens (~200 words)

**Good for:**

- **Semantic search:** Find documents similar to a query
- **Clustering:** Group similar texts together
- **Duplicate detection:** Find near-duplicate content
- **Classification features:** Use embeddings as input to a classifier

**Configuration:**

```yaml
text_embedder:
  enabled: true
  model: "all-MiniLM-L6-v2"
  max_length: 256
```

## Text Generation (TinyLlama 1.1B)

**What it does:** Generates text responses given a prompt. This is a small language model — capable of basic Q&A, simple summarization, and creative text, but not comparable to larger models.

**Model details:**

- Architecture: Llama 2 (1.1B parameters)
- Quantization: Q4_K_M (4-bit, ~670MB file)
- Context window: 2048 tokens
- Inference: via llama.cpp with CUDA GPU offloading
- Speed: ~1-3 tokens/second on Jetson Nano

**Limitations:**

- Slow generation speed
- Limited reasoning ability
- May produce inaccurate information
- Best for short responses (< 100 tokens)

**Configuration:**

```yaml
text_generator:
  enabled: false    # Enable when ready
  model: "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
  max_tokens: 256
  context_size: 2048
  gpu_layers: -1    # -1 = offload all layers to GPU
```

**Setup:**

```bash
# Download the model
bash scripts/download_models.sh --llm

# Install llama-cpp-python with CUDA
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python

# Enable in config
# Edit configs/config.yaml → text_generator.enabled: true
```

## Memory Management

The Jetson Nano has 4GB of shared RAM (CPU + GPU). The server manages memory automatically:

- **Lazy loading:** Models load on first request, not at startup
- **Idle unloading:** Models unload after 5 minutes of inactivity (configurable)
- **Memory pressure eviction:** If RAM usage exceeds 70%, the least-recently-used model is unloaded

This means:

- You can enable all models even if they don't all fit in RAM simultaneously
- The first request to each model will be slower (loading time)
- Frequently used models stay loaded; rarely used ones get evicted

**Configuration:**

```yaml
memory:
  max_ram_percent: 70         # Trigger eviction above this
  idle_unload_seconds: 300    # Unload after 5 min idle (0 = never)
```

**Tip:** If you primarily use one or two models, set `idle_unload_seconds: 0` to keep them permanently loaded.

## Performance Tips

1. **Use max performance mode:**

   ```bash
   sudo nvpmodel -m 0
   sudo jetson_clocks
   ```

2. **Use FP16 precision** for image models (enabled by default). This halves memory usage and roughly doubles throughput on the Maxwell GPU.

3. **Disable unused models** in `config.yaml` to save the overhead of registration.

4. **Keep the Jetson cool.** The GPU will throttle at high temperatures. A small fan makes a significant difference for sustained workloads.

5. **Run benchmarks** to measure actual performance on your setup:

   ```bash
   python3 scripts/benchmark.py
   ```
