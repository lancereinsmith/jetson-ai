import logging
import threading
import time

import psutil

from src.config import get_config

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model lifecycle: loading, unloading, and memory tracking."""

    def __init__(self):
        self._models = {}
        self._last_used = {}
        self._lock = threading.Lock()
        self._config = get_config()
        idle_seconds = self._config["memory"].get("idle_unload_seconds", 0)
        if idle_seconds > 0:
            self._start_idle_checker(idle_seconds)

    def register(self, name: str, service):
        """Register a model service (does not load it yet)."""
        with self._lock:
            self._models[name] = {
                "service": service,
                "loaded": False,
            }
            logger.info(f"Registered model service: {name}")

    def get(self, name: str):
        """Get a loaded model service. Loads it if not already loaded."""
        with self._lock:
            entry = self._models.get(name)
            if entry is None:
                raise KeyError(f"Model '{name}' is not registered")
            if not entry["loaded"]:
                self._check_memory()
                logger.info(f"Loading model: {name}")
                entry["service"].load()
                entry["loaded"] = True
            self._last_used[name] = time.time()
            return entry["service"]

    def unload(self, name: str):
        """Unload a model to free memory."""
        with self._lock:
            entry = self._models.get(name)
            if entry and entry["loaded"]:
                logger.info(f"Unloading model: {name}")
                entry["service"].unload()
                entry["loaded"] = False

    def status(self) -> dict:
        """Return status of all registered models."""
        with self._lock:
            return {
                name: {
                    "loaded": entry["loaded"],
                    "last_used": self._last_used.get(name),
                }
                for name, entry in self._models.items()
            }

    def _check_memory(self):
        max_percent = self._config["memory"].get("max_ram_percent", 70)
        mem = psutil.virtual_memory()
        if mem.percent > max_percent:
            self._evict_oldest()

    def _evict_oldest(self):
        if not self._last_used:
            return
        oldest = min(self._last_used, key=lambda k: self._last_used[k])
        logger.warning(f"Memory pressure: evicting model '{oldest}'")
        entry = self._models.get(oldest)
        if entry and entry["loaded"]:
            entry["service"].unload()
            entry["loaded"] = False
            del self._last_used[oldest]

    def _start_idle_checker(self, idle_seconds: int):
        def check_idle():
            while True:
                time.sleep(60)
                now = time.time()
                with self._lock:
                    for name, last in list(self._last_used.items()):
                        if now - last > idle_seconds:
                            entry = self._models.get(name)
                            if entry and entry["loaded"]:
                                logger.info(f"Idle timeout: unloading '{name}'")
                                entry["service"].unload()
                                entry["loaded"] = False
                                del self._last_used[name]

        t = threading.Thread(target=check_idle, daemon=True)
        t.start()


model_manager = ModelManager()
