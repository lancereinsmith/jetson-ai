import logging

from flask import Blueprint, abort, jsonify, request

from src.model_manager import model_manager

logger = logging.getLogger(__name__)
bp = Blueprint("text", __name__, url_prefix="/text")


@bp.route("/embeddings", methods=["POST"])
def get_embeddings():
    """Generate text embeddings using sentence-transformers."""
    data = request.get_json(force=True)
    text = data.get("text")
    if text is None:
        abort(400, "Missing 'text' field")

    try:
        embedder = model_manager.get("text_embedder")
    except KeyError:
        abort(503, "Text embedder not available")

    texts = text if isinstance(text, list) else [text]
    embeddings = embedder.encode(texts)
    return jsonify({
        "embeddings": embeddings,
        "model": "all-MiniLM-L6-v2",
        "dimensions": len(embeddings[0]) if embeddings else 0,
    })


@bp.route("/similarity", methods=["POST"])
def compute_similarity():
    """Compute cosine similarity between two texts."""
    data = request.get_json(force=True)
    text1 = data.get("text1")
    text2 = data.get("text2")
    if not text1 or not text2:
        abort(400, "Missing 'text1' or 'text2' field")

    try:
        embedder = model_manager.get("text_embedder")
    except KeyError:
        abort(503, "Text embedder not available")

    score = embedder.similarity(text1, text2)
    return jsonify({"similarity": score, "text1": text1, "text2": text2})


@bp.route("/generate", methods=["POST"])
def generate_text():
    """Generate text using a local LLM."""
    data = request.get_json(force=True)
    prompt = data.get("prompt")
    if not prompt:
        abort(400, "Missing 'prompt' field")

    try:
        generator = model_manager.get("text_generator")
    except KeyError:
        abort(503, "Text generator not available. Enable it in config.yaml and install llama-cpp-python.")

    result = generator.generate(
        prompt=prompt,
        max_tokens=data.get("max_tokens"),
        temperature=data.get("temperature", 0.7),
    )
    return jsonify(result)
