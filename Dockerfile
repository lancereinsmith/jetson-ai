# Base image from dusty-nv/jetson-containers (legacy branch)
# Includes Python 3.6, PyTorch, CUDA 10.2 for JetPack 4.6 (L4T R32.7.1)
# See: https://github.com/dusty-nv/jetson-containers/tree/legacy
FROM dustynv/l4t-pytorch:r32.7.1

# Fix locale for Click/Flask (container defaults to ASCII)
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Ensure CUDA libraries are findable during build (needed for torch import)
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install llama-cpp-python with CUDA support for text generation
RUN CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip3 install --no-cache-dir llama-cpp-python

# Pre-download all models at build time with wget (avoids torch/CUDA import
# issues during build — CUDA libs are only fully available at runtime via
# the nvidia container runtime).
ENV OPENBLAS_CORETYPE=ARMV8
ENV TOKENIZERS_PARALLELISM=false

# Torchvision model weights → torch hub cache
RUN mkdir -p /root/.cache/torch/hub/checkpoints && \
    wget -q --show-progress -O /root/.cache/torch/hub/checkpoints/mobilenet_v2-b0353104.pth \
    "https://download.pytorch.org/models/mobilenet_v2-b0353104.pth" && \
    wget -q --show-progress -O /root/.cache/torch/hub/checkpoints/ssdlite320_mobilenet_v3_large_coco-a79551df.pth \
    "https://download.pytorch.org/models/ssdlite320_mobilenet_v3_large_coco-a79551df.pth"

# Sentence-transformers model → clone from HuggingFace (avoids broken huggingface_hub download on Python 3.6)
RUN apt-get update && apt-get install -y --no-install-recommends git-lfs && \
    git lfs install && \
    git clone --depth 1 https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 \
    /root/.cache/torch/sentence_transformers/sentence-transformers_all-MiniLM-L6-v2 && \
    apt-get purge -y git-lfs && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# TinyLlama 1.1B (Q4_K_M quantized, ~670MB)
RUN mkdir -p models/weights && \
    wget -q --show-progress -O models/weights/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# ImageNet labels
RUN wget -q -O models/weights/imagenet_labels.txt \
    "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"

COPY src/ ./src/
COPY configs/ ./configs/

ENV FLASK_APP=src.main:app
EXPOSE 8000

CMD ["python3", "-m", "flask", "run", "--host", "0.0.0.0", "--port", "8000"]
