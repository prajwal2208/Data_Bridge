import logging
from flask import Blueprint, jsonify
from app.schema_loader import get_all_schemas

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


@main_bp.route("/health", methods=["GET"])
def health():
    logger.info("Health check called")
    return jsonify({
        "status": "ok",
        "message": "DataBridge is running"
    }), 200


@main_bp.route("/schema", methods=["GET"])
def schema():
    logger.info("Schema endpoint called")
    try:
        all_schemas = get_all_schemas()
        return jsonify(all_schemas), 200
    except Exception as e:
        logger.error(f"Schema endpoint error: {e}")
        return jsonify({"error": str(e)}), 500