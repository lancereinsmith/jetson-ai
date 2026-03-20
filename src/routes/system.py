import os
import subprocess

import psutil
from flask import Blueprint, jsonify

bp = Blueprint("system", __name__, url_prefix="/system")


def _get_gpu_info():
    """Read Jetson GPU stats from sysfs."""
    gpu = {"available": False}
    load_path = "/sys/devices/gpu.0/load"
    if os.path.exists(load_path):
        try:
            with open(load_path) as f:
                raw = int(f.read().strip())
                gpu["load_percent"] = round(raw / 10.0, 1)
                gpu["available"] = True
        except (OSError, ValueError):
            pass

    # Try tegrastats for memory info
    try:
        result = subprocess.run(
            ["cat", "/sys/kernel/debug/tegra_gpu/gpu_usage"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=2,
        )
        if result.returncode == 0:
            gpu["usage_raw"] = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return gpu


@bp.route("/info")
def system_info():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_freq = psutil.cpu_freq()

    return jsonify({
        "cpu": {
            "cores": psutil.cpu_count(logical=True),
            "percent": psutil.cpu_percent(interval=0.5),
            "frequency_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
        },
        "memory": {
            "total_mb": round(mem.total / 1024 / 1024, 1),
            "available_mb": round(mem.available / 1024 / 1024, 1),
            "used_percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 1),
            "used_percent": disk.percent,
        },
        "gpu": _get_gpu_info(),
        "temperature": _get_temperatures(),
    })


def _get_temperatures():
    temps = {}
    try:
        sensor_temps = psutil.sensors_temperatures()
        for name, entries in sensor_temps.items():
            for entry in entries:
                label = entry.label or name
                temps[label] = round(entry.current, 1)
    except (AttributeError, RuntimeError):
        pass

    # Jetson-specific thermal zones
    thermal_base = "/sys/devices/virtual/thermal"
    if os.path.isdir(thermal_base):
        for zone in sorted(os.listdir(thermal_base)):
            if zone.startswith("thermal_zone"):
                temp_path = os.path.join(thermal_base, zone, "temp")
                type_path = os.path.join(thermal_base, zone, "type")
                try:
                    with open(type_path) as f:
                        name = f.read().strip()
                    with open(temp_path) as f:
                        val = int(f.read().strip()) / 1000.0
                    temps[name] = round(val, 1)
                except (OSError, ValueError):
                    pass
    return temps
