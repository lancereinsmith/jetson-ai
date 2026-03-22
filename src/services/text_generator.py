import logging
import os

logger = logging.getLogger(__name__)


class TextGenerator:
    def __init__(self, config: dict):
        self._config = config
        self._model = None

    def load(self):
        try:
            from llama_cpp import Llama  # type: ignore[import-not-found]
        except ImportError:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Install it with CUDA support: "
                "CMAKE_ARGS='-DLLAMA_CUBLAS=on' pip install llama-cpp-python"
            )

        weights_dir = self._config.get(
            "weights_dir",
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "models",
                "weights",
            ),
        )
        model_file = self._config.get("model", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
        model_path = os.path.join(weights_dir, model_file)

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found: {model_path}. "
                f"Run scripts/download_models.sh to download it."
            )

        logger.info(f"Loading LLM: {model_file}")
        import inspect
        init_params = inspect.signature(Llama.__init__).parameters

        kwargs = {
            "model_path": model_path,
            "n_ctx": self._config.get("context_size", 2048),
        }
        if "verbose" in init_params:
            kwargs["verbose"] = False
        if "n_gpu_layers" in init_params:
            kwargs["n_gpu_layers"] = self._config.get("gpu_layers", -1)
        else:
            logger.warning("n_gpu_layers not supported by this llama-cpp-python version, running on CPU")
        self._model = Llama(**kwargs)
        logger.info("LLM loaded")

    def unload(self):
        self._model = None
        logger.info("LLM unloaded")

    def generate(
        self, prompt: str, max_tokens=None, temperature: float = 0.7
    ) -> dict:
        if max_tokens is None:
            max_tokens = self._config.get("max_tokens", 256)

        assert self._model is not None, "Model not loaded — call load() first"
        output = self._model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["</s>", "\n\n\n"],
        )

        return {
            "text": output["choices"][0]["text"],
            "usage": {
                "prompt_tokens": output["usage"]["prompt_tokens"],
                "completion_tokens": output["usage"]["completion_tokens"],
            },
        }
