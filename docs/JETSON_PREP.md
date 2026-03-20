# Jetson Nano Preparation Guide

How to take a Jetson Nano Developer Kit from unboxed to ready-to-run. Follow this guide before the [Setup Guide](SETUP.md).

## What You Need

### Required Hardware

| Item | Notes |
|---|---|
| Jetson Nano Developer Kit (B01) | 4GB version recommended. The 2GB version will work but limits which models you can run. |
| MicroSD card | 32GB minimum, **64GB recommended**. Use a fast card (UHS-I U3 / A2 or better). Slow cards bottleneck everything. |
| Power supply | **5V 4A DC barrel jack** (5.5mm/2.1mm center-positive). The micro-USB port only provides 5V/2A which causes throttling under load. |
| Ethernet cable | For initial setup and reliable network. WiFi adapter optional (see below). |
| Computer with SD card reader | To flash the OS image. Any Mac, Windows, or Linux machine works. |

### Required for Initial Setup Only

| Item | Notes |
|---|---|
| HDMI monitor + cable | Needed for the first-boot setup wizard. Not needed after SSH is configured. |
| USB keyboard | For the setup wizard. Mouse optional. |

### Optional but Recommended

| Item | Notes |
|---|---|
| 5V PWM fan | Prevents thermal throttling during sustained inference. Connects to the J41 header (pins 2 + 6). A Noctua NF-A4x20 5V is a popular choice. |
| Heatsink | The stock heatsink is fine for light use. For sustained GPU workloads, consider adding thermal paste or an aftermarket heatsink. |
| WiFi adapter | The Nano has no built-in WiFi. Use an Intel 8265 M.2 card (fits the M.2 slot) or a USB WiFi adapter (Edimax EW-7811Un works out of the box). |
| USB-to-serial cable | For headless setup without a monitor. Connects to J44 header. |
| Case | Protects the board. Many 3D-printable options exist. |

### Barrel Jack Jumper

**Important:** To use the barrel jack power supply (recommended), you must add a jumper on header **J48** on the Jetson Nano board. Without this jumper, the board will only draw power from the micro-USB port.

- J48 is located near the barrel jack connector
- Place a standard 2.54mm jumper across the two pins
- A simple wire jumper or dupont connector works

## Step 1: Download JetPack SD Card Image

JetPack is NVIDIA's SDK for Jetson. It includes Ubuntu 18.04, CUDA, cuDNN, TensorRT, and other libraries pre-installed.

