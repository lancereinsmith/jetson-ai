import logging
import os

from flask import Flask, jsonify, send_from_directory

from src.config import get_config
from src.model_manager import model_manager
from src.routes import health, image, system, text
from src.services.image_classifier import ImageClassifier
from src.services.object_detector import ObjectDetector
from src.services.text_embedder import TextEmbedder
from src.services.text_generator import TextGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    # CORS - allow all origins
    try:
        from flask_cors import CORS
        CORS(app)
    except ImportError:
        pass  # flask-cors is optional

    # Register blueprints
    app.register_blueprint(health.bp)
    app.register_blueprint(image.bp)
    app.register_blueprint(text.bp)
    app.register_blueprint(system.bp)

    # Register models
    config = get_config()
    models_config = config["models"]
    weights_dir = models_config.get("weights_dir", "models/weights")

    if models_config["image_classifier"].get("enabled"):
        model_manager.register(
            "image_classifier",
            ImageClassifier(models_config["image_classifier"]),
        )

    if models_config["object_detector"].get("enabled"):
        model_manager.register(
            "object_detector",
            ObjectDetector(models_config["object_detector"]),
        )

    if models_config["text_embedder"].get("enabled"):
        model_manager.register(
            "text_embedder",
            TextEmbedder(models_config["text_embedder"]),
        )

    if models_config["text_generator"].get("enabled"):
        gen_config = models_config["text_generator"].copy()
        gen_config["weights_dir"] = weights_dir
        model_manager.register(
            "text_generator",
            TextGenerator(gen_config),
        )

    logger.info("Jetson Nano AI Server started")
    logger.info("Registered models: %s", list(model_manager.status().keys()))

    static_dir = os.path.join(os.path.dirname(__file__), "static")

    @app.route("/")
    def root():
        return send_from_directory(static_dir, "index.html")

    @app.route("/api")
    def api_index():
        return jsonify({
            "name": "Jetson Nano AI Server",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "models": "/models/status",
                "system": "/system/info",
                "image_classify": "POST /image/classify",
                "image_detect": "POST /image/detect",
                "text_embeddings": "POST /text/embeddings",
                "text_similarity": "POST /text/similarity",
                "text_generate": "POST /text/generate",
            },
        })

    return app


app = create_app()
