from flask import Blueprint, jsonify

from src.model_manager import model_manager

bp = Blueprint("health", __name__)


@bp.route("/health")
def health_check():
    return jsonify({"status": "ok"})


@bp.route("/models/status")
def models_status():
    return jsonify(model_manager.status())