1. Go to the [NVIDIA JetPack download page](https://developer.nvidia.com/embedded/jetpack-archive)
2. Download **JetPack 4.6.1** (or the latest 4.6.x) for Jetson Nano
   - Direct link: Look for "Jetson Nano Developer Kit SD Card Image"
   - The file is approximately **6GB** compressed
3. The download is a `.zip` file containing an `.img` file

**Why JetPack 4.6.x?** This is the final supported JetPack for the Jetson Nano. It includes CUDA 10.2, cuDNN 8.2, and TensorRT 8.2. Do not use JetPack 5.x as it is not compatible with the Nano.

## Step 2: Flash the SD Card

### Option A: Balena Etcher (Recommended - All Platforms)

1. Download [Balena Etcher](https://www.balena.io/etcher/)
2. Insert your MicroSD card into your computer
3. Open Etcher:
   - Click "Flash from file" and select the downloaded `.zip` file (no need to extract)
   - Click "Select target" and choose your MicroSD card
   - Click "Flash!"
4. Wait for flashing and verification to complete (~10-15 minutes)

### Option B: Command Line (macOS)

```bash
# Find your SD card device
diskutil list
# Look for the disk matching your SD card size (e.g., /dev/disk4)

# Unmount the disk (replace disk4 with your disk)
diskutil unmountDisk /dev/disk4

# Unzip and flash (replace disk4 with your disk)
# Use rdisk for faster raw writes
unzip -p jetson-nano-jp461-sd-card-image.zip | sudo dd of=/dev/rdisk4 bs=1m status=progress

# Eject
diskutil eject /dev/disk4
```

### Option C: Command Line (Linux)

```bash
# Find your SD card device
lsblk
# Look for your SD card (e.g., /dev/sdb)

# Unmount any auto-mounted partitions
sudo umount /dev/sdb*

# Flash
unzip -p jetson-nano-jp461-sd-card-image.zip | sudo dd of=/dev/sdb bs=1M status=progress

# Sync and eject
sync
sudo eject /dev/sdb
```

## Step 3: First Boot

1. Insert the flashed MicroSD card into the Jetson Nano (slot is under the heatsink)
2. Connect:
   - HDMI cable to a monitor
   - USB keyboard
   - Ethernet cable to your router
   - **Do NOT plug in power yet**
3. If using barrel jack: ensure the **J48 jumper** is in place
4. Plug in the power supply — the board will boot automatically (there is no power button)

### Ubuntu Setup Wizard

The first boot takes a few minutes. You'll see the NVIDIA logo, then the Ubuntu setup wizard:

1. **License agreement** — Accept
2. **Language** — English (or your preference)
3. **Keyboard layout** — Select yours
4. **Time zone** — Select yours
5. **User account** — Create your username and password
   - Remember these! You'll use them for SSH
   - Example: username `jetson`, pick a strong password
6. **APP partition size** — Use the maximum (default fills the SD card)
7. **Network** — Should auto-configure via DHCP if Ethernet is connected
8. **Nvpmodel** — Select **MAXN (10W)** for maximum performance

The system will reboot and bring you to the Ubuntu desktop.

## Step 4: Post-Boot Configuration

Open a terminal on the Jetson (or SSH in from another machine):

### Update the System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

This may take 10-20 minutes on the first run.

### Verify the GPU and CUDA

```bash
# Check JetPack / L4T version
head -n 1 /etc/nv_tegra_release
# Expected: # R32 (release), REVISION: 7.1 (or similar for JP 4.6.x)

# Check CUDA
nvcc --version
# Expected: Cuda compilation tools, release 10.2

# Quick GPU test
cd /usr/local/cuda/samples/1_Utilities/deviceQuery
sudo make
./deviceQuery
# Should show: "Result = PASS" and list the Maxwell GPU
```

### Set Maximum Performance Mode

```bash
# Set to 10W (max performance) mode
sudo nvpmodel -m 0

# Lock CPU/GPU/EMC clocks at maximum frequency
sudo jetson_clocks

# Verify
sudo nvpmodel -q
# Expected: NV Power Mode: MAXN
```

To make `jetson_clocks` persist across reboots:

```bash
# Create a service to run jetson_clocks at boot
sudo tee /etc/systemd/system/jetson-clocks.service << 'EOF'
[Unit]
Description=Set Jetson clocks to max
After=nvpmodel.service

[Service]
Type=oneshot
ExecStart=/usr/bin/jetson_clocks
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable jetson-clocks
```

### Configure SSH

SSH should be enabled by default. Verify:

```bash
sudo systemctl status ssh
# Should show "active (running)"

# If not enabled:
sudo systemctl enable ssh
sudo systemctl start ssh
```

Find the Jetson's IP address:

```bash
hostname -I
# Example output: 192.168.1.105
```

Test from your Mac/PC:

```bash
ssh jetson@192.168.1.105
# (use whatever username you created during setup)
```

### Set a Static IP Address

A static IP means you can always reach your Jetson at the same address.

**Option A: Via NetworkManager (on the Jetson)**

```bash
# List network connections
nmcli con show

# Set static IP for Ethernet (adjust addresses to match YOUR network)
# Common home networks use 192.168.1.x or 192.168.0.x
sudo nmcli con mod "Wired connection 1" \
  ipv4.addresses "192.168.1.100/24" \
  ipv4.gateway "192.168.1.1" \
  ipv4.dns "8.8.8.8,8.8.4.4" \
  ipv4.method "manual"

# Apply the changes
sudo nmcli con up "Wired connection 1"

# Verify
ip addr show eth0
```

**Option B: Via Your Router (recommended)**

Most home routers support DHCP reservation:

1. Log into your router's admin page (usually 192.168.1.1)
2. Find the DHCP or LAN settings
3. Find the Jetson Nano in the connected devices list
4. Create a DHCP reservation assigning it a fixed IP
5. This is preferred because the router manages it and it survives network changes

### Add Swap Space (Recommended)

The Jetson Nano only has 4GB RAM. Adding swap prevents crashes during model loading and compilation:

```bash
# Create a 4GB swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make it permanent (survives reboot)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h
# Should show ~4G of swap
```

### (Optional) Disable the Desktop GUI

The Ubuntu desktop uses ~800MB of RAM. If you'll only access the Jetson via SSH and the web UI, disabling the desktop frees significant memory:

```bash
# Switch to text-only mode (takes effect after reboot)
sudo systemctl set-default multi-user.target
sudo reboot

# To re-enable the desktop later:
sudo systemctl set-default graphical.target
sudo reboot
```

### (Optional) Set Up WiFi

If using an Intel 8265 M.2 WiFi card:

```bash
# It should be detected automatically. Check:
nmcli device status

# Connect to your WiFi network:
sudo nmcli device wifi connect "YourNetworkName" password "YourPassword"

# Verify
nmcli con show --active
```

If using a USB WiFi adapter:

```bash
# Check if detected
lsusb
nmcli device status

# Connect (same command)
sudo nmcli device wifi connect "YourNetworkName" password "YourPassword"
```

## Step 5: Verify Everything

Run these checks to confirm your Jetson is ready:

```bash
echo "=== System ==="
uname -a
head -n 1 /etc/nv_tegra_release

echo "=== CUDA ==="
nvcc --version

echo "=== Performance Mode ==="
sudo nvpmodel -q

echo "=== Memory ==="
free -h

echo "=== Disk ==="
df -h /

echo "=== Network ==="
hostname -I

echo "=== GPU ==="
cat /sys/devices/gpu.0/load 2>/dev/null && echo "/10 (GPU load)" || echo "GPU load not available"

echo "=== Temperature ==="
cat /sys/devices/virtual/thermal/thermal_zone*/type /sys/devices/virtual/thermal/thermal_zone*/temp 2>/dev/null
```

Expected results:

- L4T R32.7.x
- CUDA 10.2
- MAXN power mode
- ~4GB RAM + ~4GB swap
- GPU present and responding
- Temperatures under 50C at idle

## You're Ready

Your Jetson Nano is now prepared. Continue to the [Setup Guide](SETUP.md) to install and run the AI server.

Quick summary of what to do next:

```bash
cd ~
git clone <your-repo-url> jetson-ai
cd jetson-ai
sudo bash scripts/setup_jetson.sh
# Follow instructions for PyTorch installation
bash scripts/start_server.sh
# Open http://<jetson-ip>:8000 in your browser
```
