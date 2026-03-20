import os

import yaml

CONFIG_PATH = os.environ.get(
    "JETSON_AI_CONFIG",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "config.yaml"),
)


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


_config = None


def get_config() -> dict:
    global _config
    if _config is None:
        _config = load_config()
    return _config
