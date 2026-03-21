# Troubleshooting

## Docker Issues

### Docker build fails

```bash
# Verify Docker and nvidia runtime are available
docker info | grep -i runtime

# If nvidia runtime is missing, install it:
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### "could not select device driver" / GPU not accessible in container

Make sure you're using the NVIDIA runtime. The `docker_run.sh` script handles this automatically. If running manually:

```bash
docker run --runtime nvidia ...
```

### Container starts but models fail to load

```bash
# Check container logs
docker logs -f jetson-ai

# Verify GPU is accessible inside the container
docker exec jetson-ai python3 -c "import torch; print(torch.cuda.is_available())"

# Check memory inside container
docker exec jetson-ai python3 -c "import torch; print(f'GPU mem: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f}GB')"
```

### Model weights not persisting across rebuilds

Model weights should be stored in the bind-mounted `./models/weights/` directory. If weights disappear:

```bash
# Check bind mount
docker exec jetson-ai ls -la /app/models/weights/
```

## Native Setup Issues

### "No module named torch" / PyTorch not found

PyTorch cannot be installed via `pip install torch` on the Jetson — it requires NVIDIA's pre-built ARM64 wheels.

```bash
# Check if PyTorch is installed
python3 -c "import torch; print(torch.__version__)"

# If not, download from NVIDIA:
# https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048
# Pick the wheel matching your JetPack version + Python version
```

### "import torchvision" fails

torchvision must be built from source on the Jetson. See [SETUP.md Step 4](SETUP.md#install-torchvision-from-source).

Common build errors:

```bash
# If you get "No matching distribution" or version errors:
# Make sure the torchvision version matches your PyTorch version
# PyTorch 1.10 → torchvision 0.11.x
# PyTorch 1.11 → torchvision 0.12.x
# PyTorch 1.12 → torchvision 0.13.x

# If build fails with memory errors:
# The Jetson may run out of RAM during compilation
# Create a swap file first:
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Then retry the build. Remove swap after:
sudo swapoff /swapfile
sudo rm /swapfile
```

### CUDA not available

```bash
# Check CUDA
nvcc --version
python3 -c "import torch; print(torch.cuda.is_available())"

# If CUDA shows as unavailable:
# 1. Make sure you're using NVIDIA's PyTorch wheel (not the default from PyPI)
# 2. Check that JetPack is properly installed:
dpkg -l | grep nvidia
# 3. Verify the GPU is recognized:
cat /proc/driver/nvidia/version
```

### Build errors during setup

If `pip install` fails for certain packages:

```bash
# Ensure build tools are installed
sudo apt-get install -y python3-dev build-essential cmake

# For packages that need Fortran (numpy, scipy):
sudo apt-get install -y gfortran

# If RAM runs out during compilation, add swap:
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Runtime Issues

### Server won't start

```bash
# Check if port 8000 is already in use
sudo lsof -i :8000

# Try a different port
JETSON_AI_PORT=8080 bash scripts/start_server.sh

# Check for Python errors
python3 -c "from src.main import app; print('OK')"
```

### "Connection refused" from other devices

1. Verify the server is running and listening on 0.0.0.0:

   ```bash
   curl http://localhost:8000/health
   ```

2. Check the Jetson's firewall:

   ```bash
   sudo ufw status
   # If active, allow port 8000:
   sudo ufw allow 8000
   ```

3. Verify network connectivity:

   ```bash
   # On the Jetson, find its IP:
   hostname -I

   # From your other device, ping it:
   ping 192.168.1.100
   ```

4. Make sure both devices are on the same network/subnet.

### First request is very slow

This is normal. Models load on first request (lazy loading). Subsequent requests will be much faster. You can "warm up" models by hitting each endpoint once after starting the server:

```bash
# Quick warmup script
curl -s http://localhost:8000/text/embeddings \
  -H "Content-Type: application/json" \
  -d '{"text": "warmup"}' > /dev/null
echo "Text embedder loaded"
```

### Out of memory errors

The Jetson Nano has 4GB shared between CPU and GPU. If you get OOM errors:

1. **Reduce loaded models.** Disable models you don't need in `config.yaml`.
2. **Lower idle timeout.** Set `idle_unload_seconds: 60` to free memory faster.
3. **Don't run the LLM with other models.** TinyLlama uses ~670MB. With other models loaded, RAM gets tight.
4. **Add swap space** (slower but prevents crashes):

   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   # Make permanent:
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

5. **Close other applications.** The desktop environment uses significant RAM. Consider running headless:

   ```bash
   sudo systemctl set-default multi-user.target
   # Reboot to apply. To get the desktop back:
   sudo systemctl set-default graphical.target
   ```

### GPU thermal throttling

If performance degrades over time, the GPU may be throttling due to heat:

```bash
# Check temperatures
curl http://localhost:8000/system/info | python3 -m json.tool

# Or directly:
cat /sys/devices/virtual/thermal/thermal_zone*/temp
```

If temperatures exceed 80C:

- Add a fan (5V fan connected to the J41 header)
- Improve ventilation around the Jetson
- Consider a heatsink

### llama-cpp-python build fails

```bash
# Make sure CUDA toolkit is available
nvcc --version

# Install with CUDA support
CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python --no-cache-dir

# If cmake can't find CUDA:
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --no-cache-dir
```

## Getting Help

- **Jetson forums:** <https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/jetson-nano/>
- **JetPack docs:** <https://docs.nvidia.com/jetson/>
- **Flask docs:** <https://flask.palletsprojects.com/>
- **llama.cpp:** <https://github.com/ggerganov/llama.cpp>
