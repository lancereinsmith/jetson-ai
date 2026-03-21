import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


class TextEmbedder:
    def __init__(self, config: dict):
        self._config = config
        self._model = None

    def load(self):
        from sentence_transformers import SentenceTransformer

        model_name = self._config.get("model", "all-MiniLM-L6-v2")
        logger.info(f"Loading text embedder: {model_name}")
        # Use local cached path if available (avoids broken huggingface_hub download on Python 3.6)
        local_path = f"/root/.cache/torch/sentence_transformers/sentence-transformers_{model_name}"
        import os
        if os.path.isdir(local_path):
            logger.info(f"Loading from local cache: {local_path}")
            self._model = SentenceTransformer(local_path)
        else:
            self._model = SentenceTransformer(model_name)
        logger.info("Text embedder loaded")

    def unload(self):
        self._model = None
        logger.info("Text embedder unloaded")

    def encode(self, texts: List[str]) -> List[List[float]]:
        assert self._model is not None, "Model not loaded — call load() first"
        embeddings = self._model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return [emb.tolist() for emb in embeddings]

    def similarity(self, text1: str, text2: str) -> float:
        assert self._model is not None, "Model not loaded — call load() first"
        embeddings = self._model.encode(
            [text1, text2],
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        score = float(np.dot(embeddings[0], embeddings[1]))
        return round(score, 4)
