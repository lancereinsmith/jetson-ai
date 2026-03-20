import logging
import os
from typing import List

from PIL import Image

logger = logging.getLogger(__name__)

# ImageNet class labels (loaded on first use)
_labels = None


def _load_labels():
    global _labels
    labels_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "models",
        "weights",
        "imagenet_labels.txt",
    )
    if os.path.exists(labels_path):
        with open(labels_path) as f:
            _labels = [line.strip() for line in f.readlines()]
    else:
        logger.warning(f"Labels file not found at {labels_path}")
        _labels = [str(i) for i in range(1000)]


class ImageClassifier:
    def __init__(self, config: dict):
        self._config = config
        self._model = None
        self._input_size = config.get("input_size", 224)

    def load(self):
        import torch
        import torchvision.models as models  # type: ignore[import-not-found]
        import torchvision.transforms as transforms  # type: ignore[import-not-found]

        model_name = self._config.get("model", "mobilenet_v2")
        logger.info(f"Loading image classifier: {model_name}")

        if model_name == "mobilenet_v2":
            self._model = models.mobilenet_v2(pretrained=True)
        elif model_name == "resnet18":
            self._model = models.resnet18(pretrained=True)
        else:
            raise ValueError(f"Unknown model: {model_name}")

        self._model.eval()

        if self._config.get("precision") == "fp16":
            self._model = self._model.half()

        if torch.cuda.is_available():
            self._model = self._model.cuda()
            logger.info("Image classifier loaded on GPU")
        else:
            logger.info("Image classifier loaded on CPU")

        self._transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(self._input_size),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

        if _labels is None:
            _load_labels()

    def unload(self):
        self._model = None
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Image classifier unloaded")

    def predict(self, image: Image.Image, top_k: int = 5) -> List[dict]:
        import torch

        tensor = self._transform(image).unsqueeze(0)
        if self._config.get("precision") == "fp16":
            tensor = tensor.half()
        if torch.cuda.is_available():
            tensor = tensor.cuda()

        assert self._model is not None, "Model not loaded — call load() first"
        with torch.no_grad():
            output = self._model(tensor)

        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top_probs, top_indices = torch.topk(probabilities, top_k)

        results = []
        for i in range(top_k):
            idx = top_indices[i].item()
            results.append(
                {
                    "label": _labels[idx] if _labels and idx < len(_labels) else str(idx),
                    "confidence": round(top_probs[i].item(), 4),
                    "class_id": idx,
                }
            )
        return results
