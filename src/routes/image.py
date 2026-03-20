import io
import logging

from flask import Blueprint, abort, jsonify, request
from PIL import Image

from src.model_manager import model_manager

logger = logging.getLogger(__name__)
bp = Blueprint("image", __name__, url_prefix="/image")


def _read_image():
    if "file" not in request.files:
        abort(400, "No file uploaded")
    file = request.files["file"]
    try:
        return Image.open(io.BytesIO(file.read())).convert("RGB")
    except Exception:
        abort(400, "Invalid image file")


@bp.route("/classify", methods=["POST"])
def classify_image():
    """Classify an uploaded image and return top-5 predictions."""
    image = _read_image()
    try:
        classifier = model_manager.get("image_classifier")
    except KeyError:
        abort(503, "Image classifier not available")
    results = classifier.predict(image)
    return jsonify({"predictions": results})


@bp.route("/detect", methods=["POST"])
def detect_objects():
    """Detect objects in an uploaded image."""
    image = _read_image()
    try:
        detector = model_manager.get("object_detector")
    except KeyError:
        abort(503, "Object detector not available")
    results = detector.predict(image)
    return jsonify({"detections": results})
