import logging
from typing import List

from PIL import Image

logger = logging.getLogger(__name__)

# COCO class labels
COCO_LABELS = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]


class ObjectDetector:
    def __init__(self, config: dict):
        self._config = config
        self._model = None
        self._threshold = config.get("confidence_threshold", 0.5)

    def load(self):
        import torch
        import torchvision  # type: ignore[import-not-found]

        logger.info("Loading object detector: SSD MobileNet V2")

        self._model = torchvision.models.detection.ssdlite320_mobilenet_v3_large(
            pretrained=True,
        )
        self._model.eval()

        if torch.cuda.is_available():
            self._model = self._model.cuda()
            logger.info("Object detector loaded on GPU")
        else:
            logger.info("Object detector loaded on CPU")

        self._transform = torchvision.transforms.Compose(
            [
                torchvision.transforms.ToTensor(),
            ]
        )

    def unload(self):
        self._model = None
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Object detector unloaded")

    def predict(self, image: Image.Image) -> List[dict]:
        import torch

        tensor = self._transform(image).unsqueeze(0)
        if torch.cuda.is_available():
            tensor = tensor.cuda()

        assert self._model is not None, "Model not loaded — call load() first"
        with torch.no_grad():
            outputs = self._model(tensor)

        detections = []
        output = outputs[0]
        boxes = output["boxes"].cpu().numpy()
        labels = output["labels"].cpu().numpy()
        scores = output["scores"].cpu().numpy()

        for box, label_id, score in zip(boxes, labels, scores):
            if score < self._threshold:
                continue
            label_id = int(label_id)
            label = COCO_LABELS[label_id - 1] if 0 < label_id <= len(COCO_LABELS) else str(label_id)
            detections.append(
                {
                    "label": label,
                    "confidence": round(float(score), 4),
                    "bbox": {
                        "x1": round(float(box[0]), 1),
                        "y1": round(float(box[1]), 1),
                        "x2": round(float(box[2]), 1),
                        "y2": round(float(box[3]), 1),
                    },
                }
            )

        return detections
